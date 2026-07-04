"""Integration test: Postgres Row-Level Security isolates tenant data.

Proves the platform's core isolation guarantee on `audit_logs` — the pattern
every tenant-scoped table (stores, cameras, events) will follow.
"""

import uuid

from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal, set_org_context
from app.models.audit_log import AuditLog


async def test_rls_blocks_cross_tenant_reads(db_ready) -> None:
    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    # Insert audit rows for two different organizations.
    async with AsyncSessionLocal() as session:
        session.add(AuditLog(organization_id=org_a, action="a.event"))
        session.add(AuditLog(organization_id=org_a, action="a.event2"))
        session.add(AuditLog(organization_id=org_b, action="b.event"))
        await session.commit()

    # With org A context, only org A rows are visible.
    async with AsyncSessionLocal() as session:
        await set_org_context(session, str(org_a))
        rows = (await session.execute(select(AuditLog))).scalars().all()
        assert len(rows) == 2
        assert all(r.organization_id == org_a for r in rows)

    # With org B context, only org B rows are visible.
    async with AsyncSessionLocal() as session:
        await set_org_context(session, str(org_b))
        count = await session.scalar(select(func.count()).select_from(AuditLog))
        assert count == 1

    # With no tenant context, RLS hides everything.
    async with AsyncSessionLocal() as session:
        await set_org_context(session, None)
        count = await session.scalar(select(func.count()).select_from(AuditLog))
        assert count == 0
