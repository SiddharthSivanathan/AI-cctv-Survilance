"""Report model — a generated operational report snapshot.

Stores the computed report payload (KPIs, trends, tables, deterministic
narrative + recommendations) for a period. Tenant-scoped, RLS-protected.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import OrganizationScopedMixin, UUIDMixin


class Report(Base, UUIDMixin, OrganizationScopedMixin):
    __tablename__ = "reports"

    store_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    report_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # daily|weekly|monthly
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ready")
    # Full computed report payload (see schemas.report.ReportResponse).
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
