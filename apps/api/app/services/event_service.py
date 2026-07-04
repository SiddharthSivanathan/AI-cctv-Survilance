"""Event Service — the sole writer of business events + alerts.

Consumes business events posted by the rule engine, enforces deduplication
(one open event per event_key), manages the OPEN → RESOLVED lifecycle, and
creates alerts. Runs as an internal (non-tenant) operation, setting the RLS
context per event from its organization_id.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import set_org_context
from app.models.alert import Alert
from app.models.camera_event import CameraEvent
from app.repositories.rule_repository import AlertRepository, CameraEventRepository
from app.schemas.event import IngestEventItem

logger = get_logger("event_service")


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._events = CameraEventRepository(session)
        self._alerts = AlertRepository(session)

    async def ingest(self, items: list[IngestEventItem]) -> dict[str, int]:
        created = resolved = deduped = 0
        for item in items:
            await set_org_context(self._session, str(item.organization_id))
            if item.status == "open":
                did = await self._open(item)
                created += did
                deduped += 1 - did
            elif item.status == "resolved":
                resolved += await self._resolve(item)
            await self._session.flush()

        await set_org_context(self._session, None)
        summary = {"created": created, "resolved": resolved, "deduped": deduped}
        logger.info("events_ingested", **summary)
        return summary

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
