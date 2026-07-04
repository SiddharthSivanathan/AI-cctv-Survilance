"""Camera event + alert schemas (business events)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IngestEventItem(BaseModel):
    """A single business event posted by the rule engine (internal)."""

    event_key: str
    camera_id: uuid.UUID
    organization_id: uuid.UUID
    store_id: uuid.UUID | None = None
    rule_id: uuid.UUID | None = None
    event_type: str
    status: str  # "open" | "resolved"
    severity: str = "medium"
    occurred_at: float  # unix seconds
    metadata: dict[str, Any] | None = None


class IngestEventsRequest(BaseModel):
    events: list[IngestEventItem] = Field(default_factory=list)


class CameraEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    camera_id: uuid.UUID
    store_id: uuid.UUID | None
    rule_id: uuid.UUID | None
    event_type: str
    severity: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
    created_at: datetime


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    camera_id: uuid.UUID | None
    event_type: str
    severity: str
    status: str
    acknowledged: bool
    acknowledged_at: datetime | None
    created_at: datetime
