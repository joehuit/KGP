"""Automated tests for safe category and product deletion semantics."""

from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product


def test_category_deletion_blocked_when_products_exist(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    """Category deletion must be rejected with 409 Conflict if products are assigned."""
    cat = Category(name="Category With Prods", display_order=10, is_active=True)
    db_session.add(cat)
    db_session.flush()

    prod = Product(
        sku="CAT-DEL-01",
        name="Assigned Product",
        category_id=cat.id,
        selling_price=Decimal("1500.00"),
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()

    # Attempt delete
    res = client.delete(
        f"/api/v1/categories/{cat.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 409
    assert "Cannot delete category" in res.json()["error"]["message"]


def test_category_deletion_succeeds_when_empty(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    """Category deletion succeeds if no products are assigned."""
    empty_cat = Category(name="Empty Category", display_order=99, is_active=True)
    db_session.add(empty_cat)
    db_session.commit()

    res = client.delete(
        f"/api/v1/categories/{empty_cat.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["deleted"] is True


def test_product_deletion_deactivates_if_historical_orders_exist(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    """Product with orders must be soft-deactivated instead of destroyed."""
    cat = Category(name="Cat Orders", display_order=1, is_active=True)
    db_session.add(cat)
    db_session.flush()

    prod = Product(
        sku="PROD-WITH-ORDERS",
        name="Ordered Screen",
        category_id=cat.id,
        selling_price=Decimal("2000.00"),
        is_active=True,
    )
    cust = Customer(
        full_name="Technician 1",
        phone_number="0661122334",
        is_active=True,
    )
    db_session.add_all([prod, cust])
    db_session.flush()

    order = Order(
        order_reference="ORD-DEL-TEST",
        customer_id=cust.id,
        status=OrderStatus.PENDING,
        total_amount=Decimal("2000.00"),
    )
    db_session.add(order)
    db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=prod.id,
        product_sku="PROD-WITH-ORDERS",
        product_name="Ordered Screen",
        unit_price=Decimal("2000.00"),
        quantity=1,
        total_price=Decimal("2000.00"),
    )
    db_session.add(item)
    db_session.commit()

    # Attempt delete
    res = client.delete(
        f"/api/v1/products/{prod.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["deleted"] is False
    assert res.json()["data"]["deactivated"] is True

    # Verify product is deactivated in DB
    db_session.refresh(prod)
    assert prod.is_active is False
