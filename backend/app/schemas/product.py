"""Pydantic schemas for Product catalog management with decimal currency validation."""

from datetime import datetime
from decimal import Decimal
import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    """Shared attributes for Product catalog items."""
    sku: str = Field(..., min_length=2, max_length=64, description="Unique product SKU/code")
    name: str = Field(..., min_length=2, max_length=200, description="Spare-part commercial name")
    category_id: int = Field(..., ge=1, description="Associated category ID")
    # Exact decimal currency representation in Algerian Dinars (DZD)
    selling_price: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
        decimal_places=2,
        max_digits=12,
        description="Selling price in Algerian Dinars (e.g. 14500.00 DZD)",
    )
    available_quantity: Optional[int] = Field(
        None,
        ge=0,
        description="Optional current stock quantity",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Detailed technical specs, compatibility, or quality grade",
    )
    is_active: bool = Field(default=True, description="Whether item is visible to customers")

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Validate SKU format: non-empty, stripped, reasonable characters."""
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("SKU cannot be empty or whitespace.")
        if not re.match(r"^[A-Z0-9_\-\./]+$", cleaned):
            raise ValueError("SKU must only contain alphanumeric characters, hyphens, slashes, or underscores.")
        return cleaned

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean product name."""
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Product name must be at least 2 characters long.")
        return cleaned

    @field_validator("selling_price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Enforce non-negative decimal currency with at most 2 decimal places."""
        if v < Decimal("0.00"):
            raise ValueError("Selling price cannot be negative.")
        # Ensure scale does not exceed 2 decimal places (Algerian Dinar cents)
        if v.as_tuple().exponent < -2:
            raise ValueError("Selling price cannot exceed 2 decimal places.")
        return v.quantize(Decimal("0.01"))


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product."""
    sku: Optional[str] = Field(None, min_length=2, max_length=64)
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    category_id: Optional[int] = Field(None, ge=1)
    selling_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"), decimal_places=2, max_digits=12)
    available_quantity: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip().upper()
            if not re.match(r"^[A-Z0-9_\-\./]+$", cleaned):
                raise ValueError("SKU must only contain alphanumeric characters, hyphens, or underscores.")
            return cleaned
        return v

    @field_validator("selling_price")
    @classmethod
    def validate_price(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v < Decimal("0.00"):
                raise ValueError("Selling price cannot be negative.")
            if v.as_tuple().exponent < -2:
                raise ValueError("Selling price cannot exceed 2 decimal places.")
            return v.quantize(Decimal("0.01"))
        return v


class ProductResponse(ProductBase):
    """Schema for product responses returned to clients."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProductImportRow(BaseModel):
    """Single parsed product row from uploaded spreadsheet."""
    row_index: int
    sku: str
    name: str
    category_name: str
    selling_price: Decimal
    available_quantity: Optional[int] = None
    description: Optional[str] = None
    status: str = Field(description="'new', 'update', or 'invalid'")
    errors: list[str] = []


class ExcelImportPreviewResponse(BaseModel):
    """Result of spreadsheet parsing and pre-commit validation."""
    filename: str
    detected_columns: list[str]
    column_mapping: dict[str, Optional[str]]
    total_rows: int
    valid_count: int
    invalid_count: int
    new_products_count: int
    update_products_count: int
    new_categories: list[str]
    rows: list[ProductImportRow]


class ExcelImportCommitRequest(BaseModel):
    """Payload to commit validated spreadsheet rows."""
    items: list[ProductImportRow]
    create_missing_categories: bool = True
    update_existing_products: bool = False


class ExcelImportCommitSummary(BaseModel):
    """Summary of committed bulk import transaction."""
    total_processed: int
    created: int
    updated: int
    skipped: int
    failed: int
    errors: list[str]

