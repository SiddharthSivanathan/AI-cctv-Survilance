"""Notification service (in-app bell)."""

from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationListResponse, NotificationResponse


class NotificationService:
    def __init__(self, repo: NotificationRepository) -> None:
        self._repo = repo

    async def list(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        unread_only: bool = False,
        limit: int = 50,
    ) -> NotificationListResponse:
        items = await self._repo.list_for_org(
            org_id, user_id=user_id, is_read=False if unread_only else None, limit=limit
        )
        total = await self._repo.count_for_org(org_id, user_id=user_id)
        unread = await self._repo.count_for_org(org_id, user_id=user_id, is_read=False)
        return NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in items],
            total=total,
            unread_count=unread,
        )

    async def unread_count(self, org_id: uuid.UUID, user_id: uuid.UUID) -> int:
        return await self._repo.count_for_org(org_id, user_id=user_id, is_read=False)

    async def mark_read(
        self, notification_id: uuid.UUID, org_id: uuid.UUID
    ) -> Notification:
        notif = await self._repo.mark_read(notification_id, org_id)
        if notif is None:
            raise NotFoundError("Notification not found")
        return notif

    async def mark_all_read(self, org_id: uuid.UUID, user_id: uuid.UUID) -> int:
        return await self._repo.mark_all_read(org_id, user_id)
