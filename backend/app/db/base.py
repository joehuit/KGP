"""Alembic base metadata registry.
Import all ORM models here so that Alembic and metadata reflection find them.
"""

from app.db.session import Base
from app.models.admin_user import AdminUser
from app.models.category import Category
from app.models.product import Product
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.notification_token import DeviceNotificationToken, DevicePlatform
from app.models.audit_log import AuditLog, AuditActorType

__all__ = [
    "Base",
    "AdminUser",
    "Category",
    "Product",
    "Customer",
    "Order",
    "OrderStatus",
    "OrderItem",
    "DeviceNotificationToken",
    "DevicePlatform",
    "AuditLog",
    "AuditActorType",
]
