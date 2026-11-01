"""Structured logging system with sensitive data redaction."""

import json
import logging
import re
import sys
from typing import Any, Dict
from app.core.config import settings

# Patterns for redacting sensitive information
# Redact Algerian phone numbers (e.g., 0550123456, 0661 12 34 56, 0770-12-34-56, +213 550 12 34 56, 00213...)
PHONE_REGEX = re.compile(r"(?:(?:\+213|00213)[\s\-]?)?0?[5-7](?:[\s\-]?[0-9]){8}\b")
# Redact authorization tokens / bearer headers
AUTH_BEARER_REGEX = re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)
# Redact passwords, secret keys, admin keys, authorization headers, or db credentials in strings
SECRET_KEY_REGEX = re.compile(
    r"(password|secret|token|api_key|api-key|admin_key|admin-key|x-admin-key|access_token|authorization)\s*[:=]\s*['\"]?([^'\",\s]+)['\"]?",
    re.IGNORECASE,
)
# Redact PostgreSQL connection passwords
DB_PASS_REGEX = re.compile(r"(postgresql(?:\+[a-z0-9]+)?://[^:]+:)([^@]+)(@)", re.IGNORECASE)


def redact_sensitive_data(text: str) -> str:
    """Sanitize strings by redacting phone numbers, passwords, and tokens."""
    if not isinstance(text, str):
        return text
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    text = AUTH_BEARER_REGEX.sub(r"\1[REDACTED_TOKEN]", text)
    text = SECRET_KEY_REGEX.sub(r"\1=[REDACTED]", text)
    text = DB_PASS_REGEX.sub(r"\1[REDACTED]\3", text)
    return text


class SensitiveDataFilter(logging.Filter):
    """Logging filter that ensures sensitive customer data and secrets are never emitted to logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_data(record.msg)

        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: redact_sensitive_data(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True


class JsonFormatter(logging.Formatter):
    """Production-grade JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging() -> None:
    """Initialize structured application logging with sanitization filters."""
    root_logger = logging.getLogger()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Avoid adding duplicate handlers on multiple invocations
    if root_logger.handlers:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.addFilter(SensitiveDataFilter())

    if settings.ENVIRONMENT == "production":
        console_handler.setFormatter(JsonFormatter())
    else:
        standard_format = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(standard_format)

    root_logger.addHandler(console_handler)

    # Suppress verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


# Initialize module logger
logger = logging.getLogger("kgp.backend")
