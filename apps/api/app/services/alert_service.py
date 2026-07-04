"""Alert service — list + acknowledge."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.core.exceptions import NotFoundError
from app.models.alert import Alert
from app.models.camera_event import CameraEvent
from app.repositories.rule_repository import AlertRepository, CameraEventRepository


class AlertService:
    def __init__(self, alert_repo: AlertRepository, event_repo: CameraEventRepository) -> None:
        self._alerts = alert_repo
        self._events = event_repo

    async def list(
        self, org_id: uuid.UUID, *, status: str | None = None, limit: int = 100
    ) -> list[Alert]:
        return await self._alerts.list_for_org(org_id, status=status, limit=limit)

    async def acknowledge(self, alert_id: uuid.UUID, org_id: uuid.UUID, user_id: uuid.UUID) -> Alert:
        alert = await self._alerts.get_for_org(alert_id, org_id)
        if alert is None:
            raise NotFoundError("Alert not found")
        alert.acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(UTC)
        if alert.status == "open":
            alert.status = "acknowledged"
        await self._alerts.session.flush()
        return alert

    async def list_events(
        self,
        org_id: uuid.UUID,
        *,
        camera_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[CameraEvent]:
        return await self._events.list_for_org(
            org_id, camera_id=camera_id, status=status, limit=limit
        )
