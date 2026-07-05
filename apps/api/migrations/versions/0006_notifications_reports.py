"""notifications, reports, org notification settings

Adds in-app notifications + generated reports (both RLS) and two notification
preference columns on organizations.

Revision ID: 0006_notifications_reports
Revises: 0005_camera_metrics
Create Date: 2026-07-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_notifications_reports"
down_revision: str | None = "0005_camera_metrics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ORG = "organization_id = NULLIF(current_setting('app.current_org', true), '')::uuid"


def _enable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {table}_tenant_isolation ON {table} "
        f"USING ({_ORG}) WITH CHECK ({_ORG})"
    )


def upgrade() -> None:
    # Organization notification preferences (single source of truth).
    op.add_column(
        "organizations",
        sa.Column("notify_critical_only", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "organizations",
        sa.Column("daily_summary_email", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # In-app notifications.
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.String(length=1024), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("camera_id", sa.Uuid(), nullable=True),
        sa.Column("store_id", sa.Uuid(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_organization_id", "notifications", ["organization_id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_event_type", "notifications", ["event_type"])
    op.create_index("ix_notifications_camera_id", "notifications", ["camera_id"])
    op.create_index("ix_notifications_org_created", "notifications", ["organization_id", "created_at"])
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "is_read"])
    _enable_rls("notifications")

    # Generated reports.
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("store_id", sa.Uuid(), nullable=True),
        sa.Column("report_type", sa.String(length=16), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ready"),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_organization_id", "reports", ["organization_id"])
    op.create_index("ix_reports_store_id", "reports", ["store_id"])
    op.create_index("ix_reports_report_type", "reports", ["report_type"])
    op.create_index("ix_reports_org_created", "reports", ["organization_id", "created_at"])
    _enable_rls("reports")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS reports_tenant_isolation ON reports")
    op.drop_table("reports")
    op.execute("DROP POLICY IF EXISTS notifications_tenant_isolation ON notifications")
    op.drop_table("notifications")
    op.drop_column("organizations", "daily_summary_email")
    op.drop_column("organizations", "notify_critical_only")
