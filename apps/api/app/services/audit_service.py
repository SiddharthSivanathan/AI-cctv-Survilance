"""Audit logging service."""

from __future__ import annotations

import uuid
from typing import Any

from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, audit_repo: AuditRepository) -> None:
        self._audit = audit_repo

    async def record(
        self,
        *,
        action: str,
        organization_id: uuid.UUID | None = None,
        actor_user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append an immutable audit record."""
        await self._audit.add(
            AuditLog(
                action=action,
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                event_metadata=metadata,
            )
        )
