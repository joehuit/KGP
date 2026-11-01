"""Standardized error responses, exceptions, and global exception handlers."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logging import logger


class AppException(Exception):
    """Base class for all application domain exceptions."""

    def __init__(
        self,
        message: str,
        code: str = "APPLICATION_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(AppException):
    """Entity or resource was not found."""

    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictError(AppException):
    """Duplicate key or constraint conflict."""

    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ValidationError(AppException):
    """Business rule or input validation failure."""

    def __init__(self, message: str = "Validation error", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthenticationError(AppException):
    """Missing or invalid authentication credentials."""

    def __init__(self, message: str = "Authentication required", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenError(AppException):
    """Authenticated user lacks required permissions."""

    def __init__(self, message: str = "Access forbidden", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class DatabaseUnavailableError(AppException):
    """Database connection failed or unavailable."""

    def __init__(self, message: str = "Database service unavailable", details: Optional[Any] = None):
        super().__init__(
            message=message,
            code="DATABASE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class RateLimitExceededError(AppException):
    """Client has exceeded the permitted request rate limit."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        retry_after: int = 60,
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            code="TOO_MANY_REQUESTS",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )
        self.retry_after = retry_after


def build_error_envelope(code: str, message: str, details: Optional[Any] = None) -> Dict[str, Any]:
    """Build a consistent JSON error response body."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform exception handlers on the FastAPI application instance."""

    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        logger.warning("Application exception: code=%s, message=%s", exc.code, exc.message)
        headers = {}
        if hasattr(exc, "retry_after"):
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_envelope(exc.code, exc.message, exc.details),
            headers=headers if headers else None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Simplify Pydantic validation errors for mobile and web clients
        cleaned_errors = []
        for error in exc.errors():
            loc = " -> ".join(str(item) for item in error.get("loc", []))
            cleaned_errors.append({
                "field": loc,
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error"),
            })
        logger.info("Request validation failed: %d errors", len(cleaned_errors))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=build_error_envelope(
                code="VALIDATION_ERROR",
                message="The submitted request payload contains invalid fields.",
                details=cleaned_errors,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            429: "TOO_MANY_REQUESTS",
            500: "INTERNAL_SERVER_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
        }
        code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_envelope(
                code=code,
                message=str(exc.detail) if exc.detail else "HTTP error occurred",
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        # Crucial security rule: NEVER expose stack traces or raw exception messages to clients
        logger.error("Unhandled server exception: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=build_error_envelope(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal server error occurred. Please contact support.",
            ),
        )
