"""Accounts, employers, weekly settings, work logs

Revision ID: 0002_auth_and_employers
Revises: 0001_initial
Create Date: 2026-08-07
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_auth_and_employers"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("username", sa.String(80), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("gender", sa.String(20), nullable=True),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("age", sa.Integer, nullable=True),
        sa.Column("ethnicity", sa.String(80), nullable=True),
        sa.Column("education_level", sa.String(60), nullable=True),
        sa.Column("language", sa.String(5), nullable=False, server_default="en"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

    op.create_table(
        "employers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),

        # Employment
        sa.Column("employer_name", sa.String(120), nullable=False),
        sa.Column("work_province", sa.String(40), nullable=True),
        sa.Column("work_district", sa.String(40), nullable=True),
        sa.Column("work_address", sa.String(160), nullable=True),
        sa.Column("skill_level", sa.String(20), nullable=True),
        sa.Column("industry", sa.String(40), nullable=True),
        sa.Column("employment_type", sa.String(20), nullable=False),
        sa.Column("job_title", sa.String(120), nullable=True),
        sa.Column("hiring_channel", sa.String(20), nullable=True),
        sa.Column("contractor_name", sa.String(120), nullable=True),
        sa.Column("tenure_years", sa.Float, nullable=True),
        sa.Column("tenure_months", sa.Float, nullable=True),
        sa.Column("on_probation", sa.Boolean, nullable=True),
        sa.Column("probation_since", sa.Date, nullable=True),

        # Contracted work time
        sa.Column("contract_hours_per_day", sa.Float, nullable=True),
        sa.Column("contract_break_start", sa.Time, nullable=True),
        sa.Column("contract_break_end", sa.Time, nullable=True),
        sa.Column("contract_break_unspecified", sa.Boolean, nullable=True),
        sa.Column("contract_days_per_week", sa.Float, nullable=True),
        sa.Column("contract_break_days", postgresql.JSONB, nullable=True),
        sa.Column("contract_break_days_unspecified", sa.Boolean, nullable=True),
        sa.Column("contract_months_per_year", sa.Float, nullable=True),
        sa.Column("contract_break_months", postgresql.JSONB, nullable=True),
        sa.Column("contract_daily_hours", sa.Float, nullable=True),
        sa.Column("contract_weekly_hours", sa.Float, nullable=True),
        sa.Column("contract_monthly_hours", sa.Float, nullable=True),

        # Actual work time
        sa.Column("actual_hours_per_day", sa.Float, nullable=True),
        sa.Column("actual_break_start", sa.Time, nullable=True),
        sa.Column("actual_break_end", sa.Time, nullable=True),
        sa.Column("actual_break_unspecified", sa.Boolean, nullable=True),
        sa.Column("actual_days_per_week", sa.Float, nullable=True),
        sa.Column("actual_break_days", postgresql.JSONB, nullable=True),
        sa.Column("actual_break_days_unspecified", sa.Boolean, nullable=True),
        sa.Column("actual_months_per_year", sa.Float, nullable=True),
        sa.Column("actual_break_months", postgresql.JSONB, nullable=True),
        sa.Column("actual_daily_hours", sa.Float, nullable=True),
        sa.Column("actual_weekly_hours", sa.Float, nullable=True),
        sa.Column("actual_monthly_hours", sa.Float, nullable=True),

        # Overtime
        sa.Column("overtime_rule", sa.Boolean, nullable=True),
        sa.Column("overtime_hours_per_unit", sa.Float, nullable=True),
        sa.Column("overtime_unit", sa.String(20), nullable=True),
        sa.Column("overtime_rate", sa.String(10), nullable=True),
        sa.Column("overtime_rate_other", sa.Float, nullable=True),
        sa.Column("overtime_consent", sa.String(20), nullable=True),
        sa.Column("night_work", sa.Boolean, nullable=True),
        sa.Column("night_allowance", sa.Boolean, nullable=True),

        # Pay
        sa.Column("pay_unit", sa.String(20), nullable=True),
        sa.Column("promised_wage", sa.Float, nullable=True),
        sa.Column("monthly_salary_calculated", sa.Float, nullable=True),
        sa.Column("monthly_wage_received", sa.Float, nullable=True),
        sa.Column("payment_method", sa.String(20), nullable=True),
        sa.Column("wage_payment_days_after_month_end", sa.Float, nullable=True),
        sa.Column("received_annual_increment", sa.Boolean, nullable=True),
        sa.Column("festival_expense_paid", sa.Boolean, nullable=True),
        sa.Column("other_deduction_reason", sa.String(200), nullable=True),

        # Leave
        sa.Column("weekly_leave_days_per_month", sa.Float, nullable=True),
        sa.Column("weekly_off_day_guaranteed", sa.Boolean, nullable=True),
        sa.Column("worked_off_day_paid_and_replaced", sa.Boolean, nullable=True),
        sa.Column("public_holiday_paid_leave", sa.Boolean, nullable=True),
        sa.Column("sick_leave_denied", sa.Boolean, nullable=True),
        sa.Column("pregnant_or_maternity_last_year", sa.Boolean, nullable=True),
        sa.Column("maternity_leave_denied", sa.Boolean, nullable=True),
        sa.Column("paternity_leave_denied", sa.Boolean, nullable=True),
        sa.Column("mourning_leave_denied", sa.Boolean, nullable=True),

        # Contract
        sa.Column("has_written_contract", sa.Boolean, nullable=True),
        sa.Column("contract_states_wage", sa.Boolean, nullable=True),
        sa.Column("contract_states_hours", sa.Boolean, nullable=True),
        sa.Column("contract_states_leave", sa.Boolean, nullable=True),
        sa.Column("contract_states_termination", sa.Boolean, nullable=True),
        sa.Column("contract_explained_in_own_language", sa.Boolean, nullable=True),

        # Social security
        sa.Column("ssf_registered", sa.Boolean, nullable=True),
        sa.Column("pf_deducted", sa.Boolean, nullable=True),
        sa.Column("pf_deposited", sa.Boolean, nullable=True),
        sa.Column("gratuity_deducted", sa.Boolean, nullable=True),
        sa.Column("gratuity_paid_by_employer", sa.Boolean, nullable=True),
        sa.Column("medical_insurance_provided", sa.Boolean, nullable=True),
        sa.Column("accidental_insurance_provided", sa.Boolean, nullable=True),

        # Recruitment & documents
        sa.Column("paid_fee_to_get_job", sa.Boolean, nullable=True),
        sa.Column("wage_withheld_before_start", sa.Boolean, nullable=True),
        sa.Column("employer_holds_documents", sa.Boolean, nullable=True),

        # Safety & treatment
        sa.Column("free_to_leave_during_off_hours", sa.Boolean, nullable=True),
        sa.Column("abuse_experienced", sa.Boolean, nullable=True),

        # Termination
        sa.Column("terminated", sa.Boolean, nullable=True),
        sa.Column("notice_given_days", sa.Float, nullable=True),
        sa.Column("retrenchment_compensation_months", sa.Float, nullable=True),
        sa.Column("final_settlement_within_15_days", sa.Boolean, nullable=True),

        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_employers_user_id", "employers", ["user_id"])

    op.create_table(
        "weekly_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("break_days_this_week", postgresql.JSONB, nullable=True),
        sa.Column("promised_payment_day", sa.Date, nullable=True),
        sa.Column("daily_promised_wage", sa.Float, nullable=True),
        sa.ForeignKeyConstraint(["employer_id"], ["employers.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_weekly_settings_employer_id", "weekly_settings", ["employer_id"])
    op.create_unique_constraint("uq_weekly_settings_employer_id", "weekly_settings", ["employer_id"])

    op.create_table(
        "work_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("log_date", sa.Date, nullable=False),
        sa.Column("report_time", sa.Time, nullable=True),
        sa.Column("scheduled_end_time", sa.Time, nullable=True),
        sa.Column("scheduled_break_start", sa.Time, nullable=True),
        sa.Column("scheduled_break_end", sa.Time, nullable=True),
        sa.Column("work_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("work_ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("breaks", postgresql.JSONB, nullable=True),
        sa.Column("overtime_minutes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("paid_amount", sa.Float, nullable=True),
        sa.Column("promised_amount", sa.Float, nullable=True),
        sa.Column("deductions", postgresql.JSONB, nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employer_id"], ["employers.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_work_logs_user_id", "work_logs", ["user_id"])
    op.create_index("ix_work_logs_employer_id", "work_logs", ["employer_id"])
    op.create_index("ix_work_logs_log_date", "work_logs", ["log_date"])


def downgrade() -> None:
    op.drop_index("ix_work_logs_log_date", table_name="work_logs")
    op.drop_index("ix_work_logs_employer_id", table_name="work_logs")
    op.drop_index("ix_work_logs_user_id", table_name="work_logs")
    op.drop_table("work_logs")
    op.drop_constraint("uq_weekly_settings_employer_id", "weekly_settings", type_="unique")
    op.drop_index("ix_weekly_settings_employer_id", table_name="weekly_settings")
    op.drop_table("weekly_settings")
    op.drop_index("ix_employers_user_id", table_name="employers")
    op.drop_table("employers")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_index("ix_sessions_token", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
