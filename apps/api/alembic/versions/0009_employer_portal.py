"""Employer portal: user role, share code, employer links

Revision ID: 0009_employer_portal
Revises: 0008_worklog_piece_pay
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op

revision = "0009_employer_portal"
down_revision = "0008_worklog_piece_pay"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=10), nullable=False, server_default="worker"),
    )
    op.add_column(
        "users",
        sa.Column("share_code_hash", sa.String(length=64), nullable=True),
    )
    op.create_table(
        "employer_links",
        sa.Column(
            "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True
        ),
        sa.Column(
            "employer_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "employee_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("note", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "employer_user_id", "employee_user_id", name="uq_employer_links_employer_employee"
        ),
    )
    op.create_index("ix_employer_links_employer_user_id", "employer_links", ["employer_user_id"])
    op.create_index("ix_employer_links_employee_user_id", "employer_links", ["employee_user_id"])


def downgrade() -> None:
    op.drop_index("ix_employer_links_employee_user_id", table_name="employer_links")
    op.drop_index("ix_employer_links_employer_user_id", table_name="employer_links")
    op.drop_table("employer_links")
    op.drop_column("users", "share_code_hash")
    op.drop_column("users", "role")
