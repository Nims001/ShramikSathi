"""FastAPI application entrypoint.

Wires CORS, includes routers, and exposes a health-check endpoint used by
docker-compose. Route handlers are deliberately thin — business logic lives in
`rules/` and `services/`.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import (
    analysis,
    auth,
    dashboard,
    employer_portal,
    employers,
    integrations,
    ocr,
    submissions,
    worklogs,
)

app = FastAPI(
    title="ShramikSathi — AI Labour Rights Assistant",
    version="0.1.0",
    description="Deterministic violation checker against The Labour Act, 2017 (Nepal).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(submissions.router)
app.include_router(ocr.router)
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(employers.router)
app.include_router(worklogs.router)
app.include_router(analysis.router)
app.include_router(employer_portal.router)
app.include_router(integrations.router)


@app.get("/api/health", tags=["health"])
async def health() -> dict:
    """Health-check for docker-compose / uptime probes."""
    return {"status": "ok"}
