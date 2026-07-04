"""Token service: issues access tokens and manages refresh-token rotation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.exceptions import InvalidTokenError
from app.core.security import jwt as jwt_utils
from app.core.security.tokens import generate_token_pair, hash_token
from app.models.membership import Membership
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.token import TokenResponse


class TokenService:
    def __init__(self, refresh_repo: RefreshTokenRepository) -> None:
        self._refresh = refresh_repo
        self._settings = get_settings()

    def _access_token(self, user: User, membership: Membership | None) -> str:
        return jwt_utils.create_access_token(
            str(user.id),
            organization_id=str(membership.organization_id) if membership else None,
            role=membership.role if membership else None,
        )

    async def issue_pair(
        self,
        user: User,
        membership: Membership | None,
        *,
        family_id: uuid.UUID | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Issue a new access + refresh token pair (new family unless given)."""
        raw_refresh, refresh_hash = generate_token_pair()
        expires_at = datetime.now(UTC) + timedelta(days=self._settings.refresh_token_expire_days)
        record = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            family_id=family_id or uuid.uuid4(),
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        await self._refresh.add(record)

        return TokenResponse(
            access_token=self._access_token(user, membership),
            refresh_token=raw_refresh,
            expires_in=self._settings.access_token_expire_minutes * 60,
        )

    async def rotate(
        self,
        raw_refresh_token: str,
        *,
        load_user_membership,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Rotate a refresh token.

        Detects reuse: if a revoked/rotated token is presented, the entire
        family is revoked and the request is rejected.
        ``load_user_membership`` is an async callable (user_id) ->
        (User, Membership | None).
        """
        token_hash = hash_token(raw_refresh_token)
        record = await self._refresh.get_by_hash(token_hash)

        if record is None:
            raise InvalidTokenError("Invalid refresh token")

        now = datetime.now(UTC)
        if record.revoked_at is not None:
            # Reuse of an already-rotated token → likely theft. Burn the family
            # and COMMIT the revocation before raising, so the request-level
            # rollback cannot undo the security response.
            await self._refresh.revoke_family(record.family_id)
            await self._refresh.session.commit()
            raise InvalidTokenError("Refresh token reuse detected")

        if record.expires_at <= now:
            raise InvalidTokenError("Refresh token expired")

        user, membership = await load_user_membership(record.user_id)
        if user is None or not user.is_active:
            raise InvalidTokenError("User is inactive")

        # Issue a replacement in the same family, then revoke the old one.
        new_pair = await self.issue_pair(
            user,
            membership,
            family_id=record.family_id,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        new_record = await self._refresh.get_by_hash(hash_token(new_pair.refresh_token))
        await self._refresh.revoke(record, replaced_by_id=new_record.id if new_record else None)
        return new_pair

    async def revoke(self, raw_refresh_token: str) -> None:
        """Revoke a single refresh token (logout)."""
        record = await self._refresh.get_by_hash(hash_token(raw_refresh_token))
        if record and record.revoked_at is None:
            await self._refresh.revoke(record)
