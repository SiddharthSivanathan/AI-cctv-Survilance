"""User (global identity) model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.mixins import UUIDMixin

if TYPE_CHECKING:
    from app.models.membership import Membership


class User(Base, UUIDMixin, TimestampMixin):
    """An authenticatable user identity.

    Email is stored lower-cased with a unique constraint. In V1 a user belongs
    to exactly one organization via a single Membership; the schema supports
    many-users-per-org and future invitations without change.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    membership: Mapped[Membership | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
