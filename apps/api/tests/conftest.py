"""Shared test fixtures.

Unit tests run with no external dependencies. Integration tests request the
``db_ready`` fixture, which skips the test if a Postgres database is not
reachable (so the suite stays green locally without infra; CI provides one).
"""

from __future__ import annotations

import re

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app import models  # noqa: F401  (register metadata)
from app.core.deps import get_email_sender
from app.db.base import Base
from app.db.session import engine
from app.main import app
from app.services.email.sender import EmailMessage, EmailSender

_TABLES = (
    "audit_logs",
    "alerts",
    "camera_events",
    "rules",
    "zones",
    "cameras",
    "stores",
    "password_reset_tokens",
    "email_verification_tokens",
    "refresh_tokens",
    "memberships",
    "users",
    "organizations",
)


def _rls_sql(table: str, *, with_check: str) -> list[str]:
    policy = f"{table}_tenant_isolation"
    using = "organization_id = NULLIF(current_setting('app.current_org', true), '')::uuid"
    return [
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY",
        f"DROP POLICY IF EXISTS {policy} ON {table}",
        f"CREATE POLICY {policy} ON {table} USING ({using}) WITH CHECK ({with_check})",
    ]

_db_ready: bool | None = None


async def _ensure_schema() -> bool:
    """Create the schema + RLS once. Return False if the DB is unreachable."""
    global _db_ready
    if _db_ready is not None:
        return _db_ready
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY"))
            await conn.execute(text("ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY"))
            await conn.execute(
                text("DROP POLICY IF EXISTS audit_logs_tenant_isolation ON audit_logs")
            )
            await conn.execute(
                text(
                    "CREATE POLICY audit_logs_tenant_isolation ON audit_logs "
                    "USING (organization_id = "
                    "NULLIF(current_setting('app.current_org', true), '')::uuid) "
                    "WITH CHECK (true)"
                )
            )
            # RLS for org-scoped business tables (matches migrations 0002-0004).
            org_check = "organization_id = NULLIF(current_setting('app.current_org', true), '')::uuid"
            for table in ("stores", "cameras", "zones", "rules", "camera_events", "alerts"):
                for stmt in _rls_sql(table, with_check=org_check):
                    await conn.execute(text(stmt))
        _db_ready = True
    except Exception:  # noqa: BLE001 - any connection/setup failure => skip integration
        _db_ready = False
    return _db_ready


@pytest_asyncio.fixture
async def db_ready():
    """Skip the test unless a database is reachable; truncate before each test."""
    if not await _ensure_schema():
        pytest.skip("Database not available")
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE"))
    yield


class RecordingEmailSender(EmailSender):
    """Captures outgoing emails so tests can extract verification/reset links."""

    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> None:
        self.messages.append(message)

    def last_token(self) -> str:
        match = re.search(r"token=([^\s]+)", self.messages[-1].body)
        assert match, "No token found in email body"
        return match.group(1)


@pytest.fixture
def email_recorder():
    recorder = RecordingEmailSender()
    app.dependency_overrides[get_email_sender] = lambda: recorder
    yield recorder
    app.dependency_overrides.pop(get_email_sender, None)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
