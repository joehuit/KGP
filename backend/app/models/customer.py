"""Customer model representing repair shops and spare-parts retail buyers in Algeria."""

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import PK_BIGINT, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.notification_token import DeviceNotificationToken


class Customer(Base, TimestampMixin):
    """Customer profile (repair shop technician, store owner, or individual)."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    business_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    wilaya: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    notification_tokens: Mapped[List["DeviceNotificationToken"]] = relationship(
        "DeviceNotificationToken",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} full_name={self.full_name} wilaya={self.wilaya}>"
