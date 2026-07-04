"""Alert model — a surfaced camera event requiring attention."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import OrganizationScopedMixin, UUIDMixin


class Alert(Base, UUIDMixin, OrganizationScopedMixin):
    __tablename__ = "alerts"

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("camera_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    camera_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    # open | acknowledged | resolved
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)
    acknowledged: Mapped[bool] = mapped_column(default=False)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
