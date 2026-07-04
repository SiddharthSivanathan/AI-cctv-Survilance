"""Live stream service.

Authorizes live viewing, provisions the camera's MediaMTX path via the Go
gateway, and issues a short-lived HMAC playback token the gateway verifies.
The decrypted RTSP source (with credentials) is sent only to the gateway over
the internal network — never to the browser.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
from jose import jwt

from app.core.config import get_settings
from app.core.crypto import decrypt
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.core.rtsp import build_authenticated_url
from app.models.camera import Camera
from app.schemas.stream import LiveStreamResponse

logger = get_logger("stream")


class StreamUnavailableError(AppError):
    status_code = 503
    code = "stream_unavailable"


class StreamService:
    def __init__(self) -> None:
        self._settings = get_settings()

    async def start_live(self, camera: Camera) -> LiveStreamResponse:
        """Provision the media path and return WebRTC playback details."""
        path = str(camera.id)
        password = decrypt(camera.password_encrypted) if camera.password_encrypted else None
        source = build_authenticated_url(camera.rtsp_url, camera.username, password)

        await self._provision(path, source)

        now = datetime.now(UTC)
        ttl = self._settings.stream_token_ttl_seconds
        expires_at = now + timedelta(seconds=ttl)
        token = jwt.encode(
            {"path": path, "exp": expires_at, "iat": now},
            self._settings.stream_jwt_secret,
            algorithm="HS256",
        )

        return LiveStreamResponse(
            camera_id=camera.id,
            whep_url=f"{self._settings.gateway_public_url.rstrip('/')}/whep/{path}",
            token=token,
            expires_in=ttl,
            expires_at=expires_at,
        )

    async def _provision(self, path: str, source: str) -> None:
        url = f"{self._settings.gateway_internal_url.rstrip('/')}/internal/provision"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    json={"path": path, "source": source},
                    headers={"X-Internal-Token": self._settings.internal_api_token},
                )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("stream_provision_failed", path=path, error=str(exc))
            raise StreamUnavailableError("Live streaming is currently unavailable") from exc
