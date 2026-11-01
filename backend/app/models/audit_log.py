"""AuditLog model for recording critical administrative actions and state changes."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from app.models.base import PK_BIGINT


class AuditActorType(str, Enum):
    """Actor performing the audited action."""
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    GUEST = "GUEST"
    SYSTEM = "SYSTEM"


class AuditLog(Base):
    """Audit trail record for security, price updates, and sensitive administrative operations."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True, index=True)
    actor_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} actor={self.actor_type}:{self.actor_id} action={self.action} entity={self.entity_type}:{self.entity_id}>"
