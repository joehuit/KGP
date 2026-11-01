"""Health check endpoint."""

from datetime import datetime, timezone
from fastapi import APIRouter, status
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Production-safe health check",
    description="Returns the current operational status without exposing secrets or connection strings.",
)
def check_health() -> HealthResponse:
    """Return operational health status.
    Strictly sanitizes output to avoid exposing database credentials or server paths.
    """
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
