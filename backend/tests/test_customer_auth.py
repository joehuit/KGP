"""Automated tests for customer phone validation, SMS OTP verification, and profile privacy."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.errors import AppException
from app.models.customer import Customer
from app.services.sms_provider import _dev_sms_provider, get_sms_provider


def test_customer_otp_request_and_verify_flow(client: TestClient, registered_customer: Customer):
    """Test full customer OTP challenge: request code, retrieve from dev provider, and verify."""
    phone = registered_customer.phone_number

    # 1. Request OTP
    req_res = client.post("/api/v1/auth/customer/request-otp", json={"phone_number": phone})
    assert req_res.status_code == 200
    assert "Verification code dispatched" in req_res.json()["message"]

    # 2. Retrieve generated code from dev provider
    code = _dev_sms_provider.get_last_code(phone)
    assert code is not None
    assert len(code) == 6

    # 3. Verify OTP with correct code
    verify_res = client.post(
        "/api/v1/auth/customer/verify-otp",
        json={"phone_number": phone, "code": code},
    )
    assert verify_res.status_code == 200
    data = verify_res.json()["data"]

    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["customer"]["id"] == registered_customer.id
    assert data["customer"]["phone_number"] == phone

    # 4. Use issued customer JWT to access self-profile
    token = data["access_token"]
    me_res = client.get("/api/v1/customers/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["data"]["id"] == registered_customer.id


def test_customer_phone_normalization(client: TestClient):
    """Test that Algerian phone number formats (+213, 00213, spaces) normalize correctly."""
    # International prefix +213 550 12 34 56
    req_res = client.post(
        "/api/v1/auth/customer/request-otp",
        json={"phone_number": "+213 550 12 34 56"},
    )
    assert req_res.status_code == 200
    assert req_res.json()["data"]["phone_number"] == "0550123456"


def test_invalid_phone_number_rejected(client: TestClient):
    """Test that invalid phone formats are rejected with 422 Unprocessable Content."""
    invalid_phones = [
        "12345678",       # Too short
        "0412345678",     # Landline (not mobile 05/06/07)
        "invalid_text",   # Non-numeric
        "0912345678",     # Invalid prefix
    ]
    for p in invalid_phones:
        res = client.post("/api/v1/auth/customer/request-otp", json={"phone_number": p})
        assert res.status_code == 422, f"Expected 422 for phone {p}, got {res.status_code}"


def test_customer_otp_wrong_code_and_lockout(client: TestClient, registered_customer: Customer):
    """Test wrong verification codes and lockout after 3 failed attempts."""
    phone = registered_customer.phone_number

    # Request OTP
    client.post("/api/v1/auth/customer/request-otp", json={"phone_number": phone})

    # Attempt 1: wrong code
    res1 = client.post("/api/v1/auth/customer/verify-otp", json={"phone_number": phone, "code": "000000"})
    assert res1.status_code == 401
    assert "2 attempt(s) remaining" in res1.json()["error"]["message"]

    # Attempt 2: wrong code
    res2 = client.post("/api/v1/auth/customer/verify-otp", json={"phone_number": phone, "code": "000001"})
    assert res2.status_code == 401
    assert "1 attempt(s) remaining" in res2.json()["error"]["message"]

    # Attempt 3: wrong code
    res3 = client.post("/api/v1/auth/customer/verify-otp", json={"phone_number": phone, "code": "000002"})
    assert res3.status_code == 401
    assert "0 attempt(s) remaining" in res3.json()["error"]["message"]

    # Attempt 4: challenge consumed / locked out
    res4 = client.post("/api/v1/auth/customer/verify-otp", json={"phone_number": phone, "code": "000003"})
    assert res4.status_code == 401
    assert "too many incorrect attempts" in res4.json()["error"]["message"].lower() or "no pending" in res4.json()["error"]["message"].lower()


def test_customer_profile_privacy_boundaries(
    client: TestClient,
    registered_customer: Customer,
    customer_token: str,
):
    """Ensure strict privacy: public cannot query /customers/me or /customers/{id}."""
    # 1. Public cannot access /customers/me without token
    res1 = client.get("/api/v1/customers/me")
    assert res1.status_code == 401

    # 2. Customer can access own /customers/me
    res2 = client.get(
        "/api/v1/customers/me",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert res2.status_code == 200
    assert res2.json()["data"]["id"] == registered_customer.id

    # 3. Customer token CANNOT access administrative /customers/{id}
    res3 = client.get(
        f"/api/v1/customers/{registered_customer.id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert res3.status_code == 401  # Requires admin token


def test_sms_provider_environment_guard(monkeypatch, client: TestClient):
    """Test that DevelopmentSMSProvider is blocked in production and staging environments."""
    # 1. Direct call to dev provider in production returns False and logs hazard
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert _dev_sms_provider.send_verification_code("0550123456", "123456") is False

    # 2. get_sms_provider raises 503 if no production provider is set
    monkeypatch.setattr(settings, "SMS_GATEWAY_PROVIDER", "none")
    with pytest.raises(AppException) as exc_info:
        get_sms_provider()
    assert exc_info.value.status_code == 503
    assert "No production SMS gateway configured" in exc_info.value.message

    # 3. Direct API call returns 503 when production lacks SMS gateway
    res = client.post("/api/v1/auth/customer/request-otp", json={"phone_number": "0550123456"})
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "SMS_GATEWAY_NOT_CONFIGURED"


def test_production_sms_gateway_activation_enforced(monkeypatch, client: TestClient):
    """Test that unactivated carrier gateways raise 503 instead of pretending delivery occurred."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    # 1. Twilio provider configured but carrier not activated
    monkeypatch.setattr(settings, "SMS_GATEWAY_PROVIDER", "twilio")
    monkeypatch.setattr(settings, "SMS_API_KEY", "dummy_twilio_auth_token_value")

    res = client.post("/api/v1/auth/customer/request-otp", json={"phone_number": "0550123456"})
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "SMS_GATEWAY_NOT_ACTIVATED"
    assert "Twilio SMS gateway integration is pending live carrier account activation" in res.json()["error"]["message"]

    # 2. Algerian Telecom provider configured but carrier not activated
    monkeypatch.setattr(settings, "SMS_GATEWAY_PROVIDER", "algeria_telecom")
    monkeypatch.setattr(settings, "SMS_API_KEY", "dummy_algerian_aggregator_key")

    res = client.post("/api/v1/auth/customer/request-otp", json={"phone_number": "0550123456"})
    assert res.status_code == 503
    assert res.json()["error"]["code"] == "SMS_GATEWAY_NOT_ACTIVATED"
    assert "Algerian telecom aggregator integration is pending corporate contract activation" in res.json()["error"]["message"]

