"""User schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.organization import OrganizationResponse


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_email_verified: bool


class MeResponse(BaseModel):
    """Authenticated user's full context: profile, org, role, onboarding state."""

    user: UserResponse
    organization: OrganizationResponse | None
    role: str | None
    needs_onboarding: bool
