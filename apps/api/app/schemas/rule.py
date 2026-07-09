"""Rule schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

RULE_TYPES = {
    "queue_threshold",
    "occupancy_limit",
    "loitering",
    "unattended_billing_counter",
    "intrusion",
    "line_crossing",
}


class CreateRuleRequest(BaseModel):
    camera_id: uuid.UUID
    zone_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    rule_type: str
    severity: str = Field(default="medium")
    cooldown_seconds: int = Field(default=300, ge=0, le=86_400)
    enabled: bool = True
    config: dict[str, Any] | None = None


class UpdateRuleRequest(BaseModel):
    zone_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    severity: str | None = None
    cooldown_seconds: int | None = Field(default=None, ge=0, le=86_400)
    enabled: bool | None = None
    config: dict[str, Any] | None = None


class RuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    camera_id: uuid.UUID
    store_id: uuid.UUID
    zone_id: uuid.UUID | None
    name: str
    rule_type: str
    severity: str
    cooldown_seconds: int
    enabled: bool
    config: dict[str, Any] | None
