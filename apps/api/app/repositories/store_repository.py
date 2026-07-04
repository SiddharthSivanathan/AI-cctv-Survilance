"""Store data access.

Queries filter by ``organization_id`` for clarity/defense-in-depth; Postgres
RLS enforces the same boundary at the database regardless.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.store import Store
from app.repositories.base import BaseRepository


class StoreRepository(BaseRepository[Store]):
    model = Store

    async def list_for_org(self, organization_id: uuid.UUID) -> list[Store]:
        result = await self.session.execute(
            select(Store)
            .where(Store.organization_id == organization_id)
            .order_by(Store.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_org(
        self, store_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Store | None:
        result = await self.session.execute(
            select(Store).where(
                Store.id == store_id, Store.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def count_for_org(self, organization_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(Store.id).where(Store.organization_id == organization_id)
        )
        return len(result.scalars().all())
