"""Shared API dependencies: database sessions, pagination, and administrative/customer authorization."""

from typing import Generator, List, Optional, Tuple, Union
import secrets
from fastapi import Depends, Header, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import AuthenticationError, ForbiddenError
from app.core.logging import logger
from app.core.security import AdminRole, Permission, decode_access_token, has_permission
from app.db.session import get_db
from app.models.admin_user import AdminUser
from app.models.customer import Customer


def get_db_session() -> Generator[Session, None, None]:
    """Dependency yielding a transactional SQLAlchemy Session."""
    yield from get_db()


class PaginationParams:
    """Query parameter dependency for paginated listing endpoints."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-based)"),
        page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size


def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """Extract token string from Authorization header."""
    if not authorization:
        return None
    token = authorization.strip()
    if token.lower().startswith("bearer "):
        return token[7:].strip()
    return token


def check_legacy_admin_key(key_candidate: Optional[str]) -> bool:
    """Validate temporary ADMIN_API_KEY in non-production environments.
    Strictly rejected in production and staging.
    """
    if settings.ENVIRONMENT in ("production", "staging"):
        return False
    if not key_candidate or not settings.ADMIN_API_KEY:
        return False
    candidate = key_candidate.strip()
    configured = settings.ADMIN_API_KEY.strip()
    if not candidate or not configured or len(configured) < 32:
        return False
    return secrets.compare_digest(candidate, configured)


def get_current_admin(
    authorization: Optional[str] = Header(None, description="Bearer admin JWT"),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key", description="Legacy dev API key"),
    db: Session = Depends(get_db_session),
) -> AdminUser:
    """Authenticate administrator from JWT access token or development fallback."""
    raw_token = extract_bearer_token(authorization)

    # 1. Check JWT Bearer token
    if raw_token:
        # Check if the bearer token is actually the legacy ADMIN_API_KEY in dev/testing
        if check_legacy_admin_key(raw_token):
            logger.warning("Legacy ADMIN_API_KEY passed in Authorization header. Deprecated for JWT.")
            admin = db.scalar(select(AdminUser).where(AdminUser.role == AdminRole.SUPERADMIN.value))
            if not admin:
                admin = AdminUser(
                    id=1,
                    email="admin@kgp-list.dz",
                    full_name="System Superadmin",
                    role=AdminRole.SUPERADMIN.value,
                    is_active=True,
                )
            return admin

        # Decode standard JWT
        try:
            payload = decode_access_token(raw_token)
        except AuthenticationError:
            raise
        except Exception as exc:
            raise AuthenticationError(f"Could not validate administrative credentials: {str(exc)}")

        if payload.get("type") != "admin":
            raise AuthenticationError("Administrative access requires an administrator token.")

        admin_id = payload.get("sub")
        if not admin_id:
            raise AuthenticationError("Malformed token: missing subject claim.")

        admin = db.get(AdminUser, int(admin_id))
        if not admin:
            raise AuthenticationError("Administrator account not found.")
        if not admin.is_active:
            raise AuthenticationError("Administrator account has been deactivated.")

        return admin

    # 2. Check X-Admin-Key header
    if x_admin_key is not None:
        candidate_key = x_admin_key.strip()
        if not candidate_key:
            raise AuthenticationError(
                "Administrative authorization required. Provide 'Authorization' or 'X-Admin-Key' header."
            )

        if settings.ENVIRONMENT in ("production", "staging"):
            logger.critical("Rejected ADMIN_API_KEY usage attempt in %s environment.", settings.ENVIRONMENT)
            raise AuthenticationError(
                "ADMIN_API_KEY authentication is disabled in staging and production. "
                "Authenticate using 'Authorization: Bearer <jwt_token>'."
            )

        if check_legacy_admin_key(candidate_key):
            logger.warning("Development fallback: authenticated request using deprecated X-Admin-Key.")
            admin = db.scalar(select(AdminUser).where(AdminUser.role == AdminRole.SUPERADMIN.value))
            if not admin:
                admin = AdminUser(
                    id=1,
                    email="admin@kgp-list.dz",
                    full_name="System Superadmin",
                    role=AdminRole.SUPERADMIN.value,
                    is_active=True,
                )
            return admin
        else:
            raise ForbiddenError("Invalid administrative credentials. Access denied.")

    raise AuthenticationError(
        "Administrative authorization required. Provide 'Authorization: Bearer <token>' header."
    )


def require_roles(allowed_roles: List[Union[AdminRole, str]]):
    """Dependency factory enforcing Role-Based Access Control (RBAC)."""
    normalized_roles = [r.value if isinstance(r, AdminRole) else str(r) for r in allowed_roles]

    def _role_checker(current_admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
        if current_admin.role not in normalized_roles:
            logger.warning(
                "RBAC violation: Admin %s with role '%s' attempted operation requiring roles %s",
                current_admin.email,
                current_admin.role,
                normalized_roles,
            )
            raise ForbiddenError(
                f"Role '{current_admin.role}' does not have permission to perform this operation."
            )
        return current_admin

    return _role_checker


def require_permission(permission: Permission):
    """Dependency factory enforcing granular permissions."""
    def _perm_checker(current_admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
        if not has_permission(current_admin.role, permission):
            logger.warning(
                "Permission violation: Admin %s with role '%s' lacks permission '%s'",
                current_admin.email,
                current_admin.role,
                permission.value,
            )
            raise ForbiddenError(
                f"Role '{current_admin.role}' lacks permission '{permission.value}'."
            )
        return current_admin

    return _perm_checker


def get_current_customer(
    authorization: Optional[str] = Header(None, description="Bearer customer JWT"),
    db: Session = Depends(get_db_session),
) -> Customer:
    """Authenticate mobile app customer from JWT access token."""
    raw_token = extract_bearer_token(authorization)
    if not raw_token:
        raise AuthenticationError("Customer authentication required. Provide 'Authorization: Bearer <token>'.")

    try:
        payload = decode_access_token(raw_token)
    except AuthenticationError:
        raise
    except Exception as exc:
        raise AuthenticationError(f"Could not validate customer credentials: {str(exc)}")

    if payload.get("type") != "customer":
        raise AuthenticationError("Invalid token type for customer operations.")

    cust_id = payload.get("sub")
    if not cust_id:
        raise AuthenticationError("Malformed token: missing subject claim.")

    customer = db.get(Customer, int(cust_id))
    if not customer:
        raise AuthenticationError("Customer account not found.")
    if not customer.is_active:
        raise AuthenticationError("Customer account is inactive. Please contact support.")

    return customer


def get_current_user_or_admin(
    authorization: Optional[str] = Header(None, description="Bearer customer or admin token"),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key", description="Legacy dev Admin Key"),
    db: Session = Depends(get_db_session),
) -> Tuple[Optional[Customer], Optional[AdminUser]]:
    """Determine whether the request comes from an authenticated customer or an administrator."""
    # 1. If X-Admin-Key header is presented, route to get_current_admin (handles dev fallback & prod rejection)
    if x_admin_key is not None:
        admin = get_current_admin(authorization=authorization, x_admin_key=x_admin_key, db=db)
        return None, admin

    raw_token = extract_bearer_token(authorization)
    if not raw_token:
        raise AuthenticationError("Authentication required. Provide 'Authorization: Bearer <token>' header.")

    # 2. Check if raw_token is legacy admin key in dev
    if check_legacy_admin_key(raw_token):
        admin = get_current_admin(authorization=authorization, x_admin_key=x_admin_key, db=db)
        return None, admin

    # 3. Decode JWT and branch by token type
    try:
        payload = decode_access_token(raw_token)
    except Exception as exc:
        raise AuthenticationError(f"Invalid authentication token: {str(exc)}")

    token_type = payload.get("type")
    sub_id = payload.get("sub")

    if token_type == "customer":
        customer = db.get(Customer, int(sub_id))
        if not customer or not customer.is_active:
            raise AuthenticationError("Customer account not found or inactive.")
        return customer, None
    elif token_type == "admin":
        admin = db.get(AdminUser, int(sub_id))
        if not admin or not admin.is_active:
            raise AuthenticationError("Administrator account not found or inactive.")
        return None, admin
    else:
        raise AuthenticationError("Unrecognized authentication token type.")


def get_optional_admin(
    authorization: Optional[str] = Header(None, description="Optional Bearer token"),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key", description="Optional Admin Key"),
    db: Session = Depends(get_db_session),
) -> bool:
    """Determine whether the current request presents valid admin credentials without raising."""
    try:
        admin = get_current_admin(authorization=authorization, x_admin_key=x_admin_key, db=db)
        return admin is not None
    except Exception:
        return False


# Backward-compatibility bridge for existing endpoints
def require_admin_auth(
    authorization: Optional[str] = Header(None, description="Bearer admin token"),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key", description="Admin API key"),
    db: Session = Depends(get_db_session),
) -> str:
    """Backward-compatible admin authentication returning credential string."""
    admin = get_current_admin(authorization=authorization, x_admin_key=x_admin_key, db=db)
    return admin.email
