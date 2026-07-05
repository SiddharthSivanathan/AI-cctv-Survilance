"""Analytics endpoints (tenant-scoped).

Reads aggregated metrics + business events. The overview is cached in Redis
(30s) so frequent dashboard refreshes don't recompute every time.
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, Query

from app.core.deps import AuthContext, get_analytics_service, require_membership
from app.core.redis_client import get_redis
from app.schemas.analytics import (
    AlertBreakdownResponse,
    CameraHealthResponse,
    OverviewResponse,
    TimeseriesResponse,
)
from app.services import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

_OVERVIEW_TTL = 30


def _org(ctx: AuthContext) -> uuid.UUID:
    return ctx.membership.organization_id  # type: ignore[union-attr]


@router.get("/overview", response_model=OverviewResponse)
async def overview(
    ctx: AuthContext = Depends(require_membership),
    service: AnalyticsService = Depends(get_analytics_service),
) -> OverviewResponse:
    org_id = _org(ctx)
    cache_key = f"analytics:overview:{org_id}"
    try:
        cached = await get_redis().get(cache_key)
        if cached:
            return OverviewResponse(**json.loads(cached))
    except Exception:  # noqa: BLE001 - cache is best-effort
        cached = None

    result = await service.overview(org_id)
    try:
        await get_redis().set(cache_key, result.model_dump_json(), ex=_OVERVIEW_TTL)
    except Exception:  # noqa: BLE001
        pass
    return result


@router.get("/timeseries", response_model=TimeseriesResponse)
async def timeseries(
    range: str = Query(default="7d"),
    bucket: str = Query(default="hour"),
    ctx: AuthContext = Depends(require_membership),
    service: AnalyticsService = Depends(get_analytics_service),
) -> TimeseriesResponse:
    return await service.timeseries(_org(ctx), range_key=range, bucket=bucket)


@router.get("/alerts-breakdown", response_model=AlertBreakdownResponse)
async def alerts_breakdown(
    range: str = Query(default="7d"),
    ctx: AuthContext = Depends(require_membership),
    service: AnalyticsService = Depends(get_analytics_service),
) -> AlertBreakdownResponse:
    return await service.alert_breakdown(_org(ctx), range_key=range)


@router.get("/camera-health", response_model=CameraHealthResponse)
async def camera_health(
    ctx: AuthContext = Depends(require_membership),
    service: AnalyticsService = Depends(get_analytics_service),
) -> CameraHealthResponse:
    return await service.camera_health(_org(ctx))
