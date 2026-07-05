"""Notification request/response schemas.

Notification email preferences live on the Organization (single source of
truth, RLS-protected) — see the organization settings schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID | None = None
    event_type: str
    title: str
    message: str
    severity: str
    is_read: bool
    read_at: datetime | None = None
    camera_id: uuid.UUID | None = None
    store_id: uuid.UUID | None = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int


class CreateNotificationRequest(BaseModel):
    """Internal schema for creating notifications programmatically."""

    event_type: str = Field(max_length=64)
    title: str = Field(max_length=255)
    message: str = Field(max_length=1024)
    severity: str = Field(default="medium", max_length=16)
    camera_id: uuid.UUID | None = None
    store_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    metadata: dict[str, Any] | None = None
