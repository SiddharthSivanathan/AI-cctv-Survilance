"""Zone service."""

from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError, ValidationError
from app.models.zone import Zone
from app.repositories.camera_repository import CameraRepository
from app.repositories.rule_repository import ZoneRepository
from app.schemas.zone import CreateZoneRequest, UpdateZoneRequest


class ZoneService:
    def __init__(self, zone_repo: ZoneRepository, camera_repo: CameraRepository) -> None:
        self._zones = zone_repo
        self._cameras = camera_repo

    async def list_for_camera(self, org_id: uuid.UUID, camera_id: uuid.UUID) -> list[Zone]:
        return await self._zones.list_for_camera(org_id, camera_id)

    async def get(self, zone_id: uuid.UUID, org_id: uuid.UUID) -> Zone:
        zone = await self._zones.get_for_org(zone_id, org_id)
        if zone is None:
            raise NotFoundError("Zone not found")
        return zone

    async def create(self, *, org_id: uuid.UUID, data: CreateZoneRequest) -> Zone:
        if await self._cameras.get_for_org(data.camera_id, org_id) is None:
            raise ValidationError("Camera not found in this organization")
        return await self._zones.add(
            Zone(
                organization_id=org_id,
                camera_id=data.camera_id,
                name=data.name.strip(),
                zone_type=data.zone_type,
                polygon=[list(p) for p in data.polygon],
                config=data.config,
            )
        )

    async def update(self, *, zone_id: uuid.UUID, org_id: uuid.UUID, data: UpdateZoneRequest) -> Zone:
        zone = await self.get(zone_id, org_id)
        fields = data.model_dump(exclude_unset=True)
        if "polygon" in fields and fields["polygon"] is not None:
            zone.polygon = [list(p) for p in fields.pop("polygon")]
        for attr, value in fields.items():
            if value is not None or attr == "config":
                setattr(zone, attr, value)
        await self._zones.session.flush()
        return zone

    async def delete(self, *, zone_id: uuid.UUID, org_id: uuid.UUID) -> None:
        zone = await self.get(zone_id, org_id)
        await self._zones.delete(zone)
