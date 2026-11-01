"""Automated tests for Phase 4: Guest Checkout and Order Tracking (Zero Mandatory Registration)."""

from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.product import Product


def _setup_catalog(db: Session) -> Product:
    cat = Category(name="Écrans OLED", display_order=1, is_active=True)
    db.add(cat)
    db.flush()

    prod = Product(
        sku="TEST-GUEST-01",
        name="Écran Samsung Galaxy A52",
        category_id=cat.id,
        selling_price=Decimal("8500.00"),
        available_quantity=20,
        is_active=True,
    )
    db.add(prod)
    db.commit()
    return prod


def test_guest_order_creation_success(client: TestClient, db_session: Session):
    """Test guest customer can place an order directly without login or OTP."""
    prod = _setup_catalog(db_session)
    initial_stock = prod.available_quantity

    payload = {
        "full_name": "Karim Belfort",
        "phone_number": "0550123456",
        "wilaya": "16 - Alger",
        "commune": "El Harrach",
        "delivery_address": "Rue de Belfort, Atelier 14",
        "customer_notes": "Appeler avant la livraison",
        "items": [
            {
                "product_id": prod.id,
                "quantity": 2,
            }
        ],
    }

    res = client.post("/api/v1/orders/guest", json=payload)
    assert res.status_code == 201
    data = res.json()["data"]

    # Verify generated order details
    assert data["order_reference"].startswith("KGP-")
    assert len(data["tracking_token"]) >= 32
    assert data["status"] == "PENDING"
    assert data["total_amount"] == "17000.00"  # 8500.00 * 2
    assert data["customer_name"] == "Karim Belfort"
    assert data["customer_phone_masked"] == "0550****56"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_name"] == "Écran Samsung Galaxy A52"
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["unit_price"] == "8500.00"

    # Verify order and customer persisted in database
    order = db_session.scalar(select(Order).where(Order.order_reference == data["order_reference"]))
    assert order is not None
    assert order.status == OrderStatus.PENDING
    assert order.tracking_token == data["tracking_token"]

    cust = db_session.get(Customer, order.customer_id)
    assert cust is not None
    assert cust.phone_number == "0550123456"
    assert cust.full_name == "Karim Belfort"
    assert cust.wilaya == "16 - Alger"

    # Verify Stock Policy: inventory is NOT decremented automatically upon guest submission
    db_session.refresh(prod)
    assert prod.available_quantity == initial_stock


def test_guest_order_phone_normalization_and_validation(client: TestClient, db_session: Session):
    """Test Algerian phone number formatting and rejection of invalid formats."""
    prod = _setup_catalog(db_session)

    # 1. Valid +213 format normalized to 05...
    res_int = client.post(
        "/api/v1/orders/guest",
        json={
            "full_name": "Amina Tech",
            "phone_number": "+213 661 22 33 44",
            "wilaya": "31 - Oran",
            "commune": "Es Senia",
            "delivery_address": "Zone Industrielle",
            "items": [{"product_id": prod.id, "quantity": 1}],
        },
    )
    assert res_int.status_code == 201
    assert res_int.json()["data"]["customer_phone_masked"] == "0661****44"

    # 2. Invalid phone prefix (e.g. 021 landline or arbitrary numbers) rejected
    res_bad = client.post(
        "/api/v1/orders/guest",
        json={
            "full_name": "Invalid Phone",
            "phone_number": "021554433",  # Not a mobile 05/06/07
            "wilaya": "16 - Alger",
            "commune": "Alger Centre",
            "delivery_address": "Rue Didouche",
            "items": [{"product_id": prod.id, "quantity": 1}],
        },
    )
    assert res_bad.status_code == 422


def test_guest_order_empty_cart_and_inactive_product_rejected(client: TestClient, db_session: Session):
    """Test validation errors for empty cart and inactive product ordering."""
    prod = _setup_catalog(db_session)

    # 1. Empty items list
    res_empty = client.post(
        "/api/v1/orders/guest",
        json={
            "full_name": "Empty Cart Buyer",
            "phone_number": "0770112233",
            "wilaya": "25 - Constantine",
            "commune": "El Khroub",
            "delivery_address": "Centre",
            "items": [],
        },
    )
    assert res_empty.status_code == 422

    # 2. Inactive product
    prod.is_active = False
    db_session.commit()

    res_inactive = client.post(
        "/api/v1/orders/guest",
        json={
            "full_name": "Buyer Inactive",
            "phone_number": "0770112233",
            "wilaya": "25 - Constantine",
            "commune": "El Khroub",
            "delivery_address": "Centre",
            "items": [{"product_id": prod.id, "quantity": 1}],
        },
    )
    assert res_inactive.status_code == 422
    assert "inactive" in res_inactive.json()["error"]["message"].lower()


def test_guest_order_idempotency_protection(client: TestClient, db_session: Session):
    """Test duplicate network submissions with identical Idempotency-Key return cached response."""
    prod = _setup_catalog(db_session)
    idemp_key = "guest-idem-uuid-998877"

    payload = {
        "full_name": "Duplicate Tester",
        "phone_number": "0555889900",
        "wilaya": "19 - Sétif",
        "commune": "Ain Oulmene",
        "delivery_address": "Boutique GSM",
        "items": [{"product_id": prod.id, "quantity": 1}],
    }

    # First request
    res1 = client.post("/api/v1/orders/guest", json=payload, headers={"Idempotency-Key": idemp_key})
    assert res1.status_code == 201
    order_ref_1 = res1.json()["data"]["order_reference"]

    # Second request with same idempotency key
    res2 = client.post("/api/v1/orders/guest", json=payload, headers={"Idempotency-Key": idemp_key})
    assert res2.status_code == 201
    assert res2.headers.get("Idempotent-Replay") == "true"
    assert res2.json()["data"]["order_reference"] == order_ref_1


