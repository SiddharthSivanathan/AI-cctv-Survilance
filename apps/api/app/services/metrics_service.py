"""Metrics ingest — persists aggregated per-minute camera metrics."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import set_org_context
from app.models.camera_metric import CameraMetric
from app.schemas.metric import IngestMetricItem


def _floor_minute(ts: float) -> datetime:
    dt = datetime.fromtimestamp(ts, tz=UTC)
    return dt.replace(second=0, microsecond=0)


class MetricsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ingest(self, items: list[IngestMetricItem]) -> int:
        """Upsert aggregated metrics (one row per camera per minute bucket)."""
        written = 0
        for item in items:
            await set_org_context(self._session, str(item.organization_id))
            bucket = _floor_minute(item.bucket)
            existing = await self._session.scalar(
                select(CameraMetric).where(
                    CameraMetric.camera_id == item.camera_id, CameraMetric.bucket == bucket
                )
            )
            if existing is not None:
                existing.occupancy_avg = item.occupancy_avg
                existing.occupancy_peak = item.occupancy_peak
                existing.footfall = item.footfall
                existing.queue_avg = item.queue_avg
                existing.queue_peak = item.queue_peak
            else:
                self._session.add(
                    CameraMetric(
                        organization_id=item.organization_id,
                        store_id=item.store_id,
                        camera_id=item.camera_id,
                        bucket=bucket,
                        occupancy_avg=item.occupancy_avg,
                        occupancy_peak=item.occupancy_peak,
                        footfall=item.footfall,
                        queue_avg=item.queue_avg,
                        queue_peak=item.queue_peak,
                    )
                )
            written += 1
            await self._session.flush()
        await set_org_context(self._session, None)
        return written
