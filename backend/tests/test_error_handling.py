"""Automated tests for safe error handling, standardized envelopes, and sensitive log redaction."""

from fastapi.testclient import TestClient
from app.core.logging import redact_sensitive_data


def test_404_not_found_envelope(client: TestClient):
    """Ensure non-existent endpoints return the standard error envelope."""
    response = client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404

    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "timestamp" in data["error"]


def test_422_validation_error_envelope(client: TestClient, admin_headers: dict):
    """Ensure request validation failures return standardized 422 envelope with field details."""
    # 1. Attempt to create product with invalid negative price and missing required fields (authorized)
    invalid_payload = {
        "sku": "INVALID!SKU",
        "selling_price": -50.0,
    }
    response = client.post("/api/v1/products", json=invalid_payload, headers=admin_headers)
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(data["error"]["details"], list)
    assert len(data["error"]["details"]) > 0

    # 2. Public customer registration with invalid Algerian phone number triggers 422
    cust_res = client.post("/api/v1/customers", json={"full_name": "Test", "phone_number": "12345"})
    assert cust_res.status_code == 422
    assert cust_res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_malformed_json_body_envelope(client: TestClient, admin_headers: dict):
    """Ensure raw unparseable JSON payload is caught safely."""
    response = client.post(
        "/api/v1/products",
        content="This is not JSON at all {{{",
        headers={"Content-Type": "application/json", **admin_headers},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_internal_server_error_sanitization(client: TestClient):
    """Ensure unhandled server exceptions return sanitized 500 without leaking stack traces."""
    # We can invoke a route that deliberately causes an unhandled error or test the handler directly
    from fastapi import Request
    from app.core.errors import register_exception_handlers
    from app.main import app

    # Add a temporary test-only route to trigger an unexpected exception
    @app.get("/api/test-deliberate-crash", include_in_schema=False)
    def trigger_crash():
        raise RuntimeError("Secret DB Password in memory: P@ssw0rd123! C:\\Users\\App\\db.py")

    response = client.get("/api/test-deliberate-crash")
    assert response.status_code == 500

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    # Verify the client NEVER sees internal error details or stack traces
    assert "Secret DB Password" not in response.text
    assert "P@ssw0rd123" not in response.text
    assert "C:\\Users" not in response.text
    assert "RuntimeError" not in response.text


def test_sensitive_data_redaction():
    """Verify phone numbers, bearer tokens, admin keys, and secrets are redacted from log messages."""
    # 1. Algerian phone number (compact)
    sample_phone_log = "Customer registered with phone 0550123456 and wilaya Algiers"
    redacted = redact_sensitive_data(sample_phone_log)
    assert "0550123456" not in redacted
    assert "[REDACTED_PHONE]" in redacted

    # 2. Algerian phone number with spaces and country code
    sample_phone_spaced = "Customer contact: +213 661 12 34 56 (workshop phone)"
    redacted_spaced = redact_sensitive_data(sample_phone_spaced)
    assert "661 12 34 56" not in redacted_spaced
    assert "[REDACTED_PHONE]" in redacted_spaced

    # 3. Bearer token
    sample_auth_log = "Incoming request with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token"
    redacted_auth = redact_sensitive_data(sample_auth_log)
    assert "eyJhbGciOi" not in redacted_auth
    assert "[REDACTED_TOKEN]" in redacted_auth

    # 4. Database password string
    sample_db_log = "Connecting to postgresql+psycopg://kgp_user:MySuperSecret123@localhost:5432/kgp_db"
    redacted_db = redact_sensitive_data(sample_db_log)
    assert "MySuperSecret123" not in redacted_db
    assert "[REDACTED]" in redacted_db

    # 5. X-Admin-Key header
    sample_admin_log = "Header x-admin-key: my_super_secret_admin_key_12345"
    redacted_admin = redact_sensitive_data(sample_admin_log)
    assert "my_super_secret_admin_key_12345" not in redacted_admin
    assert "[REDACTED]" in redacted_admin
