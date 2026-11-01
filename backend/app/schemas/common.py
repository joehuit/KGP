"""Common API response and pagination schemas."""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standardized top-level response envelope for consistent client responses."""
    success: bool = True
    message: Optional[str] = None
    data: T


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""
    page: int = Field(ge=1, description="Current page number (1-based)")
    page_size: int = Field(ge=1, le=100, description="Items per page")
    total_items: int = Field(ge=0, description="Total count of matching records")
    total_pages: int = Field(ge=0, description="Total number of available pages")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated list container."""
    items: List[T]
    meta: PaginationMeta
