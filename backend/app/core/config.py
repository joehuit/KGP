"""Centralized application configuration using Pydantic Settings."""

import json
from pathlib import Path
from typing import Any, List, Literal, Optional, Union
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_backend_dir = Path(__file__).resolve().parent.parent.parent
_project_root = _backend_dir.parent
_env_files = tuple(
    str(p)
    for p in (
        _project_root / ".env",
        _project_root / ".env.local",
        _backend_dir / ".env",
        _backend_dir / ".env.local",
    )
)


class Settings(BaseSettings):
    """Production-ready application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=_env_files,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "KGP LIST API"
    PROJECT_DESCRIPTION: str = "Mobile spare-parts catalog and ordering platform for Algeria"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.1.0"

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = "development"
    DEBUG: bool = False

    # Security & Tokens
    # Minimum 32-character secret key for JWT/cookie signing
    SECRET_KEY: str = "dev_insecure_secret_key_change_in_production_min_32_chars_long"
    ADMIN_API_KEY: str = "dev_admin_api_key_change_in_production_min_32_chars"
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days (default fallback)
    ADMIN_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 hours
    CUSTOMER_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days for mobile customers

    # SMS Verification Provider configuration
    SMS_GATEWAY_PROVIDER: Literal["dev_mock", "twilio", "algeria_telecom"] = "dev_mock"
    SMS_API_KEY: Optional[str] = None

    # CORS origins allowed to communicate with API
    # Supports JSON array string '["http://localhost:3000"]' or comma-separated list
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Database parameters
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "kgp_user"
    POSTGRES_PASSWORD: str = "kgp_secret_password_change_me"
    POSTGRES_DB: str = "kgp_db"
    DATABASE_URL: Union[str, None] = None
    DATABASE_URL_UNPOOLED: Union[str, None] = None
    NEON_BRANCH: Union[str, None] = None

    # Connection pool configuration
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 3600  # 1 hour

    # Rate limiting & performance
    RATE_LIMIT_PER_MINUTE: int = 60
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from JSON list, comma-separated string, or Python list."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        return []

    @property
    def sync_database_url(self) -> str:
        """Return the effective SQLAlchemy synchronous connection string."""
        if self.DATABASE_URL:
            # If standard postgresql:// is provided, normalize to postgresql+psycopg://
            url = str(self.DATABASE_URL).strip().strip("'\"")
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            return url
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_unpooled_database_url(self) -> str:
        """Return the unpooled SQLAlchemy synchronous connection string (for Alembic DDL migrations)."""
        url = self.DATABASE_URL_UNPOOLED or self.DATABASE_URL
        if url:
            url = str(url).strip().strip("'\"")
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            return url
        return self.sync_database_url

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Enforce strict production constraints to prevent insecure deployments."""
        if self.ENVIRONMENT in ("production", "staging"):
            # 1. Never allow wildcard CORS in production/staging
            if "*" in self.CORS_ORIGINS:
                raise ValueError("CORS wildcard ('*') is strictly forbidden in production mode.")

            # 2. Never allow known default or weak dev keys in production/staging
            clean_secret = (self.SECRET_KEY or "").strip()
            if "dev_insecure" in clean_secret.lower() or len(clean_secret) < 32:
                raise ValueError(
                    "SECRET_KEY must be a cryptographically secure string of at least 32 characters in production."
                )

            clean_admin_key = (self.ADMIN_API_KEY or "").strip()
            if "dev_admin" in clean_admin_key.lower() or len(clean_admin_key) < 32:
                raise ValueError(
                    "ADMIN_API_KEY must be a cryptographically secure string of at least 32 characters in production."
                )

            # 3. Prevent debug mode in production/staging
            if self.DEBUG:
                raise ValueError("DEBUG mode must be set to False in production.")

            # 4. Enforce secure JWT algorithms (strictly forbid 'none' or insecure variants)
            if self.ALGORITHM not in ("HS256", "HS384", "HS512"):
                raise ValueError("Only secure HMAC-SHA algorithms (HS256, HS384, HS512) are permitted.")

        return self


# Global singleton settings instance
settings = Settings()
