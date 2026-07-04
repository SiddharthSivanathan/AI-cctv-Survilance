"""Organization schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateOrganizationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    industry: str | None = Field(default=None, max_length=128)


class UpdateOrganizationRequest(BaseModel):
    """Editable organization settings (all optional — partial update)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    contact_email: EmailStr | None = Field(default=None)
    contact_phone: str | None = Field(default=None, max_length=64)
    address: str | None = Field(default=None, max_length=512)
    timezone: str | None = Field(default=None, max_length=64)
    currency: str | None = Field(default=None, max_length=8)
    alert_email_enabled: bool | None = Field(default=None)


class OrganizationResponse(BaseModel):
    """Full organization profile, including read-only id + creation date."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    industry: str | None
    status: str
    logo_url: str | None
    contact_email: str | None
    contact_phone: str | None
    address: str | None
    timezone: str
    currency: str
    alert_email_enabled: bool
    created_at: datetime
