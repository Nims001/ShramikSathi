"""Initial schema: submissions + violations

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-02
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # §10 employment types (regular / work_based / time_based / casual / part_time)
    employment_type = postgresql.ENUM(
        "regular", "work_based", "time_based", "casual", "part_time",
        name="employment_type", create_type=False,
    )
    employment_type.create(op.get_bind(), checkfirst=True)

    # Severity triage level used across all violation rows.
    severity = postgresql.ENUM(
        "info", "warning", "critical",
        name="severity", create_type=False,
    )
    severity.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("employment_type", employment_type, nullable=False),
        sa.Column("sector", sa.String(80), nullable=True),
        sa.Column("province", sa.String(40), nullable=True),
        sa.Column("gender", sa.String(20), nullable=True),
        sa.Column("hours_per_day", sa.Float, nullable=True),
        sa.Column("hours_per_week", sa.Float, nullable=True),
        sa.Column("worked_over_5h_without_break", sa.Boolean, nullable=True),
        sa.Column("overtime_hours_per_week", sa.Float, nullable=True),
        sa.Column("overtime_rate_paid", sa.Float, nullable=True),
        sa.Column("daily_wage", sa.Float, nullable=True),
        sa.Column("monthly_wage", sa.Float, nullable=True),
        sa.Column("wage_payment_interval_days", sa.Float, nullable=True),
        sa.Column("months_worked", sa.Float, nullable=True),
        sa.Column("years_worked", sa.Float, nullable=True),
        sa.Column("received_annual_increment", sa.Boolean, nullable=True),
        sa.Column("festival_expense_paid", sa.Boolean, nullable=True),
        sa.Column("other_deduction_reason", sa.String(200), nullable=True),
        sa.Column("weekly_leave_taken_per_month", sa.Float, nullable=True),
        sa.Column("sick_leave_denied", sa.Boolean, nullable=True),
        sa.Column("maternity_leave_denied", sa.Boolean, nullable=True),
        sa.Column("paternity_leave_denied", sa.Boolean, nullable=True),
        sa.Column("mourning_leave_denied", sa.Boolean, nullable=True),
        sa.Column("has_written_contract", sa.Boolean, nullable=True),
        sa.Column("pf_deducted", sa.Boolean, nullable=True),
        sa.Column("pf_deposited", sa.Boolean, nullable=True),
        sa.Column("gratuity_deducted", sa.Boolean, nullable=True),
        sa.Column("gratuity_paid_by_employer", sa.Boolean, nullable=True),
        sa.Column("medical_insurance_provided", sa.Boolean, nullable=True),
        sa.Column("accidental_insurance_provided", sa.Boolean, nullable=True),
        sa.Column("termination_occurred", sa.Boolean, nullable=True),
        sa.Column("notice_given_days", sa.Float, nullable=True),
        sa.Column("retrenchment_compensation_months_paid", sa.Float, nullable=True),
        sa.Column("final_settlement_within_15_days", sa.Boolean, nullable=True),
    )

    op.create_table(
        "violations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_id", sa.String(80), nullable=False),
        sa.Column("section_reference", sa.String(40), nullable=False),
        sa.Column("severity", severity, nullable=False),
        sa.Column("plain_explanation_en", sa.Text, nullable=False),
        sa.Column("plain_explanation_ne", sa.Text, nullable=False),
        sa.Column("suggested_action_en", sa.Text, nullable=False),
        sa.Column("suggested_action_ne", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_violations_submission_id", "violations", ["submission_id"])
    op.create_index("ix_violations_rule_id", "violations", ["rule_id"])


def downgrade() -> None:
    op.drop_index("ix_violations_rule_id", table_name="violations")
    op.drop_index("ix_violations_submission_id", table_name="violations")
    op.drop_table("violations")
    op.drop_table("submissions")
    postgresql.ENUM(name="severity").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="employment_type").drop(op.get_bind(), checkfirst=True)
