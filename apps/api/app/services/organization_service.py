"""Organization service: company creation + owner assignment."""

from __future__ import annotations

import re
import secrets

from app.core.exceptions import OrganizationExistsError
from app.domain.roles import Role
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.repositories.membership_repository import MembershipRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import UpdateOrganizationRequest


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return base or "org"


class OrganizationService:
    def __init__(
        self,
        org_repo: OrganizationRepository,
        membership_repo: MembershipRepository,
    ) -> None:
        self._orgs = org_repo
        self._memberships = membership_repo

    async def get(self, organization_id) -> Organization | None:
        return await self._orgs.get(organization_id)

    async def update_settings(
        self, organization: Organization, data: UpdateOrganizationRequest
    ) -> Organization:
        """Apply a partial update to an organization's editable settings."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(organization, field, value)
        await self._orgs.session.flush()
        return organization

    async def set_logo(self, organization: Organization, logo_url: str) -> Organization:
        organization.logo_url = logo_url
        await self._orgs.session.flush()
        return organization

    async def create_for_user(
        self, user: User, *, name: str, industry: str | None = None
    ) -> tuple[Organization, Membership]:
        """Create an organization and assign the user as Owner.

        Enforces one organization per user in V1: raises if the user already
        belongs to an organization.
        """
        existing = await self._memberships.get_for_user(user.id)
        if existing is not None:
            raise OrganizationExistsError("User already belongs to an organization")

        slug = await self._unique_slug(_slugify(name))
        organization = await self._orgs.add(
            Organization(name=name.strip(), slug=slug, industry=industry)
        )
        membership = await self._memberships.add(
            Membership(
                organization_id=organization.id,
                user_id=user.id,
                role=Role.OWNER.value,
            )
        )
        return organization, membership

    async def _unique_slug(self, base: str) -> str:
        slug = base
        while await self._orgs.slug_exists(slug):
            slug = f"{base}-{secrets.token_hex(3)}"
        return slug
