"""Reusable SQLAlchemy column mixins."""

import uuid

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """Adds a UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )


class OrganizationScopedMixin:
    """Adds a tenant foreign key for org-scoped (RLS-protected) tables."""

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
