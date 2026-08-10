"""Dual-consensus signing: user signature keys + worklog approval fields

Revision ID: 0010_dual_consensus_signing
Revises: 0009_employer_portal
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010_dual_consensus_signing"
down_revision = "0009_employer_portal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Per-user digital-signature keys (RSA-2048). The private half is AES-256-GCM
    # encrypted with the server SIGNING_SECRET before storage.
    op.add_column(
        "users",
        sa.Column("signing_public_key_pem", sa.Text(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("signing_private_key_enc", sa.Text(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("signing_key_fingerprint", sa.String(length=64), nullable=True),
    )

    # Work-log approval / signature state machine.
    op.add_column(
        "work_logs",
        sa.Column("content_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "work_logs",
        sa.Column(
            "approval_status",
            sa.String(length=20),
            nullable=False,
            server_default="draft",
        ),
    )
    op.add_column(
        "work_logs",
        sa.Column("submission_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "work_logs",
        sa.Column("employee_signature", sa.Text(), nullable=True),
    )
    op.add_column(
        "work_logs",
        sa.Column("employee_signed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_logs",
        sa.Column("employer_signature", sa.Text(), nullable=True),
    )
    op.add_column(
        "work_logs",
        sa.Column("employer_signed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_logs",
        sa.Column("employer_decision_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_logs",
        sa.Column("rejection_reason", sa.Text(), nullable=True),
    )

    # Append-only audit ledger of signing / approval / rejection events.
    op.create_table(
        "worklog_signatures",
        sa.Column(
            "id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True
        ),
        sa.Column(
            "worklog_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("work_logs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("actor_user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("submission_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("signature", sa.Text(), nullable=True),
        sa.Column("canonical_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_worklog_signatures_worklog_id", "worklog_signatures", ["worklog_id"])


def downgrade() -> None:
    op.drop_index("ix_worklog_signatures_worklog_id", table_name="worklog_signatures")
    op.drop_table("worklog_signatures")
    op.drop_column("work_logs", "rejection_reason")
    op.drop_column("work_logs", "employer_decision_at")
    op.drop_column("work_logs", "employer_signed_at")
    op.drop_column("work_logs", "employer_signature")
    op.drop_column("work_logs", "employee_signed_at")
    op.drop_column("work_logs", "employee_signature")
    op.drop_column("work_logs", "submission_version")
    op.drop_column("work_logs", "approval_status")
    op.drop_column("work_logs", "content_hash")
    op.drop_column("users", "signing_key_fingerprint")
    op.drop_column("users", "signing_private_key_enc")
    op.drop_column("users", "signing_public_key_pem")
