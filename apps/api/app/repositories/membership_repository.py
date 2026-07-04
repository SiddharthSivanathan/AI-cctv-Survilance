"""Membership data access."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.membership import Membership
from app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository[Membership]):
    model = Membership

    async def get_for_user(self, user_id: uuid.UUID) -> Membership | None:
        result = await self.session.execute(
            select(Membership).where(Membership.user_id == user_id)
        )
        return result.scalar_one_or_none()
