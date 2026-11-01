"""Automated tests for administrator authentication, JWT lifecycle, rate limiting, and revocation."""

from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import create_access_token, get_password_hash
from app.models.admin_user import AdminUser


def test_admin_login_success(client: TestClient, admin_user: AdminUser):
    """Test successful administrator login returns signed JWT access token and permissions."""
    payload = {
        "email": admin_user.email,
        "password": "AdminPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]

    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["role"] == "admin"
    assert data["user_id"] == admin_user.id
    assert data["full_name"] == admin_user.full_name
    assert "catalog:write" in data["permissions"]
    assert "admin_users:manage" not in data["permissions"]  # Only superadmin has user management


def test_admin_login_invalid_password(client: TestClient, admin_user: AdminUser):
    """Ensure invalid passwords return safe 401 error without leaking details."""
    payload = {
        "email": admin_user.email,
        "password": "WrongPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "UNAUTHORIZED"
    assert "Invalid email or password" in error["message"]


def test_admin_login_nonexistent_email(client: TestClient):
    """Ensure non-existent email addresses return identical safe 401 response (anti-enumeration)."""
    payload = {
        "email": "nonexistent_admin@kgp-test.dz",
        "password": "SomeRandomPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "UNAUTHORIZED"
    assert "Invalid email or password" in error["message"]


def test_admin_login_deactivated_account(client: TestClient, db_session: Session):
    """Ensure inactive admin accounts are rejected with 401."""
    inactive_user = AdminUser(
        email="inactive@kgp-test.dz",
        hashed_password=get_password_hash("ValidPass123!"),
        full_name="Inactive Admin",
        role="admin",
        is_active=False,
    )
    db_session.add(inactive_user)
    db_session.commit()

    payload = {
        "email": "inactive@kgp-test.dz",
        "password": "ValidPass123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "inactive" in response.json()["error"]["message"].lower()


def test_admin_login_rate_limiting(client: TestClient, admin_user: AdminUser):
    """Ensure rapid successive login attempts trigger HTTP 429 Too Many Requests."""
    payload = {
        "email": admin_user.email,
        "password": "WrongPassword123!",
    }
    # 5 allowed attempts
    for _ in range(5):
        res = client.post("/api/v1/auth/login", json=payload)
        assert res.status_code == 401

    # 6th attempt must be rejected by rate limiter
    blocked_res = client.post("/api/v1/auth/login", json=payload)
    assert blocked_res.status_code == 429
    assert blocked_res.json()["error"]["code"] == "TOO_MANY_REQUESTS"
    assert "Retry-After" in blocked_res.headers


def test_admin_logout_and_token_revocation(client: TestClient, admin_token: str):
    """Test that logging out revokes the JWT and subsequent requests with it are rejected."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Profile query works with valid token
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200

    # 2. Call logout
    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["data"]["revoked"] is True

    # 3. Subsequent request with the same token is rejected
    revoked_res = client.get("/api/v1/auth/me", headers=headers)
    assert revoked_res.status_code == 401
    assert "revoked" in revoked_res.json()["error"]["message"].lower()


def test_get_current_admin_profile(client: TestClient, superadmin_token: str):
    """Test /api/v1/auth/me returns complete role and permission profile."""
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["role"] == "superadmin"
    assert data["email"] == "superadmin@kgp-test.dz"
    assert "admin_users:manage" in data["permissions"]
    assert "catalog:write" in data["permissions"]
    assert "orders:write" in data["permissions"]


def test_expired_token_rejected(client: TestClient, admin_user: AdminUser):
    """Test that expired JWT access tokens are rejected with 401."""
    # Create token expired 1 hour ago
    expired_token = create_access_token(
        data={"sub": str(admin_user.id), "type": "admin", "role": admin_user.role},
        expires_delta=timedelta(hours=-1),
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert "expired" in response.json()["error"]["message"].lower()


def test_tampered_token_rejected(client: TestClient, admin_token: str):
    """Test that a tampered JWT payload/signature is rejected with 401."""
    tampered = admin_token[:-4] + "ABCD"
    headers = {"Authorization": f"Bearer {tampered}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
