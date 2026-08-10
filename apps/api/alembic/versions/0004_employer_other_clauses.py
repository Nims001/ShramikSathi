"""Add other_clauses to employers

Revision ID: 0004_employer_other_clauses
Revises: 0003_weekly_settings_week_start
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_employer_other_clauses"
down_revision = "0003_weekly_settings_week_start"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "employers",
        sa.Column("other_clauses", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("employers", "other_clauses")
