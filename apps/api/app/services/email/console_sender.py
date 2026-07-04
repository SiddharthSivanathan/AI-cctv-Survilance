"""Development email sender that logs messages instead of delivering them.

This is a real adapter (not a mock): it implements the EmailSender port and
is selected in non-production environments. Verification/reset links are
printed to the structured log so developers can complete flows locally.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.services.email.sender import EmailMessage, EmailSender

logger = get_logger("email")


class ConsoleEmailSender(EmailSender):
    async def send(self, message: EmailMessage) -> None:
        logger.info(
            "email_sent",
            to=message.to,
            subject=message.subject,
            body=message.body,
        )
