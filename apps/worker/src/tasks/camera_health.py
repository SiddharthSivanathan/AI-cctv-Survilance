"""Periodic camera health sweep task.

Triggers the API's internal health-sweep endpoint, which performs the actual
RTSP probing and status updates (keeping all DB/credential logic in the API).
"""

from __future__ import annotations

import httpx
import structlog

from src.celery_app import celery_app
from src.config import get_settings

logger = structlog.get_logger("camera_health")


@celery_app.task(name="visionops.cameras.health_sweep")
def health_sweep() -> dict | None:
    """Call the API internal endpoint to sweep camera health."""
    settings = get_settings()
    url = f"{settings.api_internal_url.rstrip('/')}/api/v1/internal/cameras/health-sweep"
    try:
        response = httpx.post(
            url,
            headers={"X-Internal-Token": settings.internal_api_token},
            timeout=120.0,
        )
        response.raise_for_status()
        summary = response.json()
        logger.info("camera_health_sweep_ok", **summary)
        return summary
    except httpx.HTTPError as exc:
        logger.warning("camera_health_sweep_failed", error=str(exc))
        return None
