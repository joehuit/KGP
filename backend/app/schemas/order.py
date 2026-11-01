"""Pydantic schemas for Orders and immutable OrderItems."""

import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    """Input line item when placing an order."""
    product_id: int = Field(..., ge=1, description="Product ID being ordered")
    quantity: int = Field(..., ge=1, le=1000, description="Quantity requested")


class OrderItemResponse(BaseModel):
    """Snapshot line item returned with order details."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    product_id: Optional[int] = None
    product_name: str
    product_sku: str
    unit_price: Decimal
    quantity: int
    total_price: Decimal
    created_at: datetime


class OrderCreate(BaseModel):
    """Schema for creating a new order."""
    customer_id: int = Field(..., ge=1, description="Customer ID placing the order")
    customer_notes: Optional[str] = Field(None, max_length=1000, description="Special instructions or delivery notes")
    items: List[OrderItemCreate] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of items to order (maximum 50 distinct items per order)",
    )


class OrderStatusUpdate(BaseModel):
    """Schema for updating order lifecycle status."""
    status: OrderStatus = Field(..., description="Target order status")


class OrderResponse(BaseModel):
    """Detailed response schema for an order."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_reference: str
    customer_id: int
    status: OrderStatus
    total_amount: Decimal
    customer_notes: Optional[str] = None
    tracking_token: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime


class GuestOrderCreate(BaseModel):
    """Schema for placing a guest order without pre-registration or password."""
    full_name: str = Field(..., min_length=2, max_length=150, description="Customer full name")
    phone_number: str = Field(..., description="Algerian mobile phone number (05, 06, or 07)")
    wilaya: str = Field(..., min_length=2, max_length=50, description="Algerian wilaya (e.g. '16 - Alger')")
    commune: str = Field(..., min_length=2, max_length=50, description="Commune (e.g. 'El Harrach')")
    delivery_address: str = Field(..., min_length=3, max_length=255, description="Street / workshop address")
    customer_notes: Optional[str] = Field(None, max_length=1000, description="Optional customer delivery instructions")
    items: List[OrderItemCreate] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of items to order (maximum 50 distinct items per order)",
    )

    @field_validator("phone_number")
    @classmethod
    def validate_algerian_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\.]", "", v)
        match = re.match(r"^(?:\+213|00213|0)([5-7][0-9]{8})$", cleaned)
        if not match:
            raise ValueError("Invalid Algerian mobile phone number. Must start with 05, 06, or 07 followed by 8 digits.")
        return f"0{match.group(1)}"


class GuestOrderResponse(BaseModel):
    """Response schema for guest orders including secure tracking token."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_reference: str
    tracking_token: str
    status: OrderStatus
    total_amount: Decimal
    customer_name: str
    customer_phone_masked: str
    wilaya: str
    commune: str
    delivery_address: str
    customer_notes: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: datetime


class GuestOrderTrackRequest(BaseModel):
    """Payload to track a guest order via POST body, preventing bearer token leakage in proxy URI logs."""
    tracking_token: str = Field(..., min_length=10, max_length=128, description="Cryptographically secure order tracking token")
