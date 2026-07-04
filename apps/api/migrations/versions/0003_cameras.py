"""cameras

Creates the tenant-scoped `cameras` table (with Row-Level Security).

Revision ID: 0003_cameras
Revises: 0002_stores_and_org_settings
Create Date: 2026-07-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_cameras"
down_revision: str | None = "0002_stores_and_org_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cameras",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("camera_type", sa.String(length=32), nullable=False, server_default="ip"),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("rtsp_url", sa.String(length=1024), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("password_encrypted", sa.String(length=1024), nullable=True),
        sa.Column("manufacturer", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("resolution", sa.String(length=32), nullable=True),
        sa.Column("fps", sa.Float(), nullable=True),
        sa.Column("codec", sa.String(length=32), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=1024), nullable=True),
        sa.Column("sample_fps", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=512), nullable=True),
        sa.Column("offline_alerted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cameras_id", "cameras", ["id"])
    op.create_index("ix_cameras_organization_id", "cameras", ["organization_id"])
    op.create_index("ix_cameras_store_id", "cameras", ["store_id"])
    op.create_index("ix_cameras_org_status", "cameras", ["organization_id", "status"])

    op.execute("ALTER TABLE cameras ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE cameras FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY cameras_tenant_isolation ON cameras
        USING (
            organization_id = NULLIF(current_setting('app.current_org', true), '')::uuid
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_org', true), '')::uuid
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS cameras_tenant_isolation ON cameras")
    op.drop_table("cameras")
