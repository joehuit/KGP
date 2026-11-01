"""Product model representing mobile phone spare-parts items."""

from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import PK_BIGINT, TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.order_item import OrderItem


class Product(Base, TimestampMixin):
    """Mobile phone spare part item with exact decimal pricing in Algerian Dinars (DZD)."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("selling_price >= 0", name="ck_products_selling_price_positive"),
        CheckConstraint(
            "available_quantity IS NULL OR available_quantity >= 0",
            name="ck_products_quantity_positive",
        ),
    )

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True, index=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Safe decimal representation for Algerian Dinars (e.g., 14500.00 DZD)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    available_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku={self.sku} name={self.name} price={self.selling_price}>"
