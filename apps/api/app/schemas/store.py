"""Store schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateStoreRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    address: str | None = Field(default=None, max_length=512)
    city: str | None = Field(default=None, max_length=128)
    country: str | None = Field(default=None, max_length=128)
    timezone: str = Field(default="UTC", max_length=64)


class UpdateStoreRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    address: str | None = Field(default=None, max_length=512)
    city: str | None = Field(default=None, max_length=128)
    country: str | None = Field(default=None, max_length=128)
    timezone: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, max_length=32)


class StoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    code: str | None
    address: str | None
    city: str | None
    country: str | None
    timezone: str
    status: str
    created_at: datetime
    updated_at: datetime
