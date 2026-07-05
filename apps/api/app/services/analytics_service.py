"""Analytics service.

Reads *aggregated* data (camera_metrics) and business events (camera_events) —
never raw AI telemetry — to power the dashboard.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camera import Camera
from app.models.camera_event import CameraEvent
from app.models.camera_metric import CameraMetric
from app.schemas.analytics import (
    AlertBreakdownResponse,
    CameraHealthResponse,
    MetricPoint,
    OverviewResponse,
    TimeseriesResponse,
)

_RANGES = {
    "today": timedelta(days=1),
    "yesterday": timedelta(days=2),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}
_TRUNC = {"hour": "hour", "day": "day", "week": "week"}


def _start_of_day() -> datetime:
    now = datetime.now(UTC)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def range_start(range_key: str) -> datetime:
    return datetime.now(UTC) - _RANGES.get(range_key, _RANGES["7d"])


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def overview(self, org_id: uuid.UUID) -> OverviewResponse:
        day_start = _start_of_day()
        recent = datetime.now(UTC) - timedelta(minutes=5)

        active = await self._session.scalar(
            select(func.count()).select_from(Camera).where(
                Camera.organization_id == org_id, Camera.enabled.is_(True)
            )
        )
        online = await self._session.scalar(
            select(func.count()).select_from(Camera).where(
                Camera.organization_id == org_id, Camera.status == "online"
            )
        )
        alerts_today = await self._session.scalar(
            select(func.count()).select_from(CameraEvent).where(
                CameraEvent.organization_id == org_id, CameraEvent.created_at >= day_start
            )
        )
        critical_today = await self._session.scalar(
            select(func.count()).select_from(CameraEvent).where(
                CameraEvent.organization_id == org_id,
                CameraEvent.created_at >= day_start,
                CameraEvent.severity.in_(("high", "critical")),
            )
        )
        footfall_today = await self._session.scalar(
            select(func.coalesce(func.sum(CameraMetric.footfall), 0)).where(
                CameraMetric.organization_id == org_id, CameraMetric.bucket >= day_start
            )
        )
        # Current occupancy: latest bucket per camera within the last 5 minutes.
        latest = (
            select(
                CameraMetric.camera_id,
                func.max(CameraMetric.bucket).label("b"),
            )
            .where(CameraMetric.organization_id == org_id, CameraMetric.bucket >= recent)
            .group_by(CameraMetric.camera_id)
            .subquery()
        )
        current_occupancy = await self._session.scalar(
            select(func.coalesce(func.sum(CameraMetric.occupancy_peak), 0)).join(
                latest,
                (CameraMetric.camera_id == latest.c.camera_id)
                & (CameraMetric.bucket == latest.c.b),
            )
        )

        return OverviewResponse(
            active_cameras=active or 0,
            cameras_online=online or 0,
            alerts_today=alerts_today or 0,
            critical_alerts_today=critical_today or 0,
            current_occupancy=int(current_occupancy or 0),
            todays_footfall=int(footfall_today or 0),
        )

    async def timeseries(
        self, org_id: uuid.UUID, *, range_key: str = "7d", bucket: str = "hour"
    ) -> TimeseriesResponse:
        trunc = _TRUNC.get(bucket, "hour")
        b = func.date_trunc(trunc, CameraMetric.bucket).label("b")
        stmt = (
            select(
                b,
                func.avg(CameraMetric.occupancy_avg),
                func.max(CameraMetric.occupancy_peak),
                func.sum(CameraMetric.footfall),
                func.avg(CameraMetric.queue_avg),
                func.max(CameraMetric.queue_peak),
            )
            .where(
                CameraMetric.organization_id == org_id,
                CameraMetric.bucket >= range_start(range_key),
            )
            .group_by(b)
            .order_by(b)
        )
        rows = (await self._session.execute(stmt)).all()
        points = [
            MetricPoint(
                bucket=r[0],
                occupancy_avg=round(float(r[1] or 0), 2),
                occupancy_peak=int(r[2] or 0),
                footfall=int(r[3] or 0),
                queue_avg=round(float(r[4] or 0), 2),
                queue_peak=int(r[5] or 0),
            )
            for r in rows
        ]
        return TimeseriesResponse(points=points)

    async def alert_breakdown(
        self, org_id: uuid.UUID, *, range_key: str = "7d"
    ) -> AlertBreakdownResponse:
        start = range_start(range_key)
        sev_rows = (
            await self._session.execute(
                select(CameraEvent.severity, func.count())
                .where(CameraEvent.organization_id == org_id, CameraEvent.created_at >= start)
                .group_by(CameraEvent.severity)
            )
        ).all()
        type_rows = (
            await self._session.execute(
                select(CameraEvent.event_type, func.count())
                .where(CameraEvent.organization_id == org_id, CameraEvent.created_at >= start)
                .group_by(CameraEvent.event_type)
            )
        ).all()
        return AlertBreakdownResponse(
            by_severity={r[0]: r[1] for r in sev_rows},
            by_type={r[0]: r[1] for r in type_rows},
        )

    async def camera_health(self, org_id: uuid.UUID) -> CameraHealthResponse:
        total = await self._session.scalar(
            select(func.count()).select_from(Camera).where(
                Camera.organization_id == org_id, Camera.enabled.is_(True)
            )
        ) or 0
        online = await self._session.scalar(
            select(func.count()).select_from(Camera).where(
                Camera.organization_id == org_id, Camera.status == "online"
            )
        ) or 0
        uptime = round((online / total) * 100, 1) if total else 0.0
        return CameraHealthResponse(
            total=total, online=online, offline=max(0, total - online), uptime_pct=uptime
        )
