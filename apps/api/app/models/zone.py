"""Zone model — a polygon region of interest within a camera view."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import JSONB

from app.db.base import Base, TimestampMixin
from app.models.mixins import OrganizationScopedMixin, UUIDMixin


class Zone(Base, UUIDMixin, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "zones"

    camera_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # queue | restricted | billing_counter | occupancy | entry
    zone_type: Mapped[str] = mapped_column(String(32), nullable=False, default="occupancy")
    # Polygon vertices in 640x640 sampled-frame space: [[x, y], ...]
    polygon: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
