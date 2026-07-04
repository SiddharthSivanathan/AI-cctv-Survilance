"""Zone endpoints (tenant-scoped)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import AuthContext, get_zone_service, require_membership
from app.schemas.zone import CreateZoneRequest, UpdateZoneRequest, ZoneResponse
from app.services import ZoneService

router = APIRouter(prefix="/zones", tags=["zones"])


def _org(ctx: AuthContext) -> uuid.UUID:
    return ctx.membership.organization_id  # type: ignore[union-attr]


@router.get("", response_model=list[ZoneResponse])
async def list_zones(
    camera_id: uuid.UUID = Query(...),
    ctx: AuthContext = Depends(require_membership),
    service: ZoneService = Depends(get_zone_service),
) -> list[ZoneResponse]:
    zones = await service.list_for_camera(_org(ctx), camera_id)
    return [ZoneResponse.model_validate(z) for z in zones]


@router.post("", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(
    payload: CreateZoneRequest,
    ctx: AuthContext = Depends(require_membership),
    service: ZoneService = Depends(get_zone_service),
) -> ZoneResponse:
    zone = await service.create(org_id=_org(ctx), data=payload)
    return ZoneResponse.model_validate(zone)


@router.patch("/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: uuid.UUID,
    payload: UpdateZoneRequest,
    ctx: AuthContext = Depends(require_membership),
    service: ZoneService = Depends(get_zone_service),
) -> ZoneResponse:
    zone = await service.update(zone_id=zone_id, org_id=_org(ctx), data=payload)
    return ZoneResponse.model_validate(zone)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: ZoneService = Depends(get_zone_service),
) -> None:
    await service.delete(zone_id=zone_id, org_id=_org(ctx))
