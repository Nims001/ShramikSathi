"""POST /api/ocr/contract — extract candidate fields from a contract photo.

These fields are returned for the *user to confirm* — they are never
auto-submitted to the rule engine.
"""

import io

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from ..ocr.extract import extract_fields_from_image

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


class OcrResult(BaseModel):
    # Candidate fields extracted from the image (a subset of SubmissionCreate).
    candidate_fields: dict
    # Raw OCR text so the user can eyeball what was read.
    raw_text: str
    warning: str | None = None


@router.post("/contract", response_model=OcrResult)
async def ocr_contract(file: UploadFile = File(...)) -> OcrResult:
    """OCR a contract image and return candidate fields for user confirmation."""
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        extracted = extract_fields_from_image(image_bytes)
    except Exception:
        raise HTTPException(status_code=422, detail="Could not read image. Try a clearer photo.")

    candidate = {k: v for k, v in extracted.items() if not k.startswith("_")}
    warning = None
    if not candidate:
        warning = "No fields could be extracted. Please enter your details manually."

    return OcrResult(
        candidate_fields=candidate,
        raw_text=extracted.get("_raw_ocr_text", ""),
        warning=warning,
    )
