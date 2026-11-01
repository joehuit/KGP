"""Pydantic schemas for Customer profiles."""

from datetime import datetime
import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CustomerBase(BaseModel):
    """Shared attributes for customer entity."""
    full_name: str = Field(..., min_length=2, max_length=150, description="Customer or shop owner name")
    phone_number: str = Field(..., description="Algerian mobile phone number (e.g. 0550123456 or +213550123456)")
    business_name: Optional[str] = Field(None, max_length=150, description="Repair shop or store trade name")
    wilaya: Optional[str] = Field(None, max_length=50, description="Algerian wilaya (province)")
    address: Optional[str] = Field(None, max_length=500, description="Street address or landmark")
    is_active: bool = Field(default=True, description="Account status")

    @field_validator("phone_number")
    @classmethod
    def validate_algerian_phone(cls, v: str) -> str:
        """Validate Algerian phone number format: standard 10-digit 05/06/07 or +213."""
        cleaned = re.sub(r"[\s\-\.]", "", v)
        # Check either 0[5-7]xxxxxxxx or +213[5-7]xxxxxxxx
        pattern = r"^(?:\+213|00213|0)([5-7][0-9]{8})$"
        match = re.match(pattern, cleaned)
        if not match:
            raise ValueError(
                "Invalid Algerian phone number. Must start with 05, 06, 07 or +213 followed by 8 digits."
            )
        # Normalize to standard 05/06/07 format
        normalized = f"0{match.group(1)}"
        return normalized


class CustomerCreate(CustomerBase):
    """Schema for registering a customer."""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating customer information."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone_number: Optional[str] = None
    business_name: Optional[str] = Field(None, max_length=150)
    wilaya: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

    @field_validator("phone_number")
    @classmethod
    def validate_algerian_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = re.sub(r"[\s\-\.]", "", v)
            pattern = r"^(?:\+213|00213|0)([5-7][0-9]{8})$"
            match = re.match(pattern, cleaned)
            if not match:
                raise ValueError("Invalid Algerian phone number.")
            return f"0{match.group(1)}"
        return v


class CustomerResponse(CustomerBase):
    """Schema for customer profile response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
