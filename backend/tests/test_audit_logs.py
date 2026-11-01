"""Automated tests for audit log inspection and system settings endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.audit_log import AuditActorType
from app.services.audit_service import AuditService


def test_audit_logs_endpoint_superadmin_only(
    client: TestClient,
    superadmin_token: str,
    admin_token: str,
    db_session: Session,
):
    """Test audit log listing is strictly reserved for Superadmin."""
    # 1. Create a sample audit log entry
    AuditService.log_event(
        db=db_session,
        actor_type=AuditActorType.ADMIN,
        actor_id="1",
        action="TEST_ACTION",
        entity_type="PRODUCT",
        entity_id="99",
        details={"reason": "test"},
    )

    # 2. Regular admin forbidden (403)
    admin_res = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 403

    # 3. Superadmin allowed (200)
    super_res = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert super_res.status_code == 200
    data = super_res.json()["data"]
    assert data["meta"]["total_items"] >= 1
    assert any(log["action"] == "TEST_ACTION" for log in data["items"])


def test_system_settings_endpoint(
    client: TestClient,
    admin_token: str,
):
    """Test system settings returns safe metadata and Algerian wilayas without secrets."""
    res = client.get(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["currency"] == "DZD"
    assert data["currency_symbol"] == "د.ج"
    assert len(data["supported_wilayas"]) == 58
    assert "SECRET_KEY" not in data
    assert "ADMIN_API_KEY" not in data


def test_audit_log_created_on_customer_and_order_updates(
    client: TestClient,
    admin_token: str,
    superadmin_token: str,
    db_session: Session,
):
    """Test that customer updates and order status changes automatically generate audit log records."""
    from decimal import Decimal
    from app.models.customer import Customer
    from app.models.category import Category
    from app.models.product import Product
    from app.models.order import Order, OrderStatus
    from app.models.order_item import OrderItem

    # 1. Setup Customer and Order
    cust = Customer(
        full_name="Audit Test Client",
        phone_number="0555998877",
        business_name="Audit Repair Workshop",
        wilaya="16 - Alger",
        is_active=True,
    )
    db_session.add(cust)
    db_session.flush()

    cat = Category(name="Audit Parts", display_order=1, is_active=True)
    db_session.add(cat)
    db_session.flush()

    prod = Product(
        sku="AUDIT-PART-01",
        name="Audit LCD Screen",
        category_id=cat.id,
        selling_price=Decimal("4500.00"),
        available_quantity=10,
        is_active=True,
    )
    db_session.add(prod)
    db_session.flush()

    order = Order(
        order_reference="ORD-AUDIT-001",
        customer_id=cust.id,
        status=OrderStatus.PENDING,
        total_amount=Decimal("4500.00"),
        customer_notes="Belfort El Harrach",
    )
    db_session.add(order)
    db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=prod.id,
        product_sku="AUDIT-PART-01",
        product_name="Audit LCD Screen",
        quantity=1,
        unit_price=Decimal("4500.00"),
        total_price=Decimal("4500.00"),
    )
    db_session.add(item)
    db_session.commit()

    # 2. Update Customer
    cust_res = client.patch(
        f"/api/v1/customers/{cust.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"business_name": "Updated Audit Shop"},
    )
    assert cust_res.status_code == 200

    # 3. Update Order Status
    order_res = client.patch(
        f"/api/v1/orders/{order.id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "CONFIRMED"},
    )
    assert order_res.status_code == 200

    # 4. Superadmin inspects audit logs
    audit_res = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert audit_res.status_code == 200
    logs = audit_res.json()["data"]["items"]

    # Verify customer audit event exists
    cust_logs = [l for l in logs if l["entity_type"] == "CUSTOMER" and l["entity_id"] == str(cust.id)]
    assert len(cust_logs) >= 1
    assert cust_logs[0]["action"] == "UPDATE"

    # Verify order audit event exists
    order_logs = [l for l in logs if l["entity_type"] == "ORDER" and l["entity_id"] == str(order.id)]
    assert len(order_logs) >= 1
    assert order_logs[0]["action"] == "STATUS_UPDATE"
    assert order_logs[0]["details"]["new_status"] == "CONFIRMED"
