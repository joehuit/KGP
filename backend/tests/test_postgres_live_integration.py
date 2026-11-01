"""Integration tests for live PostgreSQL database connectivity and migrations.

Note:
These tests require a running PostgreSQL instance (or Docker container).
If PostgreSQL is unavailable, they are cleanly and explicitly skipped with a clear explanation,
ensuring honesty and transparency per architectural requirements.
"""

import pytest
from tests.conftest import is_postgres_available
from app.core.config import settings


@pytest.mark.integration
def test_live_postgres_connectivity():
    """Verify live PostgreSQL connectivity when PostgreSQL or Docker is active."""
    if not is_postgres_available():
        pytest.skip(
            f"PostgreSQL service is not running at {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}. "
            "Live PostgreSQL integration testing requires a running PostgreSQL instance or Docker container."
        )

    from sqlalchemy import create_engine, text
    engine = create_engine(settings.sync_database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();")).scalar()
        assert "PostgreSQL" in str(result)


@pytest.mark.integration
def test_live_postgres_idempotency_table_exists():
    """Verify idempotency_keys table exists in PostgreSQL after migration."""
    if not is_postgres_available():
        pytest.skip(
            f"PostgreSQL service is not running at {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}. "
            "Skipping live PostgreSQL schema inspection."
        )

    from sqlalchemy import create_engine, inspect
    engine = create_engine(settings.sync_database_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "idempotency_keys" in tables
