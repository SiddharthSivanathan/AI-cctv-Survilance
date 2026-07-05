"""Aggregated per-minute camera metrics.

These are aggregates (not raw detections) produced by the AI worker: average /
peak occupancy, footfall (unique tracks entering), and queue length. The
dashboard reads these instead of raw AI telemetry.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import OrganizationScopedMixin, UUIDMixin


class CameraMetric(Base, UUIDMixin, OrganizationScopedMixin):
    __tablename__ = "camera_metrics"
    __table_args__ = (
        UniqueConstraint("camera_id", "bucket", name="uq_camera_metric_bucket"),
    )

    store_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    camera_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    # Minute-truncated timestamp for this aggregate bucket.
    bucket: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    occupancy_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    occupancy_peak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    footfall: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    queue_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    queue_peak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
