"""Email delivery task.

The worker is a dumb SMTP sender: the API enqueues fully-formed email jobs
(to/subject/body). If SMTP is not configured, the email is logged instead —
so development works without a mail server.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

import structlog

from src.celery_app import celery_app
from src.config import get_settings

logger = structlog.get_logger("notifications")


@celery_app.task(name="visionops.notifications.send_email", max_retries=3)
def send_email(to: str, subject: str, body: str) -> bool:
    settings = get_settings()
    if not settings.smtp_host:
        logger.info("email_logged", to=to, subject=subject, body=body)
        return True

    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password or "")
            smtp.send_message(message)
        logger.info("email_sent", to=to, subject=subject)
        return True
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("email_send_failed", to=to, error=str(exc))
        return False
