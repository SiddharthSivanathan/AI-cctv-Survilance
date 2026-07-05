"""Notification repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, notification: Notification) -> Notification:
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def list_for_org(
        self,
        org_id: uuid.UUID,
        *,
        user_id: uuid.UUID | None = None,
        is_read: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.organization_id == org_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if user_id is not None:
            stmt = stmt.where(
                (Notification.user_id == user_id) | (Notification.user_id.is_(None))
            )
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_org(
        self,
        org_id: uuid.UUID,
        *,
        user_id: uuid.UUID | None = None,
        is_read: bool | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Notification).where(
            Notification.organization_id == org_id
        )
        if user_id is not None:
            stmt = stmt.where(
                (Notification.user_id == user_id) | (Notification.user_id.is_(None))
            )
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)
        return await self.session.scalar(stmt) or 0

    async def get(self, notification_id: uuid.UUID) -> Notification | None:
        return await self.session.get(Notification, notification_id)

    async def mark_read(self, notification_id: uuid.UUID, org_id: uuid.UUID) -> Notification | None:
        notif = await self.get(notification_id)
        if notif is None or notif.organization_id != org_id:
            return None
        notif.is_read = True
        notif.read_at = datetime.now(UTC)
        await self.session.flush()
        return notif

    async def mark_all_read(self, org_id: uuid.UUID, user_id: uuid.UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.organization_id == org_id,
                Notification.is_read.is_(False),
                (Notification.user_id == user_id) | (Notification.user_id.is_(None)),
            )
            .values(is_read=True, read_at=datetime.now(UTC))
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount  # type: ignore[return-value]
