"""Idempotency record model for duplicate order submission prevention."""

from datetime import datetime, timedelta, timezone
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from app.models.base import PK_BIGINT


class IdempotencyKey(Base):
    """Stores unique idempotency tokens and their executed HTTP responses.
    Prevents duplicate charge/order creations upon network retries.
    """

    __tablename__ = "idempotency_keys"

    id: Mapped[int] = mapped_column(
        PK_BIGINT,
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    key: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )
    request_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA-256 hash of (path + customer identity + serialized request body)",
    )
    response_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    response_body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<IdempotencyKey(key='{self.key}', code={self.response_code}, expires_at='{self.expires_at}')>"
