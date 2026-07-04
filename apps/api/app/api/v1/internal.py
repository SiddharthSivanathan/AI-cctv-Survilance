"""Internal service-to-service endpoints (not tenant-scoped).

Guarded by a shared internal token. Used by the Celery Beat worker to trigger
the periodic camera health sweep.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_internal_token
from app.db.session import get_db
from app.services import CameraHealthService

router = APIRouter(prefix="/internal", tags=["internal"], dependencies=[Depends(require_internal_token)])


@router.post("/cameras/health-sweep")
async def camera_health_sweep(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    """Probe all enabled cameras across all organizations; update status."""
    return await CameraHealthService(db).sweep()
