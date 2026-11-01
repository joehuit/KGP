"""Base model and shared column mixins."""

from datetime import datetime, timezone
from sqlalchemy import BigInteger, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

# BigInteger for PostgreSQL (int64) with SQLite Integer variant for unit test autoincrement compatibility
PK_BIGINT = BigInteger().with_variant(Integer, "sqlite")


class TimestampMixin:
    """Provides automatic UTC creation and update timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
