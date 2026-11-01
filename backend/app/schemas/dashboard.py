"""Pydantic schemas for the main administration dashboard statistics."""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.order import OrderResponse
from app.schemas.product import ProductResponse


class DashboardStatsResponse(BaseModel):
    """Aggregated real-time metrics for store managers and administrators."""
    total_products: int
    total_categories: int
    total_customers: int
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    processing_orders: int
    shipped_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_revenue: Decimal
    low_stock_count: int
    low_stock_products: List[ProductResponse]
    recent_orders: List[OrderResponse]

    model_config = ConfigDict(from_attributes=True)