def test_guest_order_tracking_security(client: TestClient, db_session: Session):
    """Test guest order tracking by token succeeds, and unauthorized guesses fail."""
    prod = _setup_catalog(db_session)

    res = client.post(
        "/api/v1/orders/guest",
        json={
            "full_name": "Tracking Tester",
            "phone_number": "0555332211",
            "wilaya": "06 - Béjaïa",
            "commune": "Akbou",
            "delivery_address": "Atelier Réparation",
            "items": [{"product_id": prod.id, "quantity": 1}],
        },
    )
    assert res.status_code == 201
    tracking_token = res.json()["data"]["tracking_token"]

    # 1. Tracking with valid token succeeds
    track_res = client.get(f"/api/v1/orders/guest/track/{tracking_token}")
    assert track_res.status_code == 200
    track_data = track_res.json()["data"]
    assert track_data["status"] == "PENDING"
    assert track_data["customer_name"] == "Tracking Tester"
    assert track_data["customer_phone_masked"] == "0555****11"

    # 2. Tracking with bogus or guessed token returns 404
    bad_res = client.get("/api/v1/orders/guest/track/bogus-guessed-token-12345")
    assert bad_res.status_code == 404


def test_guest_orders_visible_to_admin_dashboard(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    """Test guest orders show up properly in the admin dashboard orders list."""
    prod = _setup_catalog(db_session)

    # Place guest order
    res = client.post(
        "/api/v1/orders/guest",
        json={
            "full_name": "Admin Visibility Check",
            "phone_number": "0666778899",
            "wilaya": "16 - Alger",
            "commune": "Bab Ezzouar",
            "delivery_address": "Cité 5 Juillet",
            "items": [{"product_id": prod.id, "quantity": 3}],
        },
    )
    assert res.status_code == 201
    guest_order_ref = res.json()["data"]["order_reference"]

    # Admin checks orders list
    admin_res = client.get(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 200
    items = admin_res.json()["data"]["items"]
    assert any(o["order_reference"] == guest_order_ref for o in items)


def test_post_tracking_endpoint_and_customer_privacy(client: TestClient, db_session: Session):
    """Test POST tracking endpoint and verify unauthenticated guest order does not corrupt registered customer profiles."""
    prod = _setup_catalog(db_session)

    # 1. Pre-register an existing customer account (e.g. registered repair shop)
    existing_shop = Customer(
        full_name="Atelier Pro Reparation",
        phone_number="0551998877",
        wilaya="16 - Alger",
        address="Rue Hassiba, Alger Centre",
        is_active=True,
    )
    db_session.add(existing_shop)
    db_session.commit()

    # 2. An unauthenticated guest places an order using that phone number but with a different recipient name and address
    guest_payload = {
        "full_name": "Employe Depot",
        "phone_number": "0551998877",
        "wilaya": "31 - Oran",
        "commune": "Es Senia",
        "delivery_address": "Zone Fret Hangar 3",
        "customer_notes": "Urgent livraison comptoir",
        "items": [{"product_id": prod.id, "quantity": 1}],
    }

    res = client.post("/api/v1/orders/guest", json=guest_payload)
    assert res.status_code == 201
    guest_data = res.json()["data"]
    tracking_token = guest_data["tracking_token"]

    # Verify the registered customer profile in DB was NOT overwritten or corrupted
    db_session.refresh(existing_shop)
    assert existing_shop.full_name == "Atelier Pro Reparation"
    assert existing_shop.wilaya == "16 - Alger"
    assert existing_shop.address == "Rue Hassiba, Alger Centre"

    # 3. Test POST tracking endpoint (bearer token in body, safe from URL proxy logging)
    track_post_res = client.post(
        "/api/v1/orders/guest/track",
        json={"tracking_token": tracking_token},
    )
    assert track_post_res.status_code == 200
    track_data = track_post_res.json()["data"]
    assert track_data["customer_name"] == "Employe Depot"
    assert track_data["wilaya"] == "31 - Oran"
    assert track_data["commune"] == "Es Senia"
    assert track_data["delivery_address"] == "Zone Fret Hangar 3"
    assert track_data["customer_notes"] == "Urgent livraison comptoir"
    assert track_data["customer_phone_masked"] == "0551****77"


def test_guest_order_deactivated_customer_account_rejected(client: TestClient, db_session: Session):
    """Test guest order placement with a deactivated account's phone number is rejected."""
    prod = _setup_catalog(db_session)

    banned_cust = Customer(
        full_name="Banned Account",
        phone_number="0559990011",
        wilaya="16 - Alger",
        address="Belfort",
        is_active=False,
    )
    db_session.add(banned_cust)
    db_session.commit()

    res = client.post(
        "/api/v1/orders/guest",
        json={
            "full_name": "Trying Again",
            "phone_number": "0559990011",
            "wilaya": "16 - Alger",
            "commune": "El Harrach",
            "delivery_address": "Belfort",
            "items": [{"product_id": prod.id, "quantity": 1}],
        },
    )
    assert res.status_code == 422
    assert "inactive" in res.json()["error"]["message"].lower()
