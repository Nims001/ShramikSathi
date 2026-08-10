"""
FastAPI endpoint for the "Analyse with AI" feature. The frontend sends
the full worker JSON payload here; this endpoint runs retrieval +
Gemini analysis and returns the new AI-generated findings.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.intake.schema import AnalyseRequest
from src.intake.retrieval import build_retrieval_context
from src.compliance.gemini_analysis import analyse_with_ai
from src.compliance.analysis_schema_validator import parse_and_validate
from src.ingestion.embed_and_index import get_vectorstore

app = FastAPI(title="Labour Act Compliance - Analyse with AI")

# Allow your frontend (adjust origins for your actual dev/prod URLs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your actual frontend URL before going live
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the vectorstore once at startup, not per-request — avoids
# reloading the embedding model on every single API call.
vectorstore = None


@app.on_event("startup")
def load_vectorstore():
    global vectorstore
    vectorstore = get_vectorstore()
    print("Vectorstore loaded and ready.")


@app.post("/analyse")
def analyse(request: AnalyseRequest):
    """
    Runs the AI compliance analysis for the first employer in the
    request. Returns new findings (not duplicating deterministic ones).
    """
    if not request.employers:
        raise HTTPException(status_code=400, detail="No employer data provided.")

    employer_block = request.employers[0]
    employer = employer_block.employer
    existing_findings = employer_block.deterministic_findings or []

    try:
        context = build_retrieval_context(employer, vectorstore=vectorstore)
        retrieved_numbers = [doc.metadata.get("section") for doc in context["deduped_sections"]]

        raw_response = analyse_with_ai(employer, existing_findings, context["deduped_sections"])
        findings, is_valid, errors = parse_and_validate(raw_response, retrieved_numbers)

        if not is_valid:
            # Don't fail the whole request — return empty findings with
            # a warning, so the frontend still gets the deterministic
            # findings even if the AI step had an issue.
            return {
                "ai_findings": [],
                "warning": "AI analysis validation failed; showing deterministic findings only.",
                "validation_errors": errors,
            }

        return {"ai_findings": findings}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/health")
def health_check():
    return {"status": "ok"}