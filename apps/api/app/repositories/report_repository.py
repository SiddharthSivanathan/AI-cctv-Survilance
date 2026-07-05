"""Report data access."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    model = Report

    async def list_for_org(
        self, organization_id: uuid.UUID, *, report_type: str | None = None, limit: int = 50
    ) -> list[Report]:
        stmt = select(Report).where(Report.organization_id == organization_id)
        if report_type is not None:
            stmt = stmt.where(Report.report_type == report_type)
        result = await self.session.execute(stmt.order_by(Report.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def get_for_org(self, report_id: uuid.UUID, organization_id: uuid.UUID) -> Report | None:
        result = await self.session.execute(
            select(Report).where(
                Report.id == report_id, Report.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()
