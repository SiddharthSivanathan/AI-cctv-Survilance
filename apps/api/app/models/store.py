"""Store (physical location) model.

A Store is one physical site owned by an Organization. It will own cameras,
AI events, alerts, and reports in later phases. Tenant-scoped and protected by
Row-Level Security.

Note: V1 has no Branch entity. A `branches` table can be added later without
altering this model — Stores simply gain child branches at that point.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.mixins import OrganizationScopedMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization


class Store(Base, UUIDMixin, OrganizationScopedMixin, TimestampMixin):
    __tablename__ = "stores"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    organization: Mapped[Organization] = relationship(back_populates="stores")
