"""Organization endpoints (company setup / onboarding)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.deps import (
    AuthContext,
    get_auth_service,
    get_current_context,
    get_organization_service,
    get_request_meta,
)
from app.core.exceptions import NotFoundError
from app.schemas.organization import CreateOrganizationRequest, OrganizationResponse
from app.schemas.user import MeResponse
from app.services import AuthService, OrganizationService, RequestMeta

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=MeResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: CreateOrganizationRequest,
    meta: RequestMeta = Depends(get_request_meta),
    ctx: AuthContext = Depends(get_current_context),
    org_service: OrganizationService = Depends(get_organization_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> MeResponse:
    """Create the caller's company and assign them as Owner (one per user).

    This is step 1 of onboarding. After creation the caller's `needs_onboarding`
    becomes False. A fresh access token reflecting the new org is obtained via
    /auth/refresh or on next login.
    """
    _org, membership = await org_service.create_for_user(
        ctx.user, name=payload.name, industry=payload.industry
    )
    _ = meta
    return await auth_service.build_me(ctx.user, membership)


@router.get("/current", response_model=OrganizationResponse)
async def current_organization(
    ctx: AuthContext = Depends(get_current_context),
    org_service: OrganizationService = Depends(get_organization_service),
) -> OrganizationResponse:
    """Return the caller's organization."""
    if ctx.membership is None:
        raise NotFoundError("No organization for this user")
    org = await org_service.get(ctx.membership.organization_id)
    if org is None:
        raise NotFoundError("Organization not found")
    return OrganizationResponse.model_validate(org)
