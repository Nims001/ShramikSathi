"""Analysis endpoints: one JSON document describing the worker's situation.

The document (user + every employer + weekly settings + work logs + derived
stats + deterministic findings) is structured to be handed to a prompting AI so
it can cite violations under The Labour Act, 2017 (Nepal).

- GET  /api/analysis      → the document itself
- POST /api/analysis/ai   → runs the RAG "Analyse with AI" step over it
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..ai.gemini_analysis import AiNotConfiguredError
from ..ai.negotiation import run_negotiation
from ..ai.service import run_ai_analysis
from ..db import get_db
from ..deps import current_user
from ..models import User
from ..services.analysis import build_analysis_document

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

NOT_CONFIGURED_MESSAGE = (
    "GEMINI_API_KEY is not set. The AI features are disabled; "
    "deterministic findings are still shown."
)


@router.get("")
async def get_analysis_document(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """The full worker document, ready for AI prompting."""
    return await build_analysis_document(db, user)


def _ai_error(status: int, e: Exception) -> HTTPException:
    """Standard error mapping for the AI endpoints (no stack traces leak)."""
    return HTTPException(status_code=status, detail=str(e))


@router.post("/ai")
async def analyse_with_ai(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Runs retrieval + Gemini over the worker's document and returns new,
    AI-generated findings (grouped by employer). Deterministic findings remain
    the source of truth; this step only adds what the rules can't catch."""
    try:
        return await run_ai_analysis(db, user)
    except AiNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")


@router.post("/negotiate")
async def generate_negotiation_script(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Drafts a short, polite negotiation script per employer (AI-generated,
    clearly labelled as a suggestion — not legal advice)."""
    try:
        return await run_negotiation(db, user)
    except AiNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Negotiation script failed: {e}")
