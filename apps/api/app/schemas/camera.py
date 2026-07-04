"""Camera schemas. Passwords are write-only and never serialized back."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateCameraRequest(BaseModel):
    store_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    camera_type: str = Field(default="ip", max_length=32)
    description: str | None = Field(default=None, max_length=512)
    rtsp_url: str = Field(min_length=1, max_length=1024)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=255)
    manufacturer: str | None = Field(default=None, max_length=128)
    model: str | None = Field(default=None, max_length=128)
    sample_fps: int = Field(default=2, ge=1, le=30)


class UpdateCameraRequest(BaseModel):
    store_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=512)
    rtsp_url: str | None = Field(default=None, max_length=1024)
    username: str | None = Field(default=None, max_length=255)
    # Blank/omitted password keeps the stored one; a value replaces it.
    password: str | None = Field(default=None, max_length=255)
    sample_fps: int | None = Field(default=None, ge=1, le=30)
    enabled: bool | None = None


class CameraResponse(BaseModel):
    """Camera representation. Never includes the password."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    store_id: uuid.UUID
    name: str
    camera_type: str
    description: str | None
    rtsp_url: str
    username: str | None
    has_credentials: bool
    manufacturer: str | None
    model: str | None
    resolution: str | None
    fps: float | None
    codec: str | None
    thumbnail_url: str | None
    sample_fps: int
    status: str
    enabled: bool
    last_seen_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class TestConnectionRequest(BaseModel):
    """Probe an RTSP URL before saving (credentials optional)."""

    rtsp_url: str = Field(min_length=1, max_length=1024)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=255)


class ConnectionTestResult(BaseModel):
    status: str  # connected | auth_failed | unreachable | invalid_url | timeout | error
    message: str | None = None
    resolution: str | None = None
    fps: float | None = None
    codec: str | None = None
    thumbnail_url: str | None = None
