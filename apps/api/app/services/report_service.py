"""Report generation service.

Aggregates business events + aggregated metrics for a period into a
business-user-focused report (KPIs, trends, tables) with a deterministic
executive summary + recommendations. Persists a Report snapshot.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.camera import Camera
from app.models.camera_event import CameraEvent
from app.models.camera_metric import CameraMetric
from app.models.organization import Organization
from app.models.report import Report
from app.repositories.report_repository import ReportRepository
from app.schemas.report import (
    AlertRow,
    AlertSummary,
    CameraActivityItem,
    QueueStats,
    ReportData,
    TrendPoint,
)
from app.services.narrative import executive_summary, recommendations

_PERIOD_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


def _window(report_type: str, end_date: date) -> tuple[date, datetime, datetime]:
    days = _PERIOD_DAYS[report_type]
    start_date = end_date - timedelta(days=days - 1)
    start_dt = datetime.combine(start_date, time.min, tzinfo=UTC)
    end_dt = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=UTC)
    return start_date, start_dt, end_dt


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ReportRepository(session)

    async def generate(
        self, org_id: uuid.UUID, *, report_type: str = "daily", end_date: date | None = None
    ) -> Report:
        if report_type not in _PERIOD_DAYS:
            raise ValidationError(f"Unsupported report type: {report_type}")
        end_date = end_date or datetime.now(UTC).date()
        org = await self._session.get(Organization, org_id)
        company = org.name if org else "VisionOps"
        logo_url = org.logo_url if org else None
        start_date, start_dt, end_dt = _window(report_type, end_date)
        days = _PERIOD_DAYS[report_type]
        prev_start = start_dt - timedelta(days=days)

        cameras = await self._session.execute(
            select(Camera).where(Camera.organization_id == org_id, Camera.enabled.is_(True))
        )
        cameras = list(cameras.scalars().all())
        cam_by_id = {c.id: c for c in cameras}

        data = ReportData(
            company_name=company,
            logo_url=logo_url,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            generated_at=datetime.now(UTC),
        )

        # --- metrics KPIs ---
        m = (
            await self._session.execute(
                select(
                    func.coalesce(func.sum(CameraMetric.footfall), 0),
                    func.coalesce(func.avg(CameraMetric.occupancy_avg), 0),
                    func.coalesce(func.max(CameraMetric.occupancy_peak), 0),
                    func.coalesce(func.avg(CameraMetric.queue_avg), 0),
                    func.coalesce(func.max(CameraMetric.queue_peak), 0),
                ).where(
                    CameraMetric.organization_id == org_id,
                    CameraMetric.bucket >= start_dt,
                    CameraMetric.bucket < end_dt,
                )
            )
        ).one()
        data.total_footfall = int(m[0])
        data.avg_occupancy = round(float(m[1]), 2)
        data.peak_occupancy = int(m[2])
        data.queue_stats = QueueStats(
            avg_queue_length=round(float(m[3]), 2), peak_queue_length=int(m[4])
        )

        previous_footfall = int(
            await self._session.scalar(
                select(func.coalesce(func.sum(CameraMetric.footfall), 0)).where(
                    CameraMetric.organization_id == org_id,
                    CameraMetric.bucket >= prev_start,
                    CameraMetric.bucket < start_dt,
                )
            )
            or 0
        )

        # --- alerts ---
        await self._load_alerts(org_id, start_dt, end_dt, data, cam_by_id)

        # --- cameras ---
        data.total_cameras = len(cameras)
        data.cameras_online = sum(1 for c in cameras if c.status == "online")
        data.overall_uptime_pct = (
            round(data.cameras_online / data.total_cameras * 100, 1) if data.total_cameras else 0.0
        )
        await self._load_camera_activity(org_id, start_dt, end_dt, data, cameras)

        # --- trends ---
        trunc = "hour" if report_type == "daily" else "day"
        await self._load_trends(org_id, start_dt, end_dt, trunc, data)

        # --- narrative ---
        data.executive_summary = executive_summary(data, previous_footfall)
        data.recommendations = recommendations(data)

        report = Report(
            organization_id=org_id,
            report_type=report_type,
            period_start=start_date,
            period_end=end_date,
            status="ready",
            data=data.model_dump(mode="json"),
        )
        return await self._repo.add(report)

    async def _load_alerts(self, org_id, start_dt, end_dt, data: ReportData, cam_by_id) -> None:
        rows = (
            await self._session.execute(
                select(CameraEvent)
                .where(
                    CameraEvent.organization_id == org_id,
                    CameraEvent.started_at >= start_dt,
                    CameraEvent.started_at < end_dt,
                )
                .order_by(CameraEvent.started_at.desc())
                .limit(100)
            )
        ).scalars().all()

        summary = AlertSummary(total_alerts=len(rows))
        for ev in rows:
            if ev.severity in ("critical", "high", "medium", "low"):
                setattr(summary, ev.severity, getattr(summary, ev.severity) + 1)
            summary.by_type[ev.event_type] = summary.by_type.get(ev.event_type, 0) + 1

        data.alert_summary = summary
        data.total_alerts = summary.total_alerts
        data.critical_alerts = summary.critical + summary.high
        data.alert_rows = [
            AlertRow(
                time=ev.started_at,
                camera_name=cam_by_id[ev.camera_id].name if ev.camera_id in cam_by_id else "—",
                event_type=ev.event_type,
                severity=ev.severity,
                status=ev.status,
            )
            for ev in rows[:25]
        ]

    async def _load_camera_activity(self, org_id, start_dt, end_dt, data: ReportData, cameras) -> None:
        items: list[CameraActivityItem] = []
        for cam in cameras:
            agg = (
                await self._session.execute(
                    select(
                        func.coalesce(func.sum(CameraMetric.footfall), 0),
                        func.coalesce(func.avg(CameraMetric.occupancy_avg), 0),
                        func.coalesce(func.max(CameraMetric.occupancy_peak), 0),
                    ).where(
                        CameraMetric.camera_id == cam.id,
                        CameraMetric.bucket >= start_dt,
                        CameraMetric.bucket < end_dt,
                    )
                )
            ).one()
            events = await self._session.scalar(
                select(func.count()).select_from(CameraEvent).where(
                    CameraEvent.camera_id == cam.id,
                    CameraEvent.started_at >= start_dt,
                    CameraEvent.started_at < end_dt,
                )
            )
            items.append(
                CameraActivityItem(
                    camera_id=cam.id,
                    camera_name=cam.name,
                    total_footfall=int(agg[0]),
                    total_events=int(events or 0),
                    avg_occupancy=round(float(agg[1]), 2),
                    peak_occupancy=int(agg[2]),
                    uptime_pct=100.0 if cam.status == "online" else 0.0,
                    status=cam.status,
                )
            )
        items.sort(key=lambda c: c.total_footfall, reverse=True)
        data.cameras = items

    async def _load_trends(self, org_id, start_dt, end_dt, trunc: str, data: ReportData) -> None:
        b = func.date_trunc(trunc, CameraMetric.bucket).label("b")
        rows = (
            await self._session.execute(
                select(
                    b,
                    func.sum(CameraMetric.footfall),
                    func.max(CameraMetric.occupancy_peak),
                    func.max(CameraMetric.queue_peak),
                )
                .where(
                    CameraMetric.organization_id == org_id,
                    CameraMetric.bucket >= start_dt,
                    CameraMetric.bucket < end_dt,
                )
                .group_by(b)
                .order_by(b)
            )
        ).all()
        fmt = "%H:00" if trunc == "hour" else "%m-%d"
        for r in rows:
            label = r[0].strftime(fmt)
            data.footfall_trend.append(TrendPoint(label=label, value=float(r[1] or 0)))
            data.occupancy_trend.append(TrendPoint(label=label, value=float(r[2] or 0)))
            data.queue_trend.append(TrendPoint(label=label, value=float(r[3] or 0)))

    # --- read ---

    async def list(self, org_id: uuid.UUID, *, report_type: str | None = None) -> list[Report]:
        return await self._repo.list_for_org(org_id, report_type=report_type)

    async def get(self, report_id: uuid.UUID, org_id: uuid.UUID) -> Report:
        report = await self._repo.get_for_org(report_id, org_id)
        if report is None:
            raise NotFoundError("Report not found")
        return report
