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
from app.models.notification import Notification
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.rule_repository import AlertRepository, CameraEventRepository
from app.schemas.event import IngestEventItem

logger = get_logger("event_service")

# Event types that trigger an immediate email (when enabled).
_EMAIL_EVENT_TYPES = {
    "unattended_billing_counter",
    "queue_threshold_exceeded",
    "occupancy_limit_exceeded",
    "camera_offline",
}

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
        self._orgs = OrganizationRepository(session)
        self._org_cache: dict = {}

    async def ingest(
        self, items: list[IngestEventItem]
    ) -> tuple[dict[str, int], list[dict[str, Any]], list[dict[str, Any]]]:
        """Persist events and return (summary, ws messages, email jobs).

        Both broadcasts and emails are dispatched by the caller AFTER the DB
        transaction commits, so users only ever receive committed events.
        """
        created = resolved = deduped = 0
        messages: list[dict[str, Any]] = []
        email_jobs: list[dict[str, Any]] = []
        for item in items:
            await set_org_context(self._session, str(item.organization_id))
            if item.status == "open":
                did = await self._open(item, email_jobs)
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
        return summary, messages, email_jobs

    async def _org(self, org_id):
        if org_id not in self._org_cache:
            self._org_cache[org_id] = await self._orgs.get(org_id)
        return self._org_cache[org_id]

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

    async def _open(self, item: IngestEventItem, email_jobs: list[dict[str, Any]]) -> int:
        existing = await self._events.get_open_by_key(item.organization_id, item.event_key)
        if existing is not None:
            return 0  # dedup — an open event with this key already exists
        occurred = datetime.fromtimestamp(item.occurred_at, tz=UTC)
        title, message = _describe(item.event_type, item.metadata)
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
        # In-app notification (bell), in the same transaction.
        self._session.add(
            Notification(
                organization_id=item.organization_id,
                event_type=item.event_type,
                title=title,
                message=message,
                severity=item.severity,
                camera_id=item.camera_id,
                store_id=item.store_id,
                notification_metadata=item.metadata,
            )
        )
        # Email job (dispatched after commit), gated by org preferences.
        await self._maybe_email(item, title, message, email_jobs)
        return 1

    async def _maybe_email(
        self, item: IngestEventItem, title: str, message: str, email_jobs: list[dict[str, Any]]
    ) -> None:
        if item.event_type not in _EMAIL_EVENT_TYPES:
            return
        org = await self._org(item.organization_id)
        if org is None or not org.alert_email_enabled or not org.contact_email:
            return
        if org.notify_critical_only and item.severity not in ("high", "critical"):
            return
        email_jobs.append(
            {
                "to": org.contact_email,
                "subject": f"[{org.name}] {title}",
                "body": f"{message}\n\nSeverity: {item.severity}\n— VisionOps AI",
            }
        )

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
