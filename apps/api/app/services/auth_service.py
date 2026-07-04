"""Authentication service: registration, verification, login, password reset.

Orchestrates repositories, the token service, email, and audit logging. All
business rules for V1 auth live here (email + password, one org per user,
hard email-verification gate).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.exceptions import (
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.core.security.password import hash_password, verify_password
from app.core.security.tokens import generate_token_pair, hash_token
from app.models.membership import Membership
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.models.verification_token import EmailVerificationToken
from app.repositories.membership_repository import MembershipRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.repositories.verification_repository import (
    EmailVerificationRepository,
    PasswordResetRepository,
)
from app.schemas.auth import AuthResult
from app.schemas.organization import OrganizationResponse
from app.schemas.token import TokenResponse
from app.schemas.user import MeResponse, UserResponse
from app.services.audit_service import AuditService
from app.services.email import EmailMessage, EmailSender
from app.services.token_service import TokenService


class RequestMeta:
    """Lightweight carrier for client metadata used in audit + tokens."""

    def __init__(self, ip_address: str | None = None, user_agent: str | None = None) -> None:
        self.ip_address = ip_address
        self.user_agent = user_agent


class AuthService:
    def __init__(
        self,
        *,
        user_repo: UserRepository,
        membership_repo: MembershipRepository,
        organization_repo: OrganizationRepository,
        refresh_repo: RefreshTokenRepository,
        email_verification_repo: EmailVerificationRepository,
        password_reset_repo: PasswordResetRepository,
        token_service: TokenService,
        audit_service: AuditService,
        email_sender: EmailSender,
    ) -> None:
        self._users = user_repo
        self._memberships = membership_repo
        self._orgs = organization_repo
        self._refresh = refresh_repo
        self._email_verifications = email_verification_repo
        self._password_resets = password_reset_repo
        self._tokens = token_service
        self._audit = audit_service
        self._email = email_sender
        self._settings = get_settings()

    # ----- registration & verification -------------------------------------

    async def register(
        self, *, full_name: str, email: str, password: str, meta: RequestMeta
    ) -> None:
        email = email.strip().lower()
        if await self._users.email_exists(email):
            raise EmailAlreadyExistsError("An account with this email already exists")

        user = await self._users.add(
            User(
                email=email,
                full_name=full_name.strip(),
                hashed_password=hash_password(password),
                is_email_verified=False,
            )
        )
        await self._send_verification(user)
        await self._audit.record(
            action="user.registered",
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=meta.ip_address,
            user_agent=meta.user_agent,
        )

    async def _send_verification(self, user: User) -> None:
        raw, token_hash = generate_token_pair()
        expires = datetime.now(UTC) + timedelta(
            hours=self._settings.email_verification_expire_hours
        )
        await self._email_verifications.add(
            EmailVerificationToken(user_id=user.id, token_hash=token_hash, expires_at=expires)
        )
        link = f"{self._settings.frontend_url}/verify-email?token={raw}"
        await self._email.send(
            EmailMessage(
                to=user.email,
                subject="Verify your email — VisionOps AI",
                body=(
                    f"Hi {user.full_name},\n\n"
                    f"Confirm your email to activate your account:\n{link}\n\n"
                    f"This link expires in {self._settings.email_verification_expire_hours} hours."
                ),
            )
        )

    async def resend_verification(self, *, email: str) -> None:
        """Resend a verification email. Silent on unknown/verified accounts to
        avoid user enumeration."""
        user = await self._users.get_by_email(email)
        if user and not user.is_email_verified:
            await self._send_verification(user)

    async def verify_email(self, *, token: str, meta: RequestMeta) -> AuthResult:
        record = await self._email_verifications.get_by_hash(hash_token(token))
        now = datetime.now(UTC)
        if record is None or record.used_at is not None or record.expires_at <= now:
            raise InvalidTokenError("Verification link is invalid or has expired")

        user = await self._users.get(record.user_id)
        if user is None:
            raise InvalidTokenError("Verification link is invalid or has expired")

        record.used_at = now
        if not user.is_email_verified:
            user.is_email_verified = True
            user.email_verified_at = now

        await self._audit.record(
            action="user.email_verified",
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=meta.ip_address,
            user_agent=meta.user_agent,
        )
        # Auto-login on successful verification.
        return await self._build_auth_result(user, meta)

    # ----- login / logout --------------------------------------------------

    async def login(self, *, email: str, password: str, meta: RequestMeta) -> AuthResult:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect email or password")
        if not user.is_active:
            raise InvalidCredentialsError("Incorrect email or password")
        if not user.is_email_verified:
            raise EmailNotVerifiedError("Please verify your email before logging in")

        await self._audit.record(
            action="user.login",
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=meta.ip_address,
            user_agent=meta.user_agent,
        )
        return await self._build_auth_result(user, meta)

    async def logout(self, *, refresh_token: str) -> None:
        await self._tokens.revoke(refresh_token)

    # ----- password reset --------------------------------------------------

    async def forgot_password(self, *, email: str) -> None:
        """Always succeeds outwardly (no user enumeration)."""
        user = await self._users.get_by_email(email)
        if user is None:
            return
        raw, token_hash = generate_token_pair()
        expires = datetime.now(UTC) + timedelta(hours=self._settings.password_reset_expire_hours)
        await self._password_resets.add(
            PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires)
        )
        link = f"{self._settings.frontend_url}/reset-password?token={raw}"
        await self._email.send(
            EmailMessage(
                to=user.email,
                subject="Reset your password — VisionOps AI",
                body=f"Reset your password:\n{link}\n\nIf you didn't request this, ignore it.",
            )
        )

    async def reset_password(self, *, token: str, password: str, meta: RequestMeta) -> None:
        record = await self._password_resets.get_by_hash(hash_token(token))
        now = datetime.now(UTC)
        if record is None or record.used_at is not None or record.expires_at <= now:
            raise InvalidTokenError("Reset link is invalid or has expired")
        user = await self._users.get(record.user_id)
        if user is None:
            raise InvalidTokenError("Reset link is invalid or has expired")

        user.hashed_password = hash_password(password)
        record.used_at = now
        # Invalidate all active sessions on password change.
        await self._refresh.revoke_family_for_user(user.id)
        await self._audit.record(
            action="user.password_reset",
            actor_user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=meta.ip_address,
            user_agent=meta.user_agent,
        )

    # ----- helpers ---------------------------------------------------------

    async def load_user_membership(
        self, user_id: uuid.UUID
    ) -> tuple[User | None, Membership | None]:
        user = await self._users.get(user_id)
        if user is None:
            return None, None
        membership = await self._memberships.get_for_user(user_id)
        return user, membership

    async def _build_auth_result(self, user: User, meta: RequestMeta) -> AuthResult:
        membership = await self._memberships.get_for_user(user.id)
        tokens: TokenResponse = await self._tokens.issue_pair(
            user,
            membership,
            user_agent=meta.user_agent,
            ip_address=meta.ip_address,
        )
        return AuthResult(tokens=tokens, user=await self.build_me(user, membership))

    async def build_me(self, user: User, membership: Membership | None) -> MeResponse:
        organization = None
        role = None
        if membership is not None:
            org = await self._orgs.get(membership.organization_id)
            organization = OrganizationResponse.model_validate(org) if org else None
            role = membership.role
        return MeResponse(
            user=UserResponse.model_validate(user),
            organization=organization,
            role=role,
            needs_onboarding=membership is None,
        )
