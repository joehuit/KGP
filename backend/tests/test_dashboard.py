"""Automated tests for the main admin dashboard statistics endpoint."""

from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product


def test_dashboard_stats_endpoint(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    """Test dashboard stats returns accurate counts, revenue, and low-stock alerts."""
    # 1. Setup sample data
    cat = Category(name="Écrans Test", display_order=1, is_active=True)
    db_session.add(cat)
    db_session.flush()

    prod1 = Product(
        sku="TEST-LCD-01",
        name="Écran LCD A51",
        category_id=cat.id,
        selling_price=Decimal("4500.00"),
        available_quantity=2,  # Low stock <= 5
        is_active=True,
    )
    prod2 = Product(
        sku="TEST-LCD-02",
        name="Écran OLED S20",
        category_id=cat.id,
        selling_price=Decimal("12000.00"),
        available_quantity=20,  # Healthy stock
        is_active=True,
    )
    db_session.add_all([prod1, prod2])

    cust = Customer(
        full_name="Technicien Alger",
        phone_number="0550998877",
        business_name="Belfort Phone Clinic",
        wilaya="Alger",
        is_active=True,
    )
    db_session.add(cust)
    db_session.flush()

    order = Order(
        order_reference="ORD-DASH-001",
        customer_id=cust.id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("4500.00"),
    )
    db_session.add(order)
    db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=prod1.id,
        product_sku="TEST-LCD-01",
        product_name="Écran LCD A51",
        unit_price=Decimal("4500.00"),
        quantity=1,
        total_price=Decimal("4500.00"),
    )
    db_session.add(item)
    db_session.commit()

    # 2. Call dashboard endpoint
    res = client.get(
        "/api/v1/dashboard/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["total_products"] >= 2
    assert data["total_categories"] >= 1
    assert data["total_customers"] >= 1
    assert data["total_orders"] >= 1
    assert data["confirmed_orders"] >= 1
    assert float(data["total_revenue"]) >= 4500.0
    assert data["low_stock_count"] >= 1

    # Verify low stock product is listed
    low_skus = [p["sku"] for p in data["low_stock_products"]]
    assert "TEST-LCD-01" in low_skus
