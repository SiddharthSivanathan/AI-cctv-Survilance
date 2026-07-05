"""Event Service — the sole writer of business events + alerts.

Consumes business events posted by the rule engine, enforces deduplication
(one open event per event_key), manages the OPEN → RESOLVED lifecycle, and
creates alerts. Runs as an internal (non-tenant) operation, setting the RLS
context per event from its organization_id.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from typing import Any

from app.core.logging import get_logger
from app.core.pubsub import build_message
from app.db.session import set_org_context
from app.models.alert import Alert
from app.models.camera_event import CameraEvent
from app.repositories.rule_repository import AlertRepository, CameraEventRepository
from app.schemas.event import IngestEventItem

logger = get_logger("event_service")

# Human-readable titles per business event type.
_TITLES: dict[str, str] = {
    "queue_threshold_exceeded": "Queue threshold exceeded",
    "queue_resolved": "Queue cleared",
    "occupancy_limit_exceeded": "Occupancy limit exceeded",
    "occupancy_normalized": "Occupancy back to normal",
    "loitering_detected": "Loitering detected",
    "loitering_ended": "Loitering ended",
    "unattended_billing_counter": "Billing counter unattended",
    "billing_counter_staffed": "Billing counter staffed",
    "camera_offline": "Camera offline",
    "camera_online": "Camera online",
}


def _describe(event_type: str, metadata: dict[str, Any] | None) -> tuple[str, str]:
    title = _TITLES.get(event_type, event_type.replace("_", " ").title())
    md = metadata or {}
    if "count" in md:
        message = f"{md['count']} detected."
    elif "empty_seconds" in md:
        message = f"No person detected for {md['empty_seconds']}s."
    elif "dwell_seconds" in md:
        message = f"Person present for {md['dwell_seconds']}s."
    elif "duration_seconds" in md:
        message = f"Resolved after {md['duration_seconds']}s."
    else:
        message = title
    return title, message


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._events = CameraEventRepository(session)
        self._alerts = AlertRepository(session)

    async def ingest(
        self, items: list[IngestEventItem]
    ) -> tuple[dict[str, int], list[dict[str, Any]]]:
        """Persist events and return (summary, broadcast messages).

        Messages are broadcast by the caller AFTER the DB transaction commits,
        so clients only ever receive committed events.
        """
        created = resolved = deduped = 0
        messages: list[dict[str, Any]] = []
        for item in items:
            await set_org_context(self._session, str(item.organization_id))
            if item.status == "open":
                did = await self._open(item)
                created += did
                deduped += 1 - did
                if did:
                    messages.append(self._message("alert.created", item))
            elif item.status == "resolved":
                did = await self._resolve(item)
                resolved += did
                if did:
                    messages.append(self._message("alert.resolved", item))
            await self._session.flush()

        await set_org_context(self._session, None)
        summary = {"created": created, "resolved": resolved, "deduped": deduped}
        logger.info("events_ingested", **summary)
        return summary, messages

    def _message(self, ws_type: str, item: IngestEventItem) -> dict[str, Any]:
        title, message = _describe(item.event_type, item.metadata)
        return build_message(
            type=ws_type,
            organization_id=str(item.organization_id),
            camera_id=str(item.camera_id),
            store_id=str(item.store_id) if item.store_id else None,
            severity=item.severity,
            title=title,
            message=message,
            timestamp=datetime.fromtimestamp(item.occurred_at, tz=UTC).isoformat(),
            metadata={"eventType": item.event_type, **(item.metadata or {})},
        )

    async def _open(self, item: IngestEventItem) -> int:
        existing = await self._events.get_open_by_key(item.organization_id, item.event_key)
        if existing is not None:
            return 0  # dedup — an open event with this key already exists
        occurred = datetime.fromtimestamp(item.occurred_at, tz=UTC)
        event = CameraEvent(
            organization_id=item.organization_id,
            store_id=item.store_id,
            camera_id=item.camera_id,
            rule_id=item.rule_id,
            event_key=item.event_key,
            event_type=item.event_type,
            severity=item.severity,
            status="open",
            started_at=occurred,
            event_metadata=item.metadata,
        )
        await self._events.add(event)
        await self._alerts.add(
            Alert(
                organization_id=item.organization_id,
                event_id=event.id,
                camera_id=item.camera_id,
                event_type=item.event_type,
                severity=item.severity,
                status="open",
            )
        )
        return 1

    async def _resolve(self, item: IngestEventItem) -> int:
        existing = await self._events.get_open_by_key(item.organization_id, item.event_key)
        if existing is None:
            return 0
        occurred = datetime.fromtimestamp(item.occurred_at, tz=UTC)
        existing.status = "resolved"
        existing.ended_at = occurred
        existing.duration_seconds = max(
            0, int(item.occurred_at - existing.started_at.timestamp())
        )
        alert = await self._alerts.get_open_by_event(item.organization_id, existing.id)
        if alert is not None:
            alert.status = "resolved"
        return 1
