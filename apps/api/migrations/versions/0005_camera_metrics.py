"""camera metrics (aggregated)

Per-minute aggregated occupancy/footfall/queue metrics powering the dashboard.
Tenant-scoped, RLS-protected.

Revision ID: 0005_camera_metrics
Revises: 0004_rules_events
Create Date: 2026-07-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_camera_metrics"
down_revision: str | None = "0004_rules_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ORG = "organization_id = NULLIF(current_setting('app.current_org', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        "camera_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=True),
        sa.Column("camera_id", sa.Uuid(), nullable=False),
        sa.Column("bucket", sa.DateTime(timezone=True), nullable=False),
        sa.Column("occupancy_avg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("occupancy_peak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("footfall", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("queue_avg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("queue_peak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("camera_id", "bucket", name="uq_camera_metric_bucket"),
    )
    op.create_index("ix_camera_metrics_organization_id", "camera_metrics", ["organization_id"])
    op.create_index("ix_camera_metrics_camera_id", "camera_metrics", ["camera_id"])
    op.create_index("ix_camera_metrics_bucket", "camera_metrics", ["bucket"])
    op.create_index("ix_camera_metrics_org_bucket", "camera_metrics", ["organization_id", "bucket"])

    op.execute("ALTER TABLE camera_metrics ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE camera_metrics FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY camera_metrics_tenant_isolation ON camera_metrics "
        f"USING ({_ORG}) WITH CHECK ({_ORG})"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS camera_metrics_tenant_isolation ON camera_metrics")
    op.drop_table("camera_metrics")
