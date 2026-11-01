"""Automated regression tests proving ADMIN_API_KEY migration and production rejection."""

from fastapi.testclient import TestClient
from app.core.config import settings


def test_legacy_admin_key_accepted_in_test_environment(client: TestClient, admin_headers: dict):
    """Ensure X-Admin-Key continues to work as development bridge in non-production environments."""
    assert settings.ENVIRONMENT == "testing"
    res = client.get("/api/v1/orders", headers=admin_headers)
    assert res.status_code == 200


def test_legacy_admin_key_rejected_in_production(client: TestClient, monkeypatch):
    """Ensure X-Admin-Key is strictly blocked when ENVIRONMENT is set to production."""
    # Temporarily switch ENVIRONMENT to production
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    headers = {"X-Admin-Key": "test_admin_api_key_minimum_32_characters_for_validation"}
    res = client.get("/api/v1/orders", headers=headers)
    assert res.status_code == 401
    assert "disabled in staging and production" in res.json()["error"]["message"]


def test_legacy_admin_key_rejected_in_staging(client: TestClient, monkeypatch):
    """Ensure X-Admin-Key is strictly blocked when ENVIRONMENT is set to staging."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")

    headers = {"X-Admin-Key": "test_admin_api_key_minimum_32_characters_for_validation"}
    res = client.get("/api/v1/orders", headers=headers)
    assert res.status_code == 401
    assert "disabled in staging and production" in res.json()["error"]["message"]
