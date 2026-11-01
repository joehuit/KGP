"""Automated integration tests for Categories, Products, Customers, and Orders API routes.
Verifies business operations, administrative authorization, historical snapshotting,
and strict security boundaries.
"""

from decimal import Decimal
from fastapi.testclient import TestClient


def test_customer_registration_and_lookup_workflow(client: TestClient, admin_headers: dict):
    """Test public customer registration, validation, and authorized administrative phone lookup."""
    # 1. Register new customer (public allowed)
    payload = {
        "full_name": "Yacine Belkacem",
        "phone_number": "0661234567",
        "business_name": "Belkacem Phone Repair",
        "wilaya": "Oran",
        "address": "Zone Industrielle Es Senia",
    }
    create_res = client.post("/api/v1/customers", json=payload)
    assert create_res.status_code == 201
    cust = create_res.json()["data"]
    assert cust["id"] is not None
    assert cust["full_name"] == "Yacine Belkacem"
    assert cust["phone_number"] == "0661234567"

    # 2. Duplicate phone number rejected
    dup_res = client.post("/api/v1/customers", json=payload)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "CONFLICT"

    # 3. Public unauthenticated lookup by phone is rejected (PII privacy rule)
    unauth_lookup = client.get("/api/v1/customers/by-phone/0661234567")
    assert unauth_lookup.status_code == 401
    assert unauth_lookup.json()["error"]["code"] == "UNAUTHORIZED"

    # 4. Authorized admin lookup by phone succeeds
    lookup_res = client.get("/api/v1/customers/by-phone/0661234567", headers=admin_headers)
    assert lookup_res.status_code == 200
    assert lookup_res.json()["data"]["id"] == cust["id"]


def test_unauthorized_administrative_access_rejected(client: TestClient):
    """Security verification: Public callers cannot perform administrative operations."""
    # 1. Attempt category creation without admin credentials
    res1 = client.post("/api/v1/categories", json={"name": "Cameras", "display_order": 5})
    assert res1.status_code == 401
    assert res1.json()["error"]["code"] == "UNAUTHORIZED"

    # 2. Attempt product creation without admin credentials
    res2 = client.post(
        "/api/v1/products",
        json={"sku": "CAM-IPH-12", "name": "Camera", "category_id": 1, "selling_price": "9000.00"},
    )
    assert res2.status_code == 401
    assert res2.json()["error"]["code"] == "UNAUTHORIZED"

    # 3. Attempt order status change without admin credentials
    res3 = client.patch("/api/v1/orders/1/status", json={"status": "CONFIRMED"})
    assert res3.status_code == 401
    assert res3.json()["error"]["code"] == "UNAUTHORIZED"

    # 4. Attempt order status change with invalid admin credentials
    res4 = client.patch(
        "/api/v1/orders/1/status",
        json={"status": "CONFIRMED"},
        headers={"X-Admin-Key": "wrong_invalid_admin_secret_key_32_characters_long"},
    )
    assert res4.status_code == 403
    assert res4.json()["error"]["code"] == "FORBIDDEN"

    # 5. Public caller cannot list orders
    res5 = client.get("/api/v1/orders")
    assert res5.status_code == 401
    assert res5.json()["error"]["code"] == "UNAUTHORIZED"

    # 6. Public caller cannot retrieve arbitrary order by ID
    res6 = client.get("/api/v1/orders/1")
    assert res6.status_code == 401
    assert res6.json()["error"]["code"] == "UNAUTHORIZED"

    # 7. Public caller cannot retrieve customer profile by ID
    res7 = client.get("/api/v1/customers/1")
    assert res7.status_code == 401
    assert res7.json()["error"]["code"] == "UNAUTHORIZED"


