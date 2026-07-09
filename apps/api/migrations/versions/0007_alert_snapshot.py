"""alert snapshot url

Adds alerts.snapshot_url — the MinIO URL of the frame captured when a rule
fired (populated by the Event Service from the AI engine's snapshot).

Revision ID: 0007_alert_snapshot
Revises: 0006_notifications_reports
Create Date: 2026-07-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_alert_snapshot"
down_revision: str | None = "0006_notifications_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("snapshot_url", sa.String(length=1024), nullable=True))


def downgrade() -> None:
    op.drop_column("alerts", "snapshot_url")
