"""Database type helpers for cross-dialect compatibility."""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB as PostgresJSONB
from sqlalchemy.types import TypeDecorator


class JSONB(TypeDecorator):
    """A Postgres JSONB type with a SQLite-compatible JSON fallback."""

    impl = PostgresJSONB
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgresJSONB())
        return dialect.type_descriptor(JSON())
