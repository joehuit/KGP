"""API v1 router assembling all resource endpoints."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    audit_logs,
    auth,
    categories,
    customers,
    dashboard,
    health,
    orders,
    products,
    settings,
)

api_v1_router = APIRouter()

# Include resource routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(auth.admin_users_router)
api_v1_router.include_router(auth.admin_users_router, prefix="/auth")
api_v1_router.include_router(dashboard.router)
api_v1_router.include_router(categories.router)
api_v1_router.include_router(products.router)
api_v1_router.include_router(customers.router)
api_v1_router.include_router(orders.router)
api_v1_router.include_router(audit_logs.router)
api_v1_router.include_router(settings.router)

