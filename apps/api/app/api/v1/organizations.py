"""Organization endpoints: onboarding (create) + settings + logo."""

from __future__ import annotations

import io
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.core.deps import (
    AuthContext,
    get_auth_service,
    get_current_context,
    get_organization_service,
    get_request_meta,
    get_storage,
    require_membership,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.storage import ObjectStorage, StorageError
from app.schemas.organization import (
    CreateOrganizationRequest,
    OrganizationResponse,
    UpdateOrganizationRequest,
)
from app.schemas.user import MeResponse
from app.services import AuthService, OrganizationService, RequestMeta

router = APIRouter(prefix="/organizations", tags=["organizations"])

_ALLOWED_LOGO_TYPES = {"image/png", "image/jpeg", "image/webp", "image/svg+xml"}
_MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2 MB


@router.post("", response_model=MeResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: CreateOrganizationRequest,
    meta: RequestMeta = Depends(get_request_meta),
    ctx: AuthContext = Depends(get_current_context),
    org_service: OrganizationService = Depends(get_organization_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> MeResponse:
    """Create the caller's company and assign them as Owner (one per user)."""
    _org, membership = await org_service.create_for_user(
        ctx.user, name=payload.name, industry=payload.industry
    )
    _ = meta
    return await auth_service.build_me(ctx.user, membership)


@router.get("/current", response_model=OrganizationResponse)
async def current_organization(
    ctx: AuthContext = Depends(require_membership),
    org_service: OrganizationService = Depends(get_organization_service),
) -> OrganizationResponse:
    """Return the caller's full organization profile (settings)."""
    org = await org_service.get(ctx.membership.organization_id)  # type: ignore[union-attr]
    if org is None:
        raise NotFoundError("Organization not found")
    return OrganizationResponse.model_validate(org)


@router.patch("/current", response_model=OrganizationResponse)
async def update_organization(
    payload: UpdateOrganizationRequest,
    ctx: AuthContext = Depends(require_membership),
    org_service: OrganizationService = Depends(get_organization_service),
) -> OrganizationResponse:
    """Update editable organization settings."""
    org = await org_service.get(ctx.membership.organization_id)  # type: ignore[union-attr]
    if org is None:
        raise NotFoundError("Organization not found")
    updated = await org_service.update_settings(org, payload)
    return OrganizationResponse.model_validate(updated)


@router.post("/current/logo", response_model=OrganizationResponse)
async def upload_logo(
    file: UploadFile = File(...),
    ctx: AuthContext = Depends(require_membership),
    org_service: OrganizationService = Depends(get_organization_service),
    storage: ObjectStorage = Depends(get_storage),
) -> OrganizationResponse:
    """Upload an organization logo to object storage and store its public URL."""
    if file.content_type not in _ALLOWED_LOGO_TYPES:
        raise ValidationError("Unsupported image type. Use PNG, JPEG, WEBP, or SVG.")

    contents = await file.read()
    if len(contents) > _MAX_LOGO_BYTES:
        raise ValidationError("Logo must be 2 MB or smaller.")

    org_id = ctx.membership.organization_id  # type: ignore[union-attr]
    extension = (file.filename or "logo").rsplit(".", 1)[-1].lower()
    key = f"logos/{org_id}/{uuid.uuid4()}.{extension}"

    try:
        url = storage.upload_public(
            io.BytesIO(contents), key=key, content_type=file.content_type
        )
    except StorageError as exc:
        raise ValidationError(f"Could not store the logo: {exc}") from exc

    org = await org_service.get(org_id)
    if org is None:
        raise NotFoundError("Organization not found")
    updated = await org_service.set_logo(org, url)
    return OrganizationResponse.model_validate(updated)
