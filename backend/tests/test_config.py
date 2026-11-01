"""Automated tests for configuration management, CORS parsing, and security validation."""

import pytest
from pydantic import ValidationError
from app.core.config import Settings


def test_default_config_loading():
    """Test standard settings initialization with development defaults."""
    cfg = Settings(
        ENVIRONMENT="development",
        SECRET_KEY="dev_key_sufficiently_long_for_development_purposes_only",
    )
    assert cfg.PROJECT_NAME == "KGP LIST API"
    assert cfg.API_V1_STR == "/api/v1"
    assert cfg.ENVIRONMENT == "development"
    assert cfg.RATE_LIMIT_PER_MINUTE == 60


def test_cors_origins_parsing():
    """Test parsing CORS origins from various formats (JSON string, CSV, list)."""
    # From JSON array string
    cfg_json = Settings(
        CORS_ORIGINS='["http://localhost:3000", "http://admin.kgp.dz"]',
        SECRET_KEY="test_key_minimum_32_characters_long_for_test",
    )
    assert cfg_json.CORS_ORIGINS == ["http://localhost:3000", "http://admin.kgp.dz"]

    # From comma-separated string
    cfg_csv = Settings(
        CORS_ORIGINS="http://localhost:3000, http://admin.kgp.dz",
        SECRET_KEY="test_key_minimum_32_characters_long_for_test",
    )
    assert cfg_csv.CORS_ORIGINS == ["http://localhost:3000", "http://admin.kgp.dz"]

    # From Python list
    cfg_list = Settings(
        CORS_ORIGINS=["http://localhost:3000", "http://admin.kgp.dz"],
        SECRET_KEY="test_key_minimum_32_characters_long_for_test",
    )
    assert cfg_list.CORS_ORIGINS == ["http://localhost:3000", "http://admin.kgp.dz"]


def test_production_cors_wildcard_forbidden():
    """Ensure CORS wildcard (*) is strictly rejected in production."""
    with pytest.raises(ValidationError, match="CORS wildcard .* forbidden in production"):
        Settings(
            ENVIRONMENT="production",
            CORS_ORIGINS=["*"],
            SECRET_KEY="a_very_secure_and_cryptographically_strong_random_key_here",
            DEBUG=False,
        )


def test_production_weak_secret_key_forbidden():
    """Ensure default or short secret keys are rejected in production."""
    with pytest.raises(ValidationError, match="SECRET_KEY must be a cryptographically secure string"):
        Settings(
            ENVIRONMENT="production",
            CORS_ORIGINS=["https://admin.kgp.dz"],
            SECRET_KEY="dev_insecure_key",
            DEBUG=False,
        )

    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            ENVIRONMENT="production",
            CORS_ORIGINS=["https://admin.kgp.dz"],
            SECRET_KEY="too_short_key",
            DEBUG=False,
        )


def test_production_weak_admin_api_key_forbidden():
    """Ensure default, short, or whitespace admin API keys are rejected in production."""
    # 1. Default dev key rejected
    with pytest.raises(ValidationError, match="ADMIN_API_KEY must be a cryptographically secure string"):
        Settings(
            ENVIRONMENT="production",
            CORS_ORIGINS=["https://admin.kgp.dz"],
            SECRET_KEY="a_very_secure_and_cryptographically_strong_random_key_here",
            ADMIN_API_KEY="dev_admin_api_key_default",
            DEBUG=False,
        )

    # 2. Too short key rejected
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            ENVIRONMENT="production",
            CORS_ORIGINS=["https://admin.kgp.dz"],
            SECRET_KEY="a_very_secure_and_cryptographically_strong_random_key_here",
            ADMIN_API_KEY="short_key_123",
            DEBUG=False,
        )

    # 3. Whitespace key rejected
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            ENVIRONMENT="production",
            CORS_ORIGINS=["https://admin.kgp.dz"],
            SECRET_KEY="a_very_secure_and_cryptographically_strong_random_key_here",
            ADMIN_API_KEY=" " * 35,
            DEBUG=False,
        )

    # 4. Valid key accepted
    valid_cfg = Settings(
        ENVIRONMENT="production",
        CORS_ORIGINS=["https://admin.kgp.dz"],
        SECRET_KEY="a_very_secure_and_cryptographically_strong_random_key_here",
        ADMIN_API_KEY="a_very_secure_and_cryptographically_strong_admin_key_32_chars",
        DEBUG=False,
    )
    assert valid_cfg.ADMIN_API_KEY == "a_very_secure_and_cryptographically_strong_admin_key_32_chars"


def test_staging_weak_keys_forbidden():
    """Ensure staging environment also strictly rejects dev keys."""
    with pytest.raises(ValidationError, match="ADMIN_API_KEY must be a cryptographically secure string"):
        Settings(
            ENVIRONMENT="staging",
            CORS_ORIGINS=["https://staging.kgp.dz"],
            SECRET_KEY="a_very_secure_and_cryptographically_strong_random_key_here",
            ADMIN_API_KEY="dev_admin_staging_key",
            DEBUG=False,
        )


def test_production_debug_mode_forbidden():
    """Ensure debug mode cannot be enabled in production."""
    with pytest.raises(ValidationError, match="DEBUG mode must be set to False in production"):
        Settings(
            ENVIRONMENT="production",
            CORS_ORIGINS=["https://admin.kgp.dz"],
            SECRET_KEY="a_very_secure_and_cryptographically_strong_random_key_here",
            DEBUG=True,
        )


def test_database_url_normalization():
    """Ensure standard postgresql:// URLs are normalized to postgresql+psycopg://."""
    cfg = Settings(
        DATABASE_URL="postgresql://user:pass@dbhost:5432/dbname",
        SECRET_KEY="test_key_minimum_32_characters_long_for_test",
    )
    assert cfg.sync_database_url == "postgresql+psycopg://user:pass@dbhost:5432/dbname"

    cfg_short = Settings(
        DATABASE_URL="postgres://user:pass@dbhost:5432/dbname",
        SECRET_KEY="test_key_minimum_32_characters_long_for_test",
    )
    assert cfg_short.sync_database_url == "postgresql+psycopg://user:pass@dbhost:5432/dbname"
