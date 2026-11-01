"""Main admin dashboard aggregated analytics endpoint."""

from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_db_session, require_roles
from app.core.security import AdminRole
from app.models.admin_user import AdminUser
from app.models.category import Category
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.schemas.common import ResponseEnvelope
from app.schemas.dashboard import DashboardStatsResponse
from app.schemas.order import OrderResponse
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=ResponseEnvelope[DashboardStatsResponse])
def get_dashboard_statistics(
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.OPERATOR])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[DashboardStatsResponse]:
    """Retrieve real-time business statistics and inventory health."""
    total_products = db.scalar(select(func.count(Product.id))) or 0
    total_categories = db.scalar(select(func.count(Category.id))) or 0
    total_customers = db.scalar(select(func.count(Customer.id))) or 0
    total_orders = db.scalar(select(func.count(Order.id))) or 0

    pending_orders = db.scalar(select(func.count(Order.id)).where(Order.status == OrderStatus.PENDING)) or 0
    confirmed_orders = db.scalar(select(func.count(Order.id)).where(Order.status == OrderStatus.CONFIRMED)) or 0
    processing_orders = db.scalar(select(func.count(Order.id)).where(Order.status == OrderStatus.PROCESSING)) or 0
    shipped_orders = db.scalar(select(func.count(Order.id)).where(Order.status == OrderStatus.SHIPPED)) or 0
    delivered_orders = db.scalar(select(func.count(Order.id)).where(Order.status == OrderStatus.DELIVERED)) or 0
    cancelled_orders = db.scalar(select(func.count(Order.id)).where(Order.status == OrderStatus.CANCELLED)) or 0

    revenue_query = select(
        func.coalesce(func.sum(Order.total_amount), 0)
    ).where(
        Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED])
    )
    total_revenue = db.scalar(revenue_query) or Decimal("0.00")

    # Low stock query (<= 5 units in stock)
    low_stock_base = select(Product).where(
        Product.is_active.is_(True),
        Product.available_quantity.is_not(None),
        Product.available_quantity <= 5,
    )
    low_stock_count = db.scalar(select(func.count()).select_from(low_stock_base.subquery())) or 0
    low_stock_products = list(
        db.scalars(low_stock_base.order_by(Product.available_quantity.asc()).limit(10)).all()
    )

    # Recent orders (top 10)
    recent_orders = list(
        db.scalars(
            select(Order)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .limit(10)
        ).all()
    )

    stats = DashboardStatsResponse(
        total_products=total_products,
        total_categories=total_categories,
        total_customers=total_customers,
        total_orders=total_orders,
        pending_orders=pending_orders,
        confirmed_orders=confirmed_orders,
        processing_orders=processing_orders,
        shipped_orders=shipped_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        total_revenue=Decimal(str(total_revenue)),
        low_stock_count=low_stock_count,
        low_stock_products=[ProductResponse.model_validate(p) for p in low_stock_products],
        recent_orders=[OrderResponse.model_validate(o) for o in recent_orders],
    )

    return ResponseEnvelope(data=stats)
