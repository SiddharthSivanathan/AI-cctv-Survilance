"""Camera health monitoring sweep.

Runs periodically (triggered by the Celery Beat worker via an internal
endpoint). For each organization it sets the tenant RLS context, re-probes
enabled cameras, updates status + last_seen, and emits a ``camera.offline``
event when a camera has been unreachable beyond the configured threshold.

The full Alert entity + notification delivery lands in Phase 10; here the
offline condition is recorded on the event/audit trail.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.crypto import DecryptionError, decrypt
from app.core.logging import get_logger
from app.core.pubsub import build_message
from app.core.rtsp import ProbeStatus, probe_rtsp
from app.db.session import set_org_context
from app.repositories.audit_repository import AuditRepository
from app.repositories.camera_repository import CameraRepository
from app.repositories.organization_repository import OrganizationRepository
from app.services.audit_service import AuditService

logger = get_logger("camera_health")


class CameraHealthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._settings = get_settings()
        self._audit = AuditService(AuditRepository(session))
        self.messages: list[dict[str, Any]] = []

    async def sweep(self) -> dict[str, int]:
        """Probe all enabled cameras across all organizations.

        Collects camera status-change broadcast messages in ``self.messages``
        for the caller to publish after commit.
        """
        orgs = await OrganizationRepository(self._session).list_all()
        online = offline = alerts = 0

        for org in orgs:
            await set_org_context(self._session, str(org.id))
            cameras = await CameraRepository(self._session).list_enabled_for_org(org.id)
            now = datetime.now(UTC)

            for camera in cameras:
                password = None
                if camera.password_encrypted:
                    try:
                        password = decrypt(camera.password_encrypted)
                    except DecryptionError:
                        password = None

                result = await probe_rtsp(
                    camera.rtsp_url,
                    username=camera.username,
                    password=password,
                    timeout=float(self._settings.rtsp_probe_timeout_seconds),
                    capture_frame=False,
                )

                previous = camera.status
                if result.status is ProbeStatus.CONNECTED:
                    camera.status = "online"
                    camera.last_seen_at = now
                    camera.last_error = None
                    camera.offline_alerted_at = None
                    online += 1
                    if previous == "offline":
                        self._add_status_message(org.id, camera, "camera.reconnected", now)
                    elif previous != "online":
                        self._add_status_message(org.id, camera, "camera.online", now)
                else:
                    camera.status = "offline"
                    camera.last_error = f"{result.status.value}: {result.message or ''}".strip()
                    offline += 1
                    if previous != "offline":
                        self._add_status_message(org.id, camera, "camera.offline", now)
                    reference = camera.last_seen_at or camera.created_at
                    elapsed = (now - reference).total_seconds()
                    if (
                        elapsed > self._settings.camera_offline_threshold_seconds
                        and camera.offline_alerted_at is None
                    ):
                        await self._audit.record(
                            action="camera.offline",
                            organization_id=org.id,
                            resource_type="camera",
                            resource_id=str(camera.id),
                            metadata={"name": camera.name, "offline_seconds": int(elapsed)},
                        )
                        camera.offline_alerted_at = now
                        alerts += 1

            await self._session.flush()

        await set_org_context(self._session, None)
        summary = {
            "organizations": len(orgs),
            "online": online,
            "offline": offline,
            "offline_alerts": alerts,
        }
        logger.info("camera_health_sweep", **summary)
        return summary

    def _add_status_message(self, org_id, camera, ws_type: str, now: datetime) -> None:
        titles = {
            "camera.offline": "Camera offline",
            "camera.online": "Camera online",
            "camera.reconnected": "Camera reconnected",
        }
        self.messages.append(
            build_message(
                type=ws_type,
                organization_id=str(org_id),
                camera_id=str(camera.id),
                store_id=str(camera.store_id),
                severity="high" if ws_type == "camera.offline" else "low",
                title=titles[ws_type],
                message=f"{camera.name} is {ws_type.split('.')[1]}.",
                timestamp=now.isoformat(),
                metadata={"eventType": ws_type},
            )
        )
