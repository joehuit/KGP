"""Automated tests for Role-Based Access Control (RBAC).

Tests explicitly verify allowed and forbidden operations across all three roles:
- superadmin
- admin
- operator
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.product import Product


def test_superadmin_full_access(client: TestClient, superadmin_token: str):
    """Superadmin has unrestricted access: catalog management and admin user management."""
    headers = {"Authorization": f"Bearer {superadmin_token}"}

    # 1. Superadmin can list admin users
    users_res = client.get("/api/v1/admin/users", headers=headers)
    assert users_res.status_code == 200

    # 2. Superadmin can provision new admin users
    create_user_res = client.post(
        "/api/v1/admin/users",
        json={
            "email": "new_operator@kgp-test.dz",
            "password": "SecurePassword123!",
            "full_name": "New Warehouse Staff",
            "role": "operator",
            "is_active": True,
        },
        headers=headers,
    )
    assert create_user_res.status_code == 201
    assert create_user_res.json()["data"]["role"] == "operator"

    # 3. Superadmin can create categories
    cat_res = client.post(
        "/api/v1/categories",
        json={"name": "Tools & Soldering", "display_order": 10},
        headers=headers,
    )
    assert cat_res.status_code == 201


def test_admin_role_permissions(client: TestClient, admin_token: str):
    """Admin role can manage catalog and orders, but is FORBIDDEN from admin user management."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Allowed: Admin can create product categories
    cat_res = client.post(
        "/api/v1/categories",
        json={"name": "Microscopes", "display_order": 11},
        headers=headers,
    )
    assert cat_res.status_code == 201

    # 2. Forbidden: Admin CANNOT list admin users (403 Forbidden)
    users_res = client.get("/api/v1/admin/users", headers=headers)
    assert users_res.status_code == 403
    assert users_res.json()["error"]["code"] == "FORBIDDEN"

    # 3. Forbidden: Admin CANNOT create new admin users (403 Forbidden)
    create_user_res = client.post(
        "/api/v1/admin/users",
        json={
            "email": "rogue_user@kgp-test.dz",
            "password": "Password123!",
            "full_name": "Rogue User",
            "role": "admin",
        },
        headers=headers,
    )
    assert create_user_res.status_code == 403
    assert create_user_res.json()["error"]["code"] == "FORBIDDEN"


def test_operator_role_permissions(
    client: TestClient,
    operator_token: str,
    db_session: Session,
):
    """Operator role can inspect catalog and update order status,
    but is FORBIDDEN from modifying the product catalog or managing users.
    """
    headers = {"Authorization": f"Bearer {operator_token}"}

    # Setup: Existing Category, Product, Customer, and Order
    cat = Category(name="LCD Screens", display_order=1, is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)

    cust = Customer(full_name="Brahim", phone_number="0550001122", is_active=True)
    db_session.add(cust)
    db_session.commit()
    db_session.refresh(cust)

    order = Order(
        order_reference="KGP-TEST-OP-1",
        customer_id=cust.id,
        status=OrderStatus.PENDING,
        total_amount=5000,
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    # 1. Allowed: Operator can read categories
    cat_list_res = client.get("/api/v1/categories", headers=headers)
    assert cat_list_res.status_code == 200

    # 2. Allowed: Operator can update order lifecycle status
    status_res = client.patch(
        f"/api/v1/orders/{order.id}/status",
        json={"status": "CONFIRMED"},
        headers=headers,
    )
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"] == "CONFIRMED"

    # 3. Forbidden: Operator CANNOT create categories
    create_cat_res = client.post(
        "/api/v1/categories",
        json={"name": "Operator Category", "display_order": 99},
        headers=headers,
    )
    assert create_cat_res.status_code == 403
    assert create_cat_res.json()["error"]["code"] == "FORBIDDEN"

    # 4. Forbidden: Operator CANNOT create products
    create_prod_res = client.post(
        "/api/v1/products",
        json={
            "sku": "OP-PROD-1",
            "name": "Operator Product",
            "category_id": cat.id,
            "selling_price": "1000.00",
        },
        headers=headers,
    )
    assert create_prod_res.status_code == 403
    assert create_prod_res.json()["error"]["code"] == "FORBIDDEN"

    # 5. Forbidden: Operator CANNOT access admin user management
    users_res = client.get("/api/v1/admin/users", headers=headers)
    assert users_res.status_code == 403
    assert users_res.json()["error"]["code"] == "FORBIDDEN"
