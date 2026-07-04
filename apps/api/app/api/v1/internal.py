"""Internal service-to-service endpoints (not tenant-scoped).

Guarded by a shared internal token. Used by the Celery Beat worker (camera
health sweep) and the AI engine (camera stream list for the frame sampler).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import DecryptionError, decrypt
from app.core.deps import require_internal_token
from app.core.rtsp import build_authenticated_url
from app.db.session import get_db, set_org_context
from app.repositories.camera_repository import CameraRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services import CameraHealthService

router = APIRouter(
    prefix="/internal", tags=["internal"], dependencies=[Depends(require_internal_token)]
)


@router.post("/cameras/health-sweep")
async def camera_health_sweep(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    """Probe all enabled cameras across all organizations; update status."""
    return await CameraHealthService(db).sweep()


@router.get("/cameras/streams")
async def camera_streams(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    """Return enabled cameras with decrypted RTSP sources for the AI sampler.

    Internal only. Iterates organizations, setting the RLS context per org so
    cameras are read within their tenant boundary.
    """
    streams: list[dict[str, Any]] = []
    orgs = await OrganizationRepository(db).list_all()
    for org in orgs:
        await set_org_context(db, str(org.id))
        cameras = await CameraRepository(db).list_enabled_for_org(org.id)
        for camera in cameras:
            password = None
            if camera.password_encrypted:
                try:
                    password = decrypt(camera.password_encrypted)
                except DecryptionError:
                    password = None
            streams.append(
                {
                    "camera_id": str(camera.id),
                    "source": build_authenticated_url(camera.rtsp_url, camera.username, password),
                    "sample_fps": camera.sample_fps,
                }
            )
    await set_org_context(db, None)
    return streams
