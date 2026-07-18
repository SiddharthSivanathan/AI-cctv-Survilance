"""Camera endpoints (tenant-scoped)."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.redis_client import get_redis
from app.core.deps import (
    AuthContext,
    get_camera_service,
    get_stream_service,
    require_membership,
)
from app.schemas.camera import (
    CameraResponse,
    ConnectionTestResult,
    CreateCameraRequest,
    TestConnectionRequest,
    UpdateCameraRequest,
)
from app.schemas.stream import LiveStreamResponse
from app.services import CameraService, StreamService

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
        organization_id=_org(ctx),
        actor_user_id=ctx.user.id,
        data=payload,
    )

    await service._cameras.session.refresh(camera)

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


@router.get("/{camera_id}/detections/latest")
async def latest_detections(
    camera_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: CameraService = Depends(get_camera_service),
) -> dict:
    """Return the most recent detection payload for a camera (ephemeral, Redis).

    Used by the live view to overlay bounding boxes. Returns an empty payload
    when no recent detections exist.
    """
    await service.get(camera_id, _org(ctx))  # 404 if not in org

    empty = {
        "camera_id": str(camera_id),
        "person_count": 0,
        "detections": [],
    }

    try:
        raw = await get_redis().get(f"detections:latest:{camera_id}")
    except Exception:  # noqa: BLE001
        return empty

    if not raw:
        return empty

    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return empty


@router.post("/{camera_id}/live", response_model=LiveStreamResponse)
async def start_live(
    camera_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    camera_service: CameraService = Depends(get_camera_service),
    stream_service: StreamService = Depends(get_stream_service),
) -> LiveStreamResponse:
    """Authorize live viewing and return a short-lived WebRTC playback token."""
    camera = await camera_service.get(camera_id, _org(ctx))
    return await stream_service.start_live(camera)


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
        camera_id=camera_id,
        organization_id=_org(ctx),
        actor_user_id=ctx.user.id,
    )
