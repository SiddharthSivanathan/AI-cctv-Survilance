"""Notification endpoints (in-app bell, tenant-scoped)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query

from app.core.deps import AuthContext, get_notification_service, require_membership
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.services import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _org(ctx: AuthContext) -> uuid.UUID:
    return ctx.membership.organization_id  # type: ignore[union-attr]


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    ctx: AuthContext = Depends(require_membership),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    return await service.list(_org(ctx), ctx.user.id, unread_only=unread_only, limit=limit)


@router.get("/unread-count")
async def unread_count(
    ctx: AuthContext = Depends(require_membership),
    service: NotificationService = Depends(get_notification_service),
) -> dict[str, int]:
    return {"unread": await service.unread_count(_org(ctx), ctx.user.id)}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    notif = await service.mark_read(notification_id, _org(ctx))
    return NotificationResponse.model_validate(notif)


@router.post("/read-all")
async def mark_all_read(
    ctx: AuthContext = Depends(require_membership),
    service: NotificationService = Depends(get_notification_service),
) -> dict[str, int]:
    updated = await service.mark_all_read(_org(ctx), ctx.user.id)
    return {"updated": updated}
