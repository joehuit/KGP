"""Automated tests validating Alembic migration configuration and version scripts."""

from pathlib import Path
import configparser
import importlib.util


def test_alembic_ini_validity():
    """Ensure alembic.ini exists and has valid configuration directives."""
    ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    assert ini_path.exists(), "alembic.ini file missing from backend root."

    config = configparser.ConfigParser()
    config.read(str(ini_path))
    assert "alembic" in config.sections()
    assert config.get("alembic", "script_location") == "alembic"


def test_initial_migration_script_structure():
    """Ensure initial migration 0001_initial_schema.py is syntactically valid and exposes upgrade/downgrade."""
    migration_path = (
        Path(__file__).resolve().parent.parent / "alembic" / "versions" / "0001_initial_schema.py"
    )
    assert migration_path.exists(), "Initial migration script 0001_initial_schema.py is missing."

    spec = importlib.util.spec_from_file_location("initial_migration", str(migration_path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Verify migration identifiers
    assert getattr(module, "revision") == "0001_initial_schema"
    assert getattr(module, "down_revision") is None

    # Verify required callables exist
    assert callable(getattr(module, "upgrade"))
    assert callable(getattr(module, "downgrade"))


def test_idempotency_migration_script_structure():
    """Ensure idempotency migration 0002_add_idempotency_keys.py is syntactically valid."""
    migration_path = (
        Path(__file__).resolve().parent.parent / "alembic" / "versions" / "0002_add_idempotency_keys.py"
    )
    assert migration_path.exists(), "Migration script 0002_add_idempotency_keys.py is missing."

    spec = importlib.util.spec_from_file_location("idempotency_migration", str(migration_path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Verify migration identifiers
    assert getattr(module, "revision") == "0002_add_idempotency_keys"
    assert getattr(module, "down_revision") == "0001_initial_schema"

    # Verify required callables exist
    assert callable(getattr(module, "upgrade"))
    assert callable(getattr(module, "downgrade"))


def test_tracking_token_migration_script_structure():
    """Ensure order tracking token migration 0003_add_order_tracking_token.py is syntactically valid."""
    migration_path = (
        Path(__file__).resolve().parent.parent / "alembic" / "versions" / "0003_add_order_tracking_token.py"
    )
    assert migration_path.exists(), "Migration script 0003_add_order_tracking_token.py is missing."

    spec = importlib.util.spec_from_file_location("tracking_token_migration", str(migration_path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Verify migration identifiers
    assert getattr(module, "revision") == "0003_add_order_tracking_token"
    assert getattr(module, "down_revision") == "0002_add_idempotency_keys"

    # Verify required callables exist
    assert callable(getattr(module, "upgrade"))
    assert callable(getattr(module, "downgrade"))
