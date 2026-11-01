"""Automated tests for administrative customer management and order history."""

from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.order import Order, OrderStatus


def test_admin_customer_listing_and_filtering(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    """Test administrator can list and search customers by name, phone, or wilaya."""
    c1 = Customer(
        full_name="Belfort Mobile Shop",
        phone_number="0770112233",
        business_name="Belfort Store",
        wilaya="Alger",
        is_active=True,
    )
    c2 = Customer(
        full_name="Oran Tech Repair",
        phone_number="0660445566",
        business_name="Oran Tech",
        wilaya="Oran",
        is_active=True,
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    # 1. Non-admin forbidden
    unauth_res = client.get("/api/v1/customers")
    assert unauth_res.status_code == 401

    # 2. Admin list
    res = client.get(
        "/api/v1/customers",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["meta"]["total_items"] >= 2

    # 3. Search filter
    search_res = client.get(
        "/api/v1/customers?search=Oran",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert search_res.status_code == 200
    search_items = search_res.json()["data"]["items"]
    assert any("Oran" in c["full_name"] for c in search_items)


def test_admin_customer_order_history(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    """Test retrieving orders placed by a specific customer."""
    cust = Customer(full_name="Order History Cust", phone_number="0550334455", is_active=True)
    db_session.add(cust)
    db_session.flush()

    o1 = Order(order_reference="ORD-HIST-01", customer_id=cust.id, status=OrderStatus.PENDING, total_amount=Decimal("1500.00"))
    o2 = Order(order_reference="ORD-HIST-02", customer_id=cust.id, status=OrderStatus.DELIVERED, total_amount=Decimal("3000.00"))
    db_session.add_all([o1, o2])
    db_session.commit()

    res = client.get(
        f"/api/v1/customers/{cust.id}/orders",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) == 2
    refs = [o["order_reference"] for o in items]
    assert "ORD-HIST-01" in refs
    assert "ORD-HIST-02" in refs
