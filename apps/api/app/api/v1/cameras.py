"""Camera endpoints (tenant-scoped)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import AuthContext, get_camera_service, require_membership
from app.schemas.camera import (
    CameraResponse,
    ConnectionTestResult,
    CreateCameraRequest,
    TestConnectionRequest,
    UpdateCameraRequest,
)
from app.services import CameraService

router = APIRouter(prefix="/cameras", tags=["cameras"])


def _org(ctx: AuthContext) -> uuid.UUID:
    return ctx.membership.organization_id  # type: ignore[union-attr]


@router.get("", response_model=list[CameraResponse])
async def list_cameras(
    store_id: uuid.UUID | None = Query(default=None),
    ctx: AuthContext = Depends(require_membership),
    service: CameraService = Depends(get_camera_service),
) -> list[CameraResponse]:
    cameras = await service.list(_org(ctx), store_id=store_id)
    return [CameraResponse.model_validate(c) for c in cameras]


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    payload: CreateCameraRequest,
    ctx: AuthContext = Depends(require_membership),
    service: CameraService = Depends(get_camera_service),
) -> CameraResponse:
    camera = await service.create(
        organization_id=_org(ctx), actor_user_id=ctx.user.id, data=payload
    )
    return CameraResponse.model_validate(camera)


@router.post("/test-connection", response_model=ConnectionTestResult)
async def test_connection(
    payload: TestConnectionRequest,
    _ctx: AuthContext = Depends(require_membership),
    service: CameraService = Depends(get_camera_service),
) -> ConnectionTestResult:
    """Probe an RTSP URL before saving a camera."""
    return await service.test_connection(payload)


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: CameraService = Depends(get_camera_service),
) -> CameraResponse:
    camera = await service.get(camera_id, _org(ctx))
    return CameraResponse.model_validate(camera)


@router.patch("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: uuid.UUID,
    payload: UpdateCameraRequest,
    ctx: AuthContext = Depends(require_membership),
    service: CameraService = Depends(get_camera_service),
) -> CameraResponse:
    camera = await service.update(
        camera_id=camera_id,
        organization_id=_org(ctx),
        actor_user_id=ctx.user.id,
        data=payload,
    )
    return CameraResponse.model_validate(camera)


@router.post("/{camera_id}/test", response_model=CameraResponse)
async def test_camera(
    camera_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: CameraService = Depends(get_camera_service),
) -> CameraResponse:
    """Re-probe an existing camera and refresh its status."""
    camera = await service.test(camera_id, _org(ctx))
    return CameraResponse.model_validate(camera)


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: CameraService = Depends(get_camera_service),
) -> None:
    await service.delete(
        camera_id=camera_id, organization_id=_org(ctx), actor_user_id=ctx.user.id
    )
