"""Health and readiness endpoints.

- /health   liveness (process is up)
- /ready     readiness (dependencies reachable: DB, Redis)
"""

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.health import DependencyStatus, HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    """Return liveness status. Does not touch dependencies."""
    return HealthResponse(status="ok", version=__version__)


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness probe")
async def ready(db: AsyncSession = Depends(get_db)) -> ReadinessResponse:
    """Return readiness including database and Redis connectivity."""
    settings = get_settings()
    dependencies: list[DependencyStatus] = []

    # Database
    try:
        await db.execute(text("SELECT 1"))
        dependencies.append(DependencyStatus(name="postgres", status="up"))
    except Exception as exc:  # noqa: BLE001 - report as down, don't crash probe
        logger.warning("readiness_db_check_failed", error=str(exc))
        dependencies.append(DependencyStatus(name="postgres", status="down"))

    # Redis
    try:
        client = aioredis.from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
        dependencies.append(DependencyStatus(name="redis", status="up"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("readiness_redis_check_failed", error=str(exc))
        dependencies.append(DependencyStatus(name="redis", status="down"))

    all_up = all(dep.status == "up" for dep in dependencies)
    return ReadinessResponse(
        status="ok" if all_up else "degraded",
        version=__version__,
        dependencies=dependencies,
    )
