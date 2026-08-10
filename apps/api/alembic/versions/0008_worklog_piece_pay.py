"""Add per-piece pay fields to work logs

Revision ID: 0008_worklog_piece_pay
Revises: 0007_worklog_log_date_unique
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op

revision = "0008_worklog_piece_pay"
down_revision = "0007_worklog_log_date_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("work_logs", sa.Column("piece_count", sa.Integer(), nullable=True))
    op.add_column("work_logs", sa.Column("piece_rate", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("work_logs", "piece_rate")
    op.drop_column("work_logs", "piece_count")
