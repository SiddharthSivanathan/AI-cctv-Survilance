"""Zone schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

Polygon = list[tuple[float, float]]


class CreateZoneRequest(BaseModel):
    camera_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    zone_type: str = Field(default="occupancy", max_length=32)
    polygon: Polygon = Field(min_length=3)
    config: dict[str, Any] | None = None


class UpdateZoneRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    zone_type: str | None = Field(default=None, max_length=32)
    polygon: Polygon | None = Field(default=None, min_length=3)
    config: dict[str, Any] | None = None


class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    camera_id: uuid.UUID
    name: str
    zone_type: str
    polygon: list[Any]
    config: dict[str, Any] | None
