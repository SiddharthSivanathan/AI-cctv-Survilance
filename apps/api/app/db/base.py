"""Declarative base for all SQLAlchemy ORM models.

ORM models are added starting in Phase 3 (auth/tenancy). Keeping the base
isolated here lets Alembic's autogenerate target a single metadata object.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for ORM models."""


def _utcnow() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    """Adds created_at / updated_at columns to a model.

    Both a Python-side ``default``/``onupdate`` and a DB ``server_default`` are
    set. The Python default means the ORM populates these attributes on the
    instance at INSERT/UPDATE time, so they are never left in an "expired"
    state that would trigger a lazy (synchronous) reload during serialization —
    which under async SQLAlchemy raises ``MissingGreenlet``. The server_default
    keeps rows inserted outside the ORM (raw SQL, migrations) correct too.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
        nullable=False,
    )
