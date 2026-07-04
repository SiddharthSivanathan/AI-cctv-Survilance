"""Clients for the internal API (camera stream list) and gateway (provisioning)."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger("ingestion.api")


@dataclass
class CameraStream:
    camera_id: str
    source: str  # RTSP URL with embedded credentials (internal use only)
    sample_fps: int


class ControlPlaneClient:
    """Talks to the FastAPI internal endpoints and the gateway."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def list_camera_streams(self) -> list[CameraStream]:
        """Fetch enabled cameras with decrypted sources from the API."""
        url = f"{self._settings.api_internal_url.rstrip('/')}/api/v1/internal/cameras/streams"
        try:
            resp = httpx.get(
                url,
                headers={"X-Internal-Token": self._settings.internal_api_token},
                timeout=15.0,
            )
            resp.raise_for_status()
            return [
                CameraStream(
                    camera_id=item["camera_id"],
                    source=item["source"],
                    sample_fps=int(item.get("sample_fps") or self._settings.default_sample_fps),
                )
                for item in resp.json()
            ]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            logger.warning("list_camera_streams_failed", error=str(exc))
            return []

    def provision_path(self, camera_id: str, source: str) -> bool:
        """Ensure MediaMTX has an on-demand path for the camera (via gateway)."""
        url = f"{self._settings.gateway_internal_url.rstrip('/')}/internal/provision"
        try:
            resp = httpx.post(
                url,
                json={"path": camera_id, "source": source},
                headers={"X-Internal-Token": self._settings.internal_api_token},
                timeout=10.0,
            )
            resp.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.warning("provision_failed", camera_id=camera_id, error=str(exc))
            return False
