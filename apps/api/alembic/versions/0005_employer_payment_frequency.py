"""Add payment_frequency to employers; drop inferable pay fields

Revision ID: 0005_employer_payment_frequency
Revises: 0004_employer_other_clauses
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_employer_payment_frequency"
down_revision = "0004_employer_other_clauses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "employers",
        sa.Column("payment_frequency", sa.String(length=20), nullable=True),
    )
    op.drop_column("employers", "monthly_wage_received")
    op.drop_column("employers", "wage_payment_days_after_month_end")


def downgrade() -> None:
    op.add_column(
        "employers",
        sa.Column("wage_payment_days_after_month_end", sa.Float, nullable=True),
    )
    op.add_column(
        "employers",
        sa.Column("monthly_wage_received", sa.Float, nullable=True),
    )
    op.drop_column("employers", "payment_frequency")
