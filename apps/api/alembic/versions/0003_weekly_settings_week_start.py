"""Add week_start to weekly_settings

Revision ID: 0003_weekly_settings_week_start
Revises: 0002_auth_and_employers
Create Date: 2026-08-07
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_weekly_settings_week_start"
down_revision = "0002_auth_and_employers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "weekly_settings",
        sa.Column("week_start", sa.Date, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("weekly_settings", "week_start")
