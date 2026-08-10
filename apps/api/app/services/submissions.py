"""Submission service — runs the rule engine and persists the result."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Submission, Violation
from ..rules.engine import run_rules
from ..schemas.submission import SubmissionCreate, SubmissionResult
from ..schemas.violation import ViolationOut


async def create_submission(db: AsyncSession, payload: SubmissionCreate) -> SubmissionResult:
    """Run deterministic rules, persist the anonymized submission + violations,
    and return the result payload for the client."""
    violations = run_rules(payload)

    submission = Submission(**payload.model_dump())
    db.add(submission)
    # flush assigns the server-generated id so violations can reference it.
    await db.flush()

    for v in violations:
        db.add(
            Violation(
                submission_id=submission.id,
                rule_id=v.rule_id,
                section_reference=v.section_reference,
                severity=v.severity,
                plain_explanation_en=v.plain_explanation_en,
                plain_explanation_ne=v.plain_explanation_ne,
                suggested_action_en=v.suggested_action_en,
                suggested_action_ne=v.suggested_action_ne,
            )
        )

    await db.commit()

    # Re-select the submission, eagerly loading violations (async sessions
    # cannot lazy-load a relationship without an explicit await).
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission.id)
        .options(selectinload(Submission.violations))
    )
    saved = result.scalar_one()

    return SubmissionResult(
        submission_id=saved.id,
        created_at=saved.created_at,
        violations=[ViolationOut.model_validate(v) for v in saved.violations],
    )
