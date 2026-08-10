"""Rename weekly_leave_days_per_month to weekly_leave_days_per_week

Revision ID: 0006_employer_weekly_leave_rename
Revises: 0005_employer_payment_frequency
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_weekly_leave_rename"
down_revision = "0005_employer_payment_frequency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "employers",
        "weekly_leave_days_per_month",
        new_column_name="weekly_leave_days_per_week",
    )


def downgrade() -> None:
    op.alter_column(
        "employers",
        "weekly_leave_days_per_week",
        new_column_name="weekly_leave_days_per_month",
    )
