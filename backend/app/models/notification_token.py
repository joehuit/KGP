"""DeviceNotificationToken model for Firebase Cloud Messaging (FCM) push notifications."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import PK_BIGINT

if TYPE_CHECKING:
    from app.models.admin_user import AdminUser
    from app.models.customer import Customer


class DevicePlatform(str, Enum):
    """Client device platform."""
    ANDROID = "ANDROID"
    IOS = "IOS"
    WEB = "WEB"


class DeviceNotificationToken(Base):
    """FCM device push notification registration token."""

    __tablename__ = "device_notification_tokens"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True, index=True)
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    platform: Mapped[DevicePlatform] = mapped_column(
        SQLEnum(DevicePlatform, native_enum=False, length=20),
        default=DevicePlatform.ANDROID,
        nullable=False,
    )
    customer_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    admin_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="notification_tokens")
    admin_user: Mapped[Optional["AdminUser"]] = relationship("AdminUser", back_populates="notification_tokens")

    def __repr__(self) -> str:
        return f"<DeviceToken id={self.id} platform={self.platform} active={self.is_active}>"
