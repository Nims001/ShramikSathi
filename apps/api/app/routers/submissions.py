"""POST /api/submissions — intake form -> rule engine -> persist -> results."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..schemas.submission import SubmissionCreate, SubmissionResult
from ..services.submissions import create_submission

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionResult)
async def submit(payload: SubmissionCreate, db: AsyncSession = Depends(get_db)) -> SubmissionResult:
    """Accept the anonymized intake form, run the deterministic rule engine,
    persist everything, and return the detected violations."""
    return await create_submission(db, payload)
