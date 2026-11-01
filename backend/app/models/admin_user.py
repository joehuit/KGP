"""AdminUser model for administrative authentication and access control."""

from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import PK_BIGINT, TimestampMixin

if TYPE_CHECKING:
    from app.models.notification_token import DeviceNotificationToken


class AdminUser(Base, TimestampMixin):
    """Internal administrator user account."""

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="admin", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    notification_tokens: Mapped[List["DeviceNotificationToken"]] = relationship(
        "DeviceNotificationToken",
        back_populates="admin_user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<AdminUser id={self.id} email={self.email} role={self.role}>"
