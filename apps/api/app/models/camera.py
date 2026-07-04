"""Camera model (tenant-scoped, RLS-protected).

A Camera belongs to a Store. RTSP passwords are stored ENCRYPTED
(``password_encrypted``) and never returned by the API. The ``rtsp_url`` is
stored with any embedded userinfo stripped, so it is safe to return.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.mixins import OrganizationScopedMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.store import Store


class Camera(Base, UUIDMixin, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "cameras"

    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    camera_type: Mapped[str] = mapped_column(String(32), nullable=False, default="ip")
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Connection (rtsp_url has userinfo stripped; password stored encrypted).
    rtsp_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_encrypted: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Detected stream metadata.
    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    codec: Mapped[str | None] = mapped_column(String(32), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # AI sampling rate (used by the inference pipeline in a later phase).
    sample_fps: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    # Status / health.
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    offline_alerted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    store: Mapped[Store] = relationship()

    @property
    def has_credentials(self) -> bool:
        return self.password_encrypted is not None
