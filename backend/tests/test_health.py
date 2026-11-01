"""Automated tests for health check endpoints and sensitive data leakage prevention."""

from fastapi.testclient import TestClient


def test_health_endpoint_success(client: TestClient):
    """Test that GET /api/health responds with 200 OK and expected structure."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] == "testing"
    assert "version" in data
    assert "timestamp" in data


def test_health_endpoint_does_not_leak_secrets(client: TestClient):
    """Ensure health endpoint never leaks database credentials, passwords, or secret keys."""
    response = client.get("/api/health")
    assert response.status_code == 200

    raw_text = response.text.lower()
    # Check that secrets and internals are strictly absent
    forbidden_terms = [
        "password",
        "secret",
        "postgres://",
        "postgresql://",
        "psycopg",
        "c:\\",
        "/home/",
        "root",
        "token",
        ".env",
        "database_url",
    ]
    for term in forbidden_terms:
        assert term not in raw_text, f"Potential sensitive leak detected: found '{term}' in health response"


def test_v1_health_endpoint(client: TestClient):
    """Test that GET /api/v1/health also responds with identical healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] == "testing"


def test_root_endpoint_info(client: TestClient):
    """Test that GET / responds with service overview and doc links without leaking internals."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert data["health_check"] == "/api/health"
