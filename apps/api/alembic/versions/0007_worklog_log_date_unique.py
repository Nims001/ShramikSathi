"""Enforce one work log per employer per day

Revision ID: 0007_worklog_log_date_unique
Revises: 0006_weekly_leave_rename
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op

revision = "0007_worklog_log_date_unique"
down_revision = "0006_weekly_leave_rename"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop any pre-existing duplicates, keeping the earliest-created log for
    # each (employer_id, log_date) pair (id is a deterministic tiebreaker).
    op.execute(
        """
        DELETE FROM work_logs w
        USING work_logs keep
        WHERE keep.employer_id = w.employer_id
          AND keep.log_date = w.log_date
          AND (keep.created_at, keep.id) < (w.created_at, w.id)
        """
    )
    op.create_unique_constraint(
        "uq_work_logs_employer_date",
        "work_logs",
        ["employer_id", "log_date"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_work_logs_employer_date", "work_logs", type_="unique")
