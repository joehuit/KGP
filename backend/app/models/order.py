"""Order model representing customer spare-parts purchase requests."""

from decimal import Decimal
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import PK_BIGINT, TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.order_item import OrderItem


class OrderStatus(str, Enum):
    """Lifecycle states of an order in KGP LIST."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Order(Base, TimestampMixin):
    """Order placed by a customer containing item lines."""

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_positive"),
    )

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True, index=True)
    order_reference: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
    )
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, native_enum=False, length=20),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tracking_token: Mapped[Optional[str]] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=True,
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} ref={self.order_reference} status={self.status} total={self.total_amount}>"
