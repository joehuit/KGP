"""Automated tests for SQLAlchemy models, metadata constraints, and security helpers."""

from decimal import Decimal
import pytest
from sqlalchemy import Numeric, inspect
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.db.base import Base
from app.models.admin_user import AdminUser
from app.models.category import Category
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product


def test_all_eight_core_entities_registered_in_metadata():
    """Verify that all 8 core entities required by Section 4 are registered in SQLAlchemy metadata."""
    expected_tables = {
        "admin_users",
        "categories",
        "products",
        "customers",
        "orders",
        "order_items",
        "device_notification_tokens",
        "audit_logs",
    }
    actual_tables = set(Base.metadata.tables.keys())
    for table in expected_tables:
        assert table in actual_tables, f"Table '{table}' missing from SQLAlchemy metadata."


def test_numeric_currency_column_types():
    """Verify selling prices and totals use exact Numeric types rather than floating-point."""
    products_table = Base.metadata.tables["products"]
    assert isinstance(products_table.columns["selling_price"].type, Numeric)
    assert products_table.columns["selling_price"].type.precision == 12
    assert products_table.columns["selling_price"].type.scale == 2

    orders_table = Base.metadata.tables["orders"]
    assert isinstance(orders_table.columns["total_amount"].type, Numeric)
    assert orders_table.columns["total_amount"].type.precision == 14
    assert orders_table.columns["total_amount"].type.scale == 2

    order_items_table = Base.metadata.tables["order_items"]
    assert isinstance(order_items_table.columns["unit_price"].type, Numeric)
    assert isinstance(order_items_table.columns["total_price"].type, Numeric)


def test_order_item_foreign_key_ondelete_rules():
    """Verify order items use CASCADE on order_id and SET NULL on product_id to preserve history."""
    order_items_table = Base.metadata.tables["order_items"]
    fk_order = [fk for fk in order_items_table.foreign_keys if fk.column.table.name == "orders"][0]
    fk_product = [fk for fk in order_items_table.foreign_keys if fk.column.table.name == "products"][0]

    assert fk_order.ondelete == "CASCADE"
    assert fk_product.ondelete == "SET NULL"


def test_password_hashing_and_verification():
    """Verify bcrypt password hashing generates secure hashes and accurately verifies passwords."""
    raw_password = "SuperSecretKgpPassword2026!"
    hashed = get_password_hash(raw_password)

    assert hashed != raw_password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw_password, "") is False


def test_model_persistence_and_relations(db_session: Session):
    """Test creating and linking category, product, customer, and order in an isolated DB session."""
    # 1. Category
    cat = Category(name="Screens", display_order=1, is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    assert cat.id is not None

    # 2. Product
    prod = Product(
        sku="SCR-SAM-A51-BLK",
        name="Samsung Galaxy A51 OLED Screen",
        category_id=cat.id,
        selling_price=Decimal("14500.00"),
        available_quantity=25,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)
    assert prod.id is not None
    assert prod.selling_price == Decimal("14500.00")

    # 3. Customer
    customer = Customer(
        full_name="Ahmed Benali",
        phone_number="0550123456",
        business_name="Benali Mobile Repair",
        wilaya="Algiers",
        address="12 Rue Didouche Mourad",
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    assert customer.id is not None

    # 4. Order with snapshotting
    order = Order(
        order_reference="KGP-20261029-TEST",
        customer_id=customer.id,
        status=OrderStatus.PENDING,
        total_amount=Decimal("29000.00"),
        customer_notes="Please test before dispatch",
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    item = OrderItem(
        order_id=order.id,
        product_id=prod.id,
        product_name=prod.name,
        product_sku=prod.sku,
        unit_price=prod.selling_price,
        quantity=2,
        total_price=Decimal("29000.00"),
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert item.id is not None
    assert item.product_name == "Samsung Galaxy A51 OLED Screen"
    assert item.unit_price == Decimal("14500.00")
    assert item.total_price == Decimal("29000.00")
