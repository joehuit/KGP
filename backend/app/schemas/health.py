"""Health status response schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Production-safe health check status response.
    Never exposes credentials, database connection strings, or internal paths.
    """
    status: str = Field(..., example="healthy")
    environment: str = Field(..., example="development")
    version: str = Field(..., example="0.1.0")
    timestamp: str = Field(..., example="2026-10-29T10:00:00Z")
