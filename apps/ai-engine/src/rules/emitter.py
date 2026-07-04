"""Publishes business events to the API Event Service (the sole DB writer)."""

from __future__ import annotations

import httpx
import structlog

from src.config import get_settings
from src.rules.types import BusinessEvent

logger = structlog.get_logger("rules.emitter")


class EventEmitter:
    def __init__(self) -> None:
        self._settings = get_settings()

    def emit(self, events: list[BusinessEvent]) -> None:
        if not events:
            return
        url = f"{self._settings.api_internal_url.rstrip('/')}/api/v1/internal/events"
        try:
            resp = httpx.post(
                url,
                json={"events": [e.to_dict() for e in events]},
                headers={"X-Internal-Token": self._settings.internal_api_token},
                timeout=10.0,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("event_emit_failed", count=len(events), error=str(exc))
