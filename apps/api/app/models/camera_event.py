"""Camera (business) event model — the only persisted AI output.

Raw detections are never stored; only meaningful business events reach here,
with an OPEN → RESOLVED lifecycle managed by the Event Service.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import OrganizationScopedMixin, UUIDMixin


class CameraEvent(Base, UUIDMixin, OrganizationScopedMixin):
    __tablename__ = "camera_events"
    __table_args__ = (
        Index("ix_camera_events_org_created", "organization_id", "created_at"),
        Index("ix_camera_events_key_status", "event_key", "status"),
    )

    store_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    camera_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    event_key: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
