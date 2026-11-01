"""Security utilities: password hashing, JWT generation, RBAC roles, and token revocation."""

from datetime import datetime, timedelta, timezone
from enum import Enum
import threading
import time
from typing import Any, Dict, List, Optional, Set
import uuid
import bcrypt
import jwt
from app.core.config import settings
from app.core.errors import AuthenticationError


class AdminRole(str, Enum):
    """Role-based access control roles for KGP administration."""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    OPERATOR = "operator"


class Permission(str, Enum):
    """Granular system permissions enforced across backend endpoints."""
    ADMIN_USERS_MANAGE = "admin_users:manage"
    CATALOG_READ = "catalog:read"
    CATALOG_WRITE = "catalog:write"
    ORDERS_READ = "orders:read"
    ORDERS_WRITE = "orders:write"
    ORDERS_STATUS = "orders:status"
    AUDIT_READ = "audit:read"


# Explicit Role-to-Permissions Mapping
ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
    AdminRole.SUPERADMIN.value: {
        Permission.ADMIN_USERS_MANAGE,
        Permission.CATALOG_READ,
        Permission.CATALOG_WRITE,
        Permission.ORDERS_READ,
        Permission.ORDERS_WRITE,
        Permission.ORDERS_STATUS,
        Permission.AUDIT_READ,
    },
    AdminRole.ADMIN.value: {
        Permission.CATALOG_READ,
        Permission.CATALOG_WRITE,
        Permission.ORDERS_READ,
        Permission.ORDERS_WRITE,
        Permission.ORDERS_STATUS,
    },
    AdminRole.OPERATOR.value: {
        Permission.CATALOG_READ,
        Permission.ORDERS_READ,
        Permission.ORDERS_STATUS,
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """Check if the given administrative role grants a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a salted bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a plain password using bcrypt with a secure random salt."""
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# In-Memory Token Revocation Store with Automatic Expiration Pruning
class TokenRevocationService:
    """Thread-safe store for revoked JWT token IDs (jti).
    In multi-worker production deployments, this service can be backed by Redis.
    """

    def __init__(self):
        self._revoked_tokens: Dict[str, float] = {}  # jti -> expiration timestamp
        self._lock = threading.Lock()

    def revoke(self, jti: str, expires_at: Optional[float] = None) -> None:
        """Revoke a token by its jti identifier until its natural expiration."""
        if not jti:
            return
        exp = expires_at or (time.time() + 86400 * 7)
        with self._lock:
            self._prune_expired()
            self._revoked_tokens[jti] = exp

    def is_revoked(self, jti: str) -> bool:
        """Check if a jti has been marked revoked."""
        if not jti:
            return False
        with self._lock:
            self._prune_expired()
            return jti in self._revoked_tokens

    def _prune_expired(self) -> None:
        """Remove tokens whose natural expiration has passed to conserve memory."""
        now = time.time()
        expired_keys = [k for k, exp in self._revoked_tokens.items() if exp < now]
        for k in expired_keys:
            del self._revoked_tokens[k]


token_revocation_service = TokenRevocationService()


# JWT creation and verification
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a cryptographically signed JWT access token with standard claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "iat": now,
        "nbf": now,
        "jti": jti,
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a signed JWT token.
    Enforces signature validity, expiration, and revocation status.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Access token has expired. Please authenticate again.")
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(f"Invalid access token: {str(exc)}")

    jti = payload.get("jti")
    if jti and token_revocation_service.is_revoked(jti):
        raise AuthenticationError("Access token has been revoked. Please authenticate again.")

    return payload