def test_admin_auth_bridge_edge_cases(client: TestClient):
    """Test administrative authentication bridge edge cases: whitespace, weak keys, and bearer tokens."""
    # 1. Whitespace X-Admin-Key rejected with 401
    res_ws = client.post("/api/v1/categories", json={"name": "Test"}, headers={"X-Admin-Key": "   "})
    assert res_ws.status_code == 401

    # 2. Short / weak key (< 32 characters) rejected with 403
    res_short = client.post("/api/v1/categories", json={"name": "Test"}, headers={"X-Admin-Key": "admin"})
    assert res_short.status_code == 403

    # 3. Bearer header with empty token rejected with 401
    res_empty_bearer = client.post("/api/v1/categories", json={"name": "Test"}, headers={"Authorization": "Bearer "})
    assert res_empty_bearer.status_code == 401

    # 4. Bearer header with valid admin key accepted
    valid_key = "test_admin_api_key_minimum_32_characters_for_validation"
    res_bearer = client.post(
        "/api/v1/categories",
        json={"name": "Charging Ports", "display_order": 3},
        headers={"Authorization": f"Bearer {valid_key}"},
    )
    assert res_bearer.status_code == 201


def test_category_crud_workflow(client: TestClient, admin_headers: dict):
    """Test creating, listing, and retrieving product categories with proper authorization."""
    # 1. Create Category with admin credentials
    create_res = client.post(
        "/api/v1/categories",
        json={"name": "OLED Screens", "display_order": 1, "is_active": True},
        headers=admin_headers,
    )
    assert create_res.status_code == 201
    cat = create_res.json()["data"]
    assert cat["id"] is not None
    assert cat["name"] == "OLED Screens"
    cat_id = cat["id"]

    # 2. Duplicate Category rejected
    dup_res = client.post(
        "/api/v1/categories",
        json={"name": "OLED Screens", "display_order": 2},
        headers=admin_headers,
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "CONFLICT"

    # 3. List Categories (public catalog browsing allowed)
    list_res = client.get("/api/v1/categories")
    assert list_res.status_code == 200
    categories = list_res.json()["data"]
    assert len(categories) >= 1

    # 4. Get by ID (public catalog browsing allowed)
    get_res = client.get(f"/api/v1/categories/{cat_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["name"] == "OLED Screens"


def test_product_lifecycle_and_order_snapshotting(client: TestClient, admin_headers: dict):
    """Test creating products, placing an order, and verifying historical snapshot preservation."""
    # 1. Setup Category
    cat_res = client.post(
        "/api/v1/categories",
        json={"name": "Batteries", "display_order": 2},
        headers=admin_headers,
    )
    cat_id = cat_res.json()["data"]["id"]

    # 2. Setup Products with Algerian Dinar decimal pricing
    p1_res = client.post(
        "/api/v1/products",
        json={
            "sku": "BAT-IPH-13-ORIG",
            "name": "iPhone 13 Original Battery",
            "category_id": cat_id,
            "selling_price": "6500.00",
            "available_quantity": 40,
            "description": "High-capacity genuine OEM battery for iPhone 13",
        },
        headers=admin_headers,
    )
    assert p1_res.status_code == 201
    p1 = p1_res.json()["data"]
    p1_id = p1["id"]

    # 3. Register Customer via API
    cust_res = client.post(
        "/api/v1/customers",
        json={
            "full_name": "Mourad Ziti",
            "phone_number": "0770987654",
            "business_name": "Belfort Tech Repair",
            "wilaya": "Algiers",
        },
    )
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["data"]["id"]

    # 4. Place Order for 2 units (public customer allowed)
    order_res = client.post(
        "/api/v1/orders",
        json={
            "customer_id": cust_id,
            "customer_notes": "Urgent delivery to Belfort El Harrach",
            "items": [
                {"product_id": p1_id, "quantity": 2},
            ],
        },
    )
    assert order_res.status_code == 201
    order = order_res.json()["data"]
    assert order["order_reference"].startswith("KGP-")
    assert order["status"] == "PENDING"
    assert Decimal(str(order["total_amount"])) == Decimal("13000.00")
    assert len(order["items"]) == 1
    item = order["items"][0]
    assert item["product_name"] == "iPhone 13 Original Battery"
    assert item["product_sku"] == "BAT-IPH-13-ORIG"
    assert Decimal(str(item["unit_price"])) == Decimal("6500.00")
    assert item["quantity"] == 2
    assert Decimal(str(item["total_price"])) == Decimal("13000.00")

    # 5. Public unauthenticated order listing rejected (guessing customer_id blocked)
    unauth_orders = client.get(f"/api/v1/orders?customer_id={cust_id}")
    assert unauth_orders.status_code == 401

    # 6. Admin can list orders by customer_id
    admin_orders_res = client.get(f"/api/v1/orders?customer_id={cust_id}", headers=admin_headers)
    assert admin_orders_res.status_code == 200
    assert len(admin_orders_res.json()["data"]["items"]) == 1

    # 7. Admin can list all orders across business
    all_orders_res = client.get("/api/v1/orders", headers=admin_headers)
    assert all_orders_res.status_code == 200
    assert len(all_orders_res.json()["data"]["items"]) >= 1

    # 8. Reprice product to 8000.00 DZD
    patch_res = client.patch(
        f"/api/v1/products/{p1_id}",
        json={"selling_price": "8000.00", "name": "iPhone 13 Battery (Renamed)"},
        headers=admin_headers,
    )
    assert patch_res.status_code == 200

    # 9. Verify historical order line items are 100% UNCHANGED (Historical snapshotting rule)
    get_order_res = client.get(f"/api/v1/orders/{order['id']}", headers=admin_headers)
    assert get_order_res.status_code == 200
    unchanged_order = get_order_res.json()["data"]
    # Total remains 13000.00 DZD, NOT recalculated to 16000.00 DZD
    assert Decimal(str(unchanged_order["total_amount"])) == Decimal("13000.00")
    unchanged_item = unchanged_order["items"][0]
    assert unchanged_item["product_name"] == "iPhone 13 Original Battery"
    assert Decimal(str(unchanged_item["unit_price"])) == Decimal("6500.00")

    # 10. Test invalid state transition: PENDING directly to DELIVERED rejected
    invalid_trans_res = client.patch(
        f"/api/v1/orders/{order['id']}/status",
        json={"status": "DELIVERED"},
        headers=admin_headers,
    )
    assert invalid_trans_res.status_code == 422
    assert "Invalid order status transition" in invalid_trans_res.json()["error"]["message"]

    # 11. Test valid state transition: PENDING -> CONFIRMED
    status_res = client.patch(
        f"/api/v1/orders/{order['id']}/status",
        json={"status": "CONFIRMED"},
        headers=admin_headers,
    )
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"] == "CONFIRMED"


def test_order_duplicate_submission_prevention(client: TestClient, admin_headers: dict):
    """Test that submitting duplicate orders in rapid succession is rejected."""
    # 1. Setup Category & Product
    cat_res = client.post("/api/v1/categories", json={"name": "Connectors", "display_order": 4}, headers=admin_headers)
    cat_id = cat_res.json()["data"]["id"]
    p_res = client.post(
        "/api/v1/products",
        json={"sku": "FLEX-CHG-SAM-A12", "name": "A12 Charging Flex", "category_id": cat_id, "selling_price": "1200.00"},
        headers=admin_headers,
    )
    p_id = p_res.json()["data"]["id"]

    # 2. Register Customer
    c_res = client.post("/api/v1/customers", json={"full_name": "Tahar", "phone_number": "0551998877"})
    c_id = c_res.json()["data"]["id"]

    order_payload = {
        "customer_id": c_id,
        "customer_notes": "Urgent order for repair workshop",
        "items": [{"product_id": p_id, "quantity": 1}],
    }

    # 3. First submission succeeds
    first_res = client.post("/api/v1/orders", json=order_payload)
    assert first_res.status_code == 201

    # 4. Immediate second submission of identical order is rejected with 409 CONFLICT
    second_res = client.post("/api/v1/orders", json=order_payload)
    assert second_res.status_code == 409
    assert second_res.json()["error"]["code"] == "CONFLICT"
    assert "Duplicate order detected" in second_res.json()["error"]["message"]


def test_order_items_max_bound_enforced(client: TestClient):
    """Test that submitting an excessive number of line items (>50) is rejected."""
    excessive_items = [{"product_id": i, "quantity": 1} for i in range(1, 52)]
    payload = {
        "customer_id": 1,
        "items": excessive_items,
    }
    res = client.post("/api/v1/orders", json=payload)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
