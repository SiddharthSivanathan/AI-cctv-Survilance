"""Organization (tenant) model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.mixins import UUIDMixin

if TYPE_CHECKING:
    from app.models.membership import Membership
    from app.models.store import Store


class Organization(Base, UUIDMixin, TimestampMixin):
    """A tenant. Owns all tenant-scoped resources (stores, cameras, events)."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    # Settings / profile
    logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    alert_email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    stores: Mapped[list[Store]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
