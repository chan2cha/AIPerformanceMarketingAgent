from fastapi import FastAPI

from app.schemas.health import HealthResponse

app = FastAPI(title="AI Performance Marketing API", version="0.1.0")


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Return process liveness without depending on external services."""
    return HealthResponse(status="ok")
