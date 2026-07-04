"""Email verification + password reset token data access."""

from __future__ import annotations

from sqlalchemy import select

from app.models.password_reset_token import PasswordResetToken
from app.models.verification_token import EmailVerificationToken
from app.repositories.base import BaseRepository


class EmailVerificationRepository(BaseRepository[EmailVerificationToken]):
    model = EmailVerificationToken

    async def get_by_hash(self, token_hash: str) -> EmailVerificationToken | None:
        result = await self.session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash
            )
        )
        return result.scalar_one_or_none()


class PasswordResetRepository(BaseRepository[PasswordResetToken]):
    model = PasswordResetToken

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        result = await self.session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()
