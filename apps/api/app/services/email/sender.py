"""Email sender interface (port).

The concrete SMTP/SES implementation is added in Phase 10 (Notifications).
Call sites depend on this abstraction only, so swapping the implementation
requires no changes to services.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str


class EmailSender(ABC):
    """Port for sending transactional email."""

    @abstractmethod
    async def send(self, message: EmailMessage) -> None:  # pragma: no cover - interface
        ...
