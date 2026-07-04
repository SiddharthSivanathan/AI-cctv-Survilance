"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.deps import (
    AuthContext,
    get_auth_service,
    get_current_context,
    get_request_meta,
    get_token_service,
)
from app.core.rate_limit import rate_limit
from app.schemas.auth import (
    AuthResult,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.schemas.token import TokenResponse
from app.schemas.user import MeResponse
from app.services import AuthService, RequestMeta, TokenService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("register", limit=5, window_seconds=60))],
)
async def register(
    payload: RegisterRequest,
    meta: RequestMeta = Depends(get_request_meta),
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Register a new user and send a verification email (24h expiry)."""
    await service.register(
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        meta=meta,
    )
    return MessageResponse(
        message="Account created. Check your email to verify your account."
    )


@router.post("/verify-email", response_model=AuthResult)
async def verify_email(
    payload: VerifyEmailRequest,
    meta: RequestMeta = Depends(get_request_meta),
    service: AuthService = Depends(get_auth_service),
) -> AuthResult:
    """Verify an email and auto-login (returns tokens + user context)."""
    return await service.verify_email(token=payload.token, meta=meta)


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    payload: ResendVerificationRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Resend the verification email (silent if unknown/verified)."""
    await service.resend_verification(email=payload.email)
    return MessageResponse(message="If the account exists, a verification email was sent.")


@router.post(
    "/login",
    response_model=AuthResult,
    dependencies=[Depends(rate_limit("login", limit=10, window_seconds=60))],
)
async def login(
    payload: LoginRequest,
    meta: RequestMeta = Depends(get_request_meta),
    service: AuthService = Depends(get_auth_service),
) -> AuthResult:
    """Authenticate with email + password. Requires a verified email."""
    return await service.login(email=payload.email, password=payload.password, meta=meta)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    meta: RequestMeta = Depends(get_request_meta),
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service),
) -> TokenResponse:
    """Rotate a refresh token (with reuse detection)."""
    return await token_service.rotate(
        payload.refresh_token,
        load_user_membership=auth_service.load_user_membership,
        user_agent=meta.user_agent,
        ip_address=meta.ip_address,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Revoke the presented refresh token."""
    await service.logout(refresh_token=payload.refresh_token)
    return MessageResponse(message="Logged out.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit("forgot_password", limit=5, window_seconds=60))],
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Send a password reset link (silent if the account doesn't exist)."""
    await service.forgot_password(email=payload.email)
    return MessageResponse(message="If the account exists, a reset email was sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    meta: RequestMeta = Depends(get_request_meta),
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Set a new password using a valid reset token."""
    await service.reset_password(token=payload.token, password=payload.password, meta=meta)
    return MessageResponse(message="Password updated. You can now log in.")


@router.get("/me", response_model=MeResponse)
async def me(
    ctx: AuthContext = Depends(get_current_context),
    service: AuthService = Depends(get_auth_service),
) -> MeResponse:
    """Return the authenticated user's profile, organization, and onboarding state."""
    return await service.build_me(ctx.user, ctx.membership)
