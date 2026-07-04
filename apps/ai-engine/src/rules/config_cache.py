"""Rules + zones configuration cache.

Fetches per-camera rules and zones from the API internal endpoint and refreshes
them periodically. The rule engine reads config from here — it never queries the
database.
"""

from __future__ import annotations

import time

import httpx
import structlog

from src.config import get_settings
from src.rules.types import Rule, Zone

logger = structlog.get_logger("rules.config")


class RulesConfigCache:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._rules: dict[str, list[Rule]] = {}
        self._zones: dict[str, dict[str, Zone]] = {}
        self._last_refresh = 0.0

    def maybe_refresh(self, now: float | None = None) -> None:
        now = now if now is not None else time.time()
        if now - self._last_refresh < self._settings.rules_refresh_seconds:
            return
        self.refresh()
        self._last_refresh = now

    def refresh(self) -> None:
        url = f"{self._settings.api_internal_url.rstrip('/')}/api/v1/internal/rules-config"
        try:
            resp = httpx.get(
                url,
                headers={"X-Internal-Token": self._settings.internal_api_token},
                timeout=15.0,
            )
            resp.raise_for_status()
            self._load(resp.json())
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            logger.warning("rules_config_refresh_failed", error=str(exc))

    def _load(self, payload: list[dict]) -> None:
        rules: dict[str, list[Rule]] = {}
        zones: dict[str, dict[str, Zone]] = {}
        for cam in payload:
            camera_id = cam["camera_id"]
            zones[camera_id] = {
                z["id"]: Zone(id=z["id"], polygon=[tuple(p) for p in z["polygon"]])
                for z in cam.get("zones", [])
            }
            rules[camera_id] = [
                Rule(
                    id=r["id"],
                    camera_id=camera_id,
                    rule_type=r["rule_type"],
                    zone_id=r.get("zone_id"),
                    organization_id=cam.get("organization_id", ""),
                    store_id=cam.get("store_id", ""),
                    severity=r.get("severity", "medium"),
                    cooldown_seconds=int(r.get("cooldown_seconds", 300)),
                    config=r.get("config") or {},
                )
                for r in cam.get("rules", [])
                if r.get("enabled", True)
            ]
        self._rules = rules
        self._zones = zones

    def rules_for(self, camera_id: str) -> list[Rule]:
        return self._rules.get(camera_id, [])

    def zones_for(self, camera_id: str) -> dict[str, Zone]:
        return self._zones.get(camera_id, {})
