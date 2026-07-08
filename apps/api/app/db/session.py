"""Async database engine and session management.

Provides a FastAPI dependency (`get_db`) yielding an AsyncSession. The
per-request tenant (RLS) context is set here starting in Phase 3.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_settings = get_settings()

engine: AsyncEngine = create_async_engine(
    _settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session.

    Commits on successful request completion; rolls back on any exception.
    This gives every request a single, well-defined transaction boundary.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def set_org_context(session: AsyncSession, organization_id: str | None) -> None:
    """Set the transaction-local tenant context used by Row-Level Security.

    Uses ``set_config(..., is_local => true)`` which is equivalent to
    ``SET LOCAL``: the value is scoped to the current transaction. RLS policies
    read it via ``current_setting('app.current_org', true)``.

    This is a no-op on non-Postgres backends such as SQLite used for local dev.
    """
    engine = session.get_bind()
    if engine is None or engine.dialect.name != "postgresql":
        return

    value = str(organization_id) if organization_id is not None else ""
    await session.execute(
        text("SELECT set_config('app.current_org', :org, true)"),
        {"org": value},
    )
