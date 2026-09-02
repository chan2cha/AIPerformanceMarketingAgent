from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.http import install_http_handlers
from app.modules.billing.router import router as billing_router
from app.modules.brands.router import router as brands_router
from app.modules.competitors.router import router as competitors_router
from app.modules.creatives.router import router as creatives_router
from app.modules.ingestion.router import router as ingestion_router
from app.modules.jobs.router import router as jobs_router
from app.modules.organizations.router import router as organizations_router
from app.modules.usage.router import router as usage_router
from app.schemas.health import HealthResponse

app = FastAPI(title="AI Performance Marketing API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().parsed_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)
install_http_handlers(app)
app.include_router(organizations_router)
app.include_router(brands_router)
app.include_router(competitors_router)
app.include_router(creatives_router)
app.include_router(jobs_router)
app.include_router(ingestion_router)
app.include_router(usage_router)
app.include_router(billing_router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Return process liveness without depending on external services."""
    return HealthResponse(status="ok")
