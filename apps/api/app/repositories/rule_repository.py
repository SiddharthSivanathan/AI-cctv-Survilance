"""Zone + rule + event + alert data access."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.alert import Alert
from app.models.camera_event import CameraEvent
from app.models.rule import Rule
from app.models.zone import Zone
from app.repositories.base import BaseRepository


class ZoneRepository(BaseRepository[Zone]):
    model = Zone

    async def list_for_camera(self, organization_id: uuid.UUID, camera_id: uuid.UUID) -> list[Zone]:
        result = await self.session.execute(
            select(Zone).where(
                Zone.organization_id == organization_id, Zone.camera_id == camera_id
            )
        )
        return list(result.scalars().all())

    async def get_for_org(self, zone_id: uuid.UUID, organization_id: uuid.UUID) -> Zone | None:
        result = await self.session.execute(
            select(Zone).where(Zone.id == zone_id, Zone.organization_id == organization_id)
        )
        return result.scalar_one_or_none()


class RuleRepository(BaseRepository[Rule]):
    model = Rule

    async def list_for_org(
        self, organization_id: uuid.UUID, *, camera_id: uuid.UUID | None = None
    ) -> list[Rule]:
        stmt = select(Rule).where(Rule.organization_id == organization_id)
        if camera_id is not None:
            stmt = stmt.where(Rule.camera_id == camera_id)
        result = await self.session.execute(stmt.order_by(Rule.created_at.desc()))
        return list(result.scalars().all())

    async def get_for_org(self, rule_id: uuid.UUID, organization_id: uuid.UUID) -> Rule | None:
        result = await self.session.execute(
            select(Rule).where(Rule.id == rule_id, Rule.organization_id == organization_id)
        )
        return result.scalar_one_or_none()


class CameraEventRepository(BaseRepository[CameraEvent]):
    model = CameraEvent

    async def get_open_by_key(
        self, organization_id: uuid.UUID, event_key: str
    ) -> CameraEvent | None:
        result = await self.session.execute(
            select(CameraEvent).where(
                CameraEvent.organization_id == organization_id,
                CameraEvent.event_key == event_key,
                CameraEvent.status == "open",
            )
        )
        return result.scalar_one_or_none()

    async def list_for_org(
        self,
        organization_id: uuid.UUID,
        *,
        camera_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[CameraEvent]:
        stmt = select(CameraEvent).where(CameraEvent.organization_id == organization_id)
        if camera_id is not None:
            stmt = stmt.where(CameraEvent.camera_id == camera_id)
        if status is not None:
            stmt = stmt.where(CameraEvent.status == status)
        result = await self.session.execute(
            stmt.order_by(CameraEvent.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())


class AlertRepository(BaseRepository[Alert]):
    model = Alert

    async def get_for_org(self, alert_id: uuid.UUID, organization_id: uuid.UUID) -> Alert | None:
        result = await self.session.execute(
            select(Alert).where(Alert.id == alert_id, Alert.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    async def list_for_org(
        self, organization_id: uuid.UUID, *, status: str | None = None, limit: int = 100
    ) -> list[Alert]:
        stmt = select(Alert).where(Alert.organization_id == organization_id)
        if status is not None:
            stmt = stmt.where(Alert.status == status)
        result = await self.session.execute(stmt.order_by(Alert.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def get_open_by_event(
        self, organization_id: uuid.UUID, event_id: uuid.UUID
    ) -> Alert | None:
        result = await self.session.execute(
            select(Alert).where(
                Alert.organization_id == organization_id,
                Alert.event_id == event_id,
                Alert.status != "resolved",
            )
        )
        return result.scalar_one_or_none()
