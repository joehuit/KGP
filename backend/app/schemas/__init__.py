"""Pydantic schemas package."""

from app.schemas.common import ResponseEnvelope, PaginationMeta, PaginatedResponse
from app.schemas.health import HealthResponse
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.order import OrderCreate, OrderStatusUpdate, OrderResponse, OrderItemResponse
from app.schemas.auth import (
    AdminLoginRequest,
    AdminUserCreate,
    AdminUserResponse,
    AdminUserUpdate,
    CustomerOTPRequest,
    CustomerOTPVerify,
    CustomerTokenResponse,
    TokenPayload,
    TokenResponse,
)

__all__ = [
    "ResponseEnvelope",
    "PaginationMeta",
    "PaginatedResponse",
    "HealthResponse",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "OrderCreate",
    "OrderStatusUpdate",
    "OrderResponse",
    "OrderItemResponse",
    "AdminLoginRequest",
    "AdminUserCreate",
    "AdminUserResponse",
    "AdminUserUpdate",
    "CustomerOTPRequest",
    "CustomerOTPVerify",
    "CustomerTokenResponse",
    "TokenPayload",
    "TokenResponse",
]
