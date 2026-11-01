"""Pydantic schemas for Category entities."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """Shared attributes for Category."""
    name: str = Field(..., min_length=2, max_length=100, description="Category name (e.g. Screens, Batteries)")
    display_order: int = Field(default=0, ge=0, description="Display sorting order")
    is_active: bool = Field(default=True, description="Whether the category is visible in the catalog")


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    """Schema for category responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
