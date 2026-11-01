"""Automated tests for Order Ownership enforcement and IDOR defense."""

from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import create_access_token
from app.models.category import Category
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.product import Product


def test_customer_order_placement_derives_identity_from_token(
    client: TestClient,
    registered_customer: Customer,
    customer_token: str,
    db_session: Session,
):
    """Ensure client cannot spoof another customer's identity in order placement."""
    # 1. Create a second customer in DB
    victim_customer = Customer(
        full_name="Victim Customer",
        phone_number="0661998877",
        is_active=True,
    )
    db_session.add(victim_customer)

    cat = Category(name="Batteries", display_order=1, is_active=True)
    db_session.add(cat)
    db_session.commit()

    prod = Product(
        sku="BAT-TEST-1",
        name="Test Battery",
        category_id=cat.id,
        selling_price=Decimal("3000.00"),
        available_quantity=20,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()

    # 2. Authenticated customer submits order maliciously specifying victim_customer.id
    order_payload = {
        "customer_id": victim_customer.id,  # Attempted spoof
        "customer_notes": "Attempting identity spoof",
        "items": [{"product_id": prod.id, "quantity": 1}],
    }
    headers = {"Authorization": f"Bearer {customer_token}"}
    res = client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert res.status_code == 201
    order_data = res.json()["data"]

    # 3. Server MUST have overridden customer_id to registered_customer.id from the token
    assert order_data["customer_id"] == registered_customer.id
    assert order_data["customer_id"] != victim_customer.id


def test_customer_order_listing_strictly_scoped(
    client: TestClient,
    registered_customer: Customer,
    customer_token: str,
    admin_token: str,
    db_session: Session,
):
    """Ensure customers only see their own orders, and admins can view all."""
    # Create another customer
    other_customer = Customer(
        full_name="Other Shop",
        phone_number="0770554433",
        is_active=True,
    )
    db_session.add(other_customer)
    db_session.commit()

    # Create Order 1 for registered_customer
    order1 = Order(
        order_reference="KGP-ORD-1111",
        customer_id=registered_customer.id,
        status=OrderStatus.PENDING,
        total_amount=Decimal("5000.00"),
    )
    # Create Order 2 for other_customer
    order2 = Order(
        order_reference="KGP-ORD-2222",
        customer_id=other_customer.id,
        status=OrderStatus.PENDING,
        total_amount=Decimal("8000.00"),
    )
    db_session.add_all([order1, order2])
    db_session.commit()

    # 1. Customer queries /api/v1/orders
    cust_res = client.get(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert cust_res.status_code == 200
    cust_items = cust_res.json()["data"]["items"]

    # Customer only sees Order 1, NOT Order 2
    assert len(cust_items) == 1
    assert cust_items[0]["id"] == order1.id
    assert cust_items[0]["customer_id"] == registered_customer.id

    # 2. Customer tries to pass customer_id=other_customer.id in query string
    spoof_res = client.get(
        f"/api/v1/orders?customer_id={other_customer.id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert spoof_res.status_code == 200
    # Still only returns customer's own order (ignoring client filter)
    assert len(spoof_res.json()["data"]["items"]) == 1
    assert spoof_res.json()["data"]["items"][0]["id"] == order1.id

    # 3. Admin queries /api/v1/orders -> sees both orders
    admin_res = client.get(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 200
    assert len(admin_res.json()["data"]["items"]) == 2


def test_customer_cannot_inspect_other_customer_order(
    client: TestClient,
    customer_token: str,
    db_session: Session,
):
    """Ensure customer attempting to access another customer's order by ID receives 404 (IDOR defense)."""
    other_customer = Customer(
        full_name="Target Customer",
        phone_number="0660112233",
        is_active=True,
    )
    db_session.add(other_customer)
    db_session.commit()

    target_order = Order(
        order_reference="KGP-ORD-SECRET",
        customer_id=other_customer.id,
        status=OrderStatus.PENDING,
        total_amount=Decimal("12000.00"),
    )
    db_session.add(target_order)
    db_session.commit()

    # Authenticated customer attempts to view target_order.id
    res = client.get(
        f"/api/v1/orders/{target_order.id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    # Must return 404 to not disclose order existence
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"
