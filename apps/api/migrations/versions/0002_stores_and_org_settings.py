"""stores + organization settings

Creates the tenant-scoped `stores` table (with Row-Level Security) and extends
`organizations` with the V1 settings fields.

Revision ID: 0002_stores_and_org_settings
Revises: 0001_auth_and_tenancy
Create Date: 2026-07-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_stores_and_org_settings"
down_revision: str | None = "0001_auth_and_tenancy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ----- organization settings fields -----------------------------------
    op.add_column("organizations", sa.Column("logo_url", sa.String(length=1024), nullable=True))
    op.add_column("organizations", sa.Column("contact_email", sa.String(length=320), nullable=True))
    op.add_column("organizations", sa.Column("contact_phone", sa.String(length=64), nullable=True))
    op.add_column("organizations", sa.Column("address", sa.String(length=512), nullable=True))
    op.add_column(
        "organizations",
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
    )
    op.add_column(
        "organizations",
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
    )
    op.add_column(
        "organizations",
        sa.Column(
            "alert_email_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )

    # ----- stores ----------------------------------------------------------
    op.create_table(
        "stores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("address", sa.String(length=512), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("country", sa.String(length=128), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stores_id", "stores", ["id"])
    op.create_index("ix_stores_organization_id", "stores", ["organization_id"])
    op.create_index("ix_stores_org_name", "stores", ["organization_id", "name"])

    # Row-Level Security: reads and writes are scoped to the active tenant.
    op.execute("ALTER TABLE stores ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE stores FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY stores_tenant_isolation ON stores
        USING (
            organization_id = NULLIF(current_setting('app.current_org', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_org', true), '')::uuid
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS stores_tenant_isolation ON stores")
    op.drop_table("stores")
    op.drop_column("organizations", "alert_email_enabled")
    op.drop_column("organizations", "currency")
    op.drop_column("organizations", "timezone")
    op.drop_column("organizations", "address")
    op.drop_column("organizations", "contact_phone")
    op.drop_column("organizations", "contact_email")
    op.drop_column("organizations", "logo_url")
