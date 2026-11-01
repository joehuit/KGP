"""Tests for create_superadmin CLI utility."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.admin_user import AdminUser
from app.core.security import verify_password
from scripts.create_superadmin import (
    create_or_update_superadmin,
    validate_email,
    validate_password_strength,
)


def test_validate_email():
    assert validate_email("  Admin@KGP.DZ ") == "admin@kgp.dz"
    with pytest.raises(ValueError, match="Invalid email format"):
        validate_email("not-an-email")
    with pytest.raises(ValueError, match="Invalid email format"):
        validate_email("")


def test_validate_password_strength():
    # Valid
    validate_password_strength("StrongPass123!")

    # Too short
    with pytest.raises(ValueError, match="at least 8 characters"):
        validate_password_strength("Ab1!")

    # No uppercase
    with pytest.raises(ValueError, match="uppercase letter"):
        validate_password_strength("strongpass123!")

    # No lowercase
    with pytest.raises(ValueError, match="lowercase letter"):
        validate_password_strength("STRONGPASS123!")

    # No digit
    with pytest.raises(ValueError, match="digit"):
        validate_password_strength("StrongPassword!")


def test_create_superadmin_and_login_flow(client: TestClient, db_session: Session):
    """Test provisioning superadmin and logging in via the API."""
    user = create_or_update_superadmin(
        email="owner@kgplist.dz",
        full_name="Directeur General",
        password="MyOwnerPassword2026!",
        db=db_session,
    )

    assert user.id is not None
    assert user.email == "owner@kgplist.dz"
    assert user.role == "superadmin"
    assert user.is_active is True
    assert verify_password("MyOwnerPassword2026!", user.hashed_password) is True

    # Test login via API
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@kgplist.dz", "password": "MyOwnerPassword2026!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()["data"]
    assert data["role"] == "superadmin"
    assert "access_token" in data
    assert "admin_users:manage" in data["permissions"]


def test_update_existing_admin_to_superadmin(db_session: Session):
    """Test updating existing admin account updates password and promotes to superadmin."""
    # 1. Create first
    create_or_update_superadmin(
        email="promoted@kgplist.dz",
        full_name="Technicien Initial",
        password="InitialPassword123!",
        db=db_session,
    )

    # 2. Update with new name and password
    updated = create_or_update_superadmin(
        email="promoted@kgplist.dz",
        full_name="Directeur Technique",
        password="NewPromotedPass2026!",
        db=db_session,
    )

    assert updated.full_name == "Directeur Technique"
    assert verify_password("NewPromotedPass2026!", updated.hashed_password) is True
    assert verify_password("InitialPassword123!", updated.hashed_password) is False
