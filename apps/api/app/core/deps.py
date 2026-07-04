"""Dependency-injection providers and auth dependencies.

Wires repositories → services per request, and provides the authentication /
authorization dependencies used by routers.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError, PermissionDeniedError
from app.core.security import jwt as jwt_utils
from app.core.security.jwt import TokenError
from app.db.session import get_db, set_org_context
from app.domain.roles import ROLE_RANK
from app.models.membership import Membership
from app.models.user import User
from app.repositories import (
    AuditRepository,
    EmailVerificationRepository,
    MembershipRepository,
    OrganizationRepository,
    PasswordResetRepository,
    RefreshTokenRepository,
    UserRepository,
)
from app.services import AuditService, AuthService, OrganizationService, RequestMeta, TokenService
from app.services.email import ConsoleEmailSender
from app.services.email.sender import EmailSender

bearer_scheme = HTTPBearer(auto_error=False)


# ----- infrastructure providers -------------------------------------------


def get_email_sender() -> EmailSender:
    """Return the active email sender. SMTP/SES swaps in at Phase 10."""
    return ConsoleEmailSender()


def get_request_meta(request: Request) -> RequestMeta:
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (
        request.client.host if request.client else None
    )
    return RequestMeta(ip_address=ip, user_agent=request.headers.get("user-agent"))


# ----- service factories ---------------------------------------------------


def get_token_service(db: AsyncSession = Depends(get_db)) -> TokenService:
    return TokenService(RefreshTokenRepository(db))


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> AuthService:
    return AuthService(
        user_repo=UserRepository(db),
        membership_repo=MembershipRepository(db),
        organization_repo=OrganizationRepository(db),
        refresh_repo=RefreshTokenRepository(db),
        email_verification_repo=EmailVerificationRepository(db),
        password_reset_repo=PasswordResetRepository(db),
        token_service=TokenService(RefreshTokenRepository(db)),
        audit_service=AuditService(AuditRepository(db)),
        email_sender=email_sender,
    )


def get_organization_service(db: AsyncSession = Depends(get_db)) -> OrganizationService:
    return OrganizationService(OrganizationRepository(db), MembershipRepository(db))


# ----- auth context --------------------------------------------------------


@dataclass
class AuthContext:
    user: User
    membership: Membership | None
    organization_id: str | None
    role: str | None


async def get_current_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """Validate the bearer token, load the user, and set tenant RLS context."""
    if credentials is None or not credentials.credentials:
        raise InvalidTokenError("Missing authentication credentials")

    try:
        payload = jwt_utils.decode_access_token(credentials.credentials)
        user_id = uuid.UUID(str(payload["sub"]))
    except (TokenError, KeyError, ValueError) as exc:
        raise InvalidTokenError("Invalid or expired token") from exc

    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)
    if user is None or not user.is_active:
        raise InvalidTokenError("User not found or inactive")

    membership = await MembershipRepository(db).get_for_user(user.id)
    org_id = str(membership.organization_id) if membership else None

    # Establish tenant context for RLS on any tenant-scoped query in this request.
    await set_org_context(db, org_id)

    return AuthContext(
        user=user,
        membership=membership,
        organization_id=org_id,
        role=membership.role if membership else None,
    )


async def get_current_user(ctx: AuthContext = Depends(get_current_context)) -> User:
    return ctx.user


def require_role(minimum: str):
    """Dependency factory enforcing a minimum role rank in the active org."""

    async def _dependency(ctx: AuthContext = Depends(get_current_context)) -> AuthContext:
        if ctx.role is None or ROLE_RANK.get(ctx.role, 0) < ROLE_RANK.get(minimum, 0):
            raise PermissionDeniedError("Insufficient role for this action")
        return ctx

    return _dependency
