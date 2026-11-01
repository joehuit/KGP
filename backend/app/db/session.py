"""Database engine creation, session factory, and connection lifecycle."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

# Base class for all ORM models
Base = declarative_base()

# Configure engine with robust production connection pooling
engine_kwargs = {
    "echo": False,
    "pool_pre_ping": settings.DB_POOL_PRE_PING,
    "pool_recycle": settings.DB_POOL_RECYCLE,
}

# If using PostgreSQL, configure QueuePool parameters and connect timeout
if "postgresql" in settings.sync_database_url or "postgres" in settings.sync_database_url:
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "connect_args": {"connect_timeout": 3},
    })

engine = create_engine(settings.sync_database_url, **engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a transactional database session per request."""
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error("Transaction rolled back due to error: %s", str(e))
        raise
    finally:
        db.close()


def init_db_connection() -> None:
    """Validate database connectivity on application startup."""
    if settings.ENVIRONMENT == "testing":
        logger.info("Testing environment active; skipping live database connection probe.")
        return

    try:
        with engine.connect() as conn:
            logger.info("Successfully established connection to database.")
    except Exception as exc:
        logger.warning(
            "Could not connect to database on startup (%s). "
            "Ensure PostgreSQL is running and migrations are applied.",
            exc,
        )


def dispose_db_connection() -> None:
    """Close all open pooled connections on application shutdown."""
    try:
        engine.dispose()
        logger.info("Database connection pools successfully disposed.")
    except Exception as exc:
        logger.error("Error disposing database connection pools: %s", exc)
