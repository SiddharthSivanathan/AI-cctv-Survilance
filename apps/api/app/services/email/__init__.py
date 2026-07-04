"""Email delivery adapters."""

from app.services.email.console_sender import ConsoleEmailSender
from app.services.email.sender import EmailMessage, EmailSender

__all__ = ["ConsoleEmailSender", "EmailMessage", "EmailSender"]
