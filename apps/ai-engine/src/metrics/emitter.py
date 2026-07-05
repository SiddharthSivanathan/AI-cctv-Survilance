"""Publishes aggregated metrics to the API metrics endpoint."""

from __future__ import annotations

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger("metrics.emitter")


class MetricsEmitter:
    def __init__(self) -> None:
        self._settings = get_settings()

    def emit(self, metrics: list[dict]) -> None:
        if not metrics:
            return
        url = f"{self._settings.api_internal_url.rstrip('/')}/api/v1/internal/metrics"
        try:
            resp = httpx.post(
                url,
                json={"metrics": metrics},
                headers={"X-Internal-Token": self._settings.internal_api_token},
                timeout=10.0,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("metrics_emit_failed", count=len(metrics), error=str(exc))
