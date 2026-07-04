"""Rule service."""

from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError, ValidationError
from app.models.rule import Rule
from app.repositories.camera_repository import CameraRepository
from app.repositories.rule_repository import RuleRepository, ZoneRepository
from app.schemas.rule import RULE_TYPES, CreateRuleRequest, UpdateRuleRequest
from app.services.audit_service import AuditService


class RuleService:
    def __init__(
        self,
        rule_repo: RuleRepository,
        zone_repo: ZoneRepository,
        camera_repo: CameraRepository,
        audit_service: AuditService,
    ) -> None:
        self._rules = rule_repo
        self._zones = zone_repo
        self._cameras = camera_repo
        self._audit = audit_service

    async def list(self, org_id: uuid.UUID, *, camera_id: uuid.UUID | None = None) -> list[Rule]:
        return await self._rules.list_for_org(org_id, camera_id=camera_id)

    async def get(self, rule_id: uuid.UUID, org_id: uuid.UUID) -> Rule:
        rule = await self._rules.get_for_org(rule_id, org_id)
        if rule is None:
            raise NotFoundError("Rule not found")
        return rule

    async def create(
        self, *, org_id: uuid.UUID, actor_user_id: uuid.UUID, data: CreateRuleRequest
    ) -> Rule:
        if data.rule_type not in RULE_TYPES:
            raise ValidationError(f"Unsupported rule type: {data.rule_type}")
        camera = await self._cameras.get_for_org(data.camera_id, org_id)
        if camera is None:
            raise ValidationError("Camera not found in this organization")
        if data.zone_id is not None and await self._zones.get_for_org(data.zone_id, org_id) is None:
            raise ValidationError("Zone not found in this organization")

        rule = await self._rules.add(
            Rule(
                organization_id=org_id,
                camera_id=data.camera_id,
                store_id=camera.store_id,
                zone_id=data.zone_id,
                name=data.name.strip(),
                rule_type=data.rule_type,
                severity=data.severity,
                cooldown_seconds=data.cooldown_seconds,
                enabled=data.enabled,
                config=data.config,
            )
        )
        await self._audit.record(
            action="rule.created",
            organization_id=org_id,
            actor_user_id=actor_user_id,
            resource_type="rule",
            resource_id=str(rule.id),
            metadata={"rule_type": rule.rule_type},
        )
        return rule

    async def update(
        self, *, rule_id: uuid.UUID, org_id: uuid.UUID, actor_user_id: uuid.UUID, data: UpdateRuleRequest
    ) -> Rule:
        rule = await self.get(rule_id, org_id)
        fields = data.model_dump(exclude_unset=True)
        if "zone_id" in fields and fields["zone_id"] is not None:
            if await self._zones.get_for_org(fields["zone_id"], org_id) is None:
                raise ValidationError("Zone not found in this organization")
        for attr, value in fields.items():
            setattr(rule, attr, value)
        await self._rules.session.flush()
        await self._audit.record(
            action="rule.updated",
            organization_id=org_id,
            actor_user_id=actor_user_id,
            resource_type="rule",
            resource_id=str(rule.id),
        )
        return rule

    async def delete(self, *, rule_id: uuid.UUID, org_id: uuid.UUID, actor_user_id: uuid.UUID) -> None:
        rule = await self.get(rule_id, org_id)
        await self._rules.delete(rule)
        await self._audit.record(
            action="rule.deleted",
            organization_id=org_id,
            actor_user_id=actor_user_id,
            resource_type="rule",
            resource_id=str(rule_id),
        )
