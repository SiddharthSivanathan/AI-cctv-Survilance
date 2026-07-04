"""Store service: CRUD for physical locations within an organization."""

from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.models.store import Store
from app.repositories.store_repository import StoreRepository
from app.schemas.store import CreateStoreRequest, UpdateStoreRequest
from app.services.audit_service import AuditService


class StoreService:
    def __init__(self, store_repo: StoreRepository, audit_service: AuditService) -> None:
        self._stores = store_repo
        self._audit = audit_service

    async def list(self, organization_id: uuid.UUID) -> list[Store]:
        return await self._stores.list_for_org(organization_id)

    async def get(self, store_id: uuid.UUID, organization_id: uuid.UUID) -> Store:
        store = await self._stores.get_for_org(store_id, organization_id)
        if store is None:
            raise NotFoundError("Store not found")
        return store

    async def create(
        self,
        *,
        organization_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        data: CreateStoreRequest,
    ) -> Store:
        store = await self._stores.add(
            Store(
                organization_id=organization_id,
                name=data.name.strip(),
                code=data.code,
                address=data.address,
                city=data.city,
                country=data.country,
                timezone=data.timezone,
            )
        )
        await self._audit.record(
            action="store.created",
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            resource_type="store",
            resource_id=str(store.id),
            metadata={"name": store.name},
        )
        return store

    async def update(
        self,
        *,
        store_id: uuid.UUID,
        organization_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        data: UpdateStoreRequest,
    ) -> Store:
        store = await self.get(store_id, organization_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(store, field, value)
        await self._stores.session.flush()
        await self._audit.record(
            action="store.updated",
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            resource_type="store",
            resource_id=str(store.id),
        )
        return store

    async def delete(
        self,
        *,
        store_id: uuid.UUID,
        organization_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> None:
        store = await self.get(store_id, organization_id)
        await self._stores.delete(store)
        await self._audit.record(
            action="store.deleted",
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            resource_type="store",
            resource_id=str(store_id),
        )
