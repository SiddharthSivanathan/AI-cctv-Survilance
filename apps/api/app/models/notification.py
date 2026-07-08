"""In-app notification model.

Each notification represents a single event surfaced to users (e.g. camera
going offline, occupancy exceeded). Notifications are org-scoped and
optionally targeted at a specific user.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import JSONB

from app.db.base import Base
from app.models.mixins import OrganizationScopedMixin, UUIDMixin


class Notification(Base, UUIDMixin, OrganizationScopedMixin):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_org_created", "organization_id", "created_at"),
        Index("ix_notifications_user_read", "user_id", "is_read"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1024), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    camera_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    store_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    notification_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
