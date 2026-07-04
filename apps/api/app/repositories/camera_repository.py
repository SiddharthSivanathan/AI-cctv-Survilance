"""Camera data access (org-scoped; RLS also enforces isolation)."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.camera import Camera
from app.repositories.base import BaseRepository


class CameraRepository(BaseRepository[Camera]):
    model = Camera

    async def list_for_org(
        self, organization_id: uuid.UUID, *, store_id: uuid.UUID | None = None
    ) -> list[Camera]:
        stmt = select(Camera).where(Camera.organization_id == organization_id)
        if store_id is not None:
            stmt = stmt.where(Camera.store_id == store_id)
        stmt = stmt.order_by(Camera.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_org(
        self, camera_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Camera | None:
        result = await self.session.execute(
            select(Camera).where(
                Camera.id == camera_id, Camera.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def list_enabled_for_org(self, organization_id: uuid.UUID) -> list[Camera]:
        result = await self.session.execute(
            select(Camera).where(
                Camera.organization_id == organization_id, Camera.enabled.is_(True)
            )
        )
        return list(result.scalars().all())
