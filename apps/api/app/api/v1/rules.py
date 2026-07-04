"""Rule endpoints (tenant-scoped)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import AuthContext, get_rule_service, require_membership
from app.schemas.rule import CreateRuleRequest, RuleResponse, UpdateRuleRequest
from app.services import RuleService

router = APIRouter(prefix="/rules", tags=["rules"])


def _org(ctx: AuthContext) -> uuid.UUID:
    return ctx.membership.organization_id  # type: ignore[union-attr]


@router.get("", response_model=list[RuleResponse])
async def list_rules(
    camera_id: uuid.UUID | None = Query(default=None),
    ctx: AuthContext = Depends(require_membership),
    service: RuleService = Depends(get_rule_service),
) -> list[RuleResponse]:
    rules = await service.list(_org(ctx), camera_id=camera_id)
    return [RuleResponse.model_validate(r) for r in rules]


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: CreateRuleRequest,
    ctx: AuthContext = Depends(require_membership),
    service: RuleService = Depends(get_rule_service),
) -> RuleResponse:
    rule = await service.create(org_id=_org(ctx), actor_user_id=ctx.user.id, data=payload)
    return RuleResponse.model_validate(rule)


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: RuleService = Depends(get_rule_service),
) -> RuleResponse:
    return RuleResponse.model_validate(await service.get(rule_id, _org(ctx)))


@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: uuid.UUID,
    payload: UpdateRuleRequest,
    ctx: AuthContext = Depends(require_membership),
    service: RuleService = Depends(get_rule_service),
) -> RuleResponse:
    rule = await service.update(
        rule_id=rule_id, org_id=_org(ctx), actor_user_id=ctx.user.id, data=payload
    )
    return RuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: uuid.UUID,
    ctx: AuthContext = Depends(require_membership),
    service: RuleService = Depends(get_rule_service),
) -> None:
    await service.delete(rule_id=rule_id, org_id=_org(ctx), actor_user_id=ctx.user.id)
