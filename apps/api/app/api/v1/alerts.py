"""Events + alerts read endpoints (tenant-scoped)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query

from app.core.deps import AuthContext, get_alert_service, require_membership
from app.schemas.event import AlertResponse, CameraEventResponse
from app.services import AlertService

router = APIRouter(tags=["alerts"])


def _org(ctx: AuthContext) -> uuid.UUID:
    return ctx.membership.organization_id  # type: ignore[union-attr]


@router.get("/events", response_model=list[CameraEventResponse])
async def list_events(
    camera_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    ctx: AuthContext = Depends(require_membership),
    service: AlertService = Depends(get_alert_service),
) -> list[CameraEventResponse]:
    events = await service.list_events(_org(ctx), camera_id=camera_id, status=status, limit=limit)
    return [CameraEventResponse.model_validate(e) for e in events]


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    ctx: AuthContext = Depends(require_membership),
    service: AlertService = Depends(get_alert_service),
) -> list[AlertResponse]:
    alerts = await service.list(_org(ctx), status=status, limit=limit)
    return [AlertResponse.model_validate(a) for a in alerts]


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: AlertService = Depends(get_alert_service),
) -> AlertResponse:
    alert = await service.acknowledge(alert_id, _org(ctx), ctx.user.id)
    return AlertResponse.model_validate(alert)
