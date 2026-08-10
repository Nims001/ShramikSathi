"""Placeholder integration routes for future external systems.

These are deliberately stub-grade (per the build brief, "just stubbed
routes/interfaces, not real integrations"):

- Nagarik app SSO   -> POST /api/integrations/nagarik/sso
- Sharmsansar export -> GET  /api/integrations/sharmsansar/export

The Sharmsansar export returns the worker's own data as JSON (the same
document used by the AI analysis) so the interface is real and testable, while
the actual mapping to Sharmsansar's API remains future work.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import current_user
from ..models import User
from ..services.analysis import build_analysis_document

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.post("/nagarik/sso")
async def nagarik_sso_placeholder() -> dict:
    """Future Nagarik app single sign-on. Not implemented — returns a stub."""
    raise HTTPException(
        status_code=501,
        detail="The Nagarik app SSO integration is a placeholder stub and is not "
        "implemented yet.",
    )


@router.get("/sharmsansar/export")
async def sharmsansar_export_placeholder(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Exports the worker's data as JSON (placeholder for Sharmsansar).

    The payload is the same analysis document used elsewhere in the app; a real
    integration would map this onto Sharmsansar's schema instead of returning
    it verbatim.
    """
    document = await build_analysis_document(db, user)
    return {
        "format": "sharmsansar-export-placeholder",
        "note": "Stub export — the real Sharmsansar data mapping is future work.",
        "data": document,
    }
