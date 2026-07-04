"""Store endpoints (tenant-scoped)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.core.deps import (
    AuthContext,
    get_camera_service,
    get_store_service,
    require_membership,
)
from app.schemas.camera import CameraResponse
from app.schemas.store import CreateStoreRequest, StoreResponse, UpdateStoreRequest
from app.services import CameraService, StoreService

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("", response_model=list[StoreResponse])
async def list_stores(
    ctx: AuthContext = Depends(require_membership),
    service: StoreService = Depends(get_store_service),
) -> list[StoreResponse]:
    stores = await service.list(ctx.membership.organization_id)  # type: ignore[union-attr]
    return [StoreResponse.model_validate(s) for s in stores]


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    payload: CreateStoreRequest,
    ctx: AuthContext = Depends(require_membership),
    service: StoreService = Depends(get_store_service),
) -> StoreResponse:
    store = await service.create(
        organization_id=ctx.membership.organization_id,  # type: ignore[union-attr]
        actor_user_id=ctx.user.id,
        data=payload,
    )
    return StoreResponse.model_validate(store)


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(
    store_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: StoreService = Depends(get_store_service),
) -> StoreResponse:
    store = await service.get(store_id, ctx.membership.organization_id)  # type: ignore[union-attr]
    return StoreResponse.model_validate(store)


@router.patch("/{store_id}", response_model=StoreResponse)
async def update_store(
    store_id: uuid.UUID,
    payload: UpdateStoreRequest,
    ctx: AuthContext = Depends(require_membership),
    service: StoreService = Depends(get_store_service),
) -> StoreResponse:
    store = await service.update(
        store_id=store_id,
        organization_id=ctx.membership.organization_id,  # type: ignore[union-attr]
        actor_user_id=ctx.user.id,
        data=payload,
    )
    return StoreResponse.model_validate(store)


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(
    store_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: StoreService = Depends(get_store_service),
) -> None:
    await service.delete(
        store_id=store_id,
        organization_id=ctx.membership.organization_id,  # type: ignore[union-attr]
        actor_user_id=ctx.user.id,
    )


@router.get("/{store_id}/cameras", response_model=list[CameraResponse])
async def list_store_cameras(
    store_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    store_service: StoreService = Depends(get_store_service),
    camera_service: CameraService = Depends(get_camera_service),
) -> list[CameraResponse]:
    """List cameras belonging to a store (validates store ownership first)."""
    org_id = ctx.membership.organization_id  # type: ignore[union-attr]
    await store_service.get(store_id, org_id)  # 404 if not in org
    cameras = await camera_service.list(org_id, store_id=store_id)
    return [CameraResponse.model_validate(c) for c in cameras]
