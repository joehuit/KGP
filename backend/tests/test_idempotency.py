"""Automated tests for persistent Idempotency-Key mechanism and duplicate submission prevention."""

from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.customer import Customer
from app.models.idempotency import IdempotencyKey
from app.models.order import Order
from app.models.product import Product


def test_idempotent_order_submission_workflow(
    client: TestClient,
    registered_customer: Customer,
    db_session: Session,
):
    """Test that Idempotency-Key safely handles network retries and rejects conflicting reuses."""
    # Setup Category and Product
    cat = Category(name="Charging Ports", display_order=1, is_active=True)
    db_session.add(cat)
    db_session.commit()

    prod = Product(
        sku="CHG-USB-C-SAM",
        name="Samsung USB-C Port",
        category_id=cat.id,
        selling_price=Decimal("450.00"),
        available_quantity=100,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()

    order_payload = {
        "customer_id": registered_customer.id,
        "customer_notes": "Urgent delivery",
        "items": [{"product_id": prod.id, "quantity": 2}],
    }
    idempotency_headers = {"Idempotency-Key": "client-uuid-test-12345-abcde"}

    # 1. First submission -> executes order creation
    first_res = client.post("/api/v1/orders", json=order_payload, headers=idempotency_headers)
    assert first_res.status_code == 201
    assert "Idempotent-Replay" not in first_res.headers
    order1 = first_res.json()["data"]
    order1_id = order1["id"]
    assert order1["order_reference"].startswith("KGP-")

    # Verify idempotency record persisted in database
    idemp_record = db_session.scalar(select(IdempotencyKey).where(IdempotencyKey.key == "client-uuid-test-12345-abcde"))
    assert idemp_record is not None
    assert idemp_record.response_code == 201

    # 2. Replay EXACT same request with identical Idempotency-Key
    replay_res = client.post("/api/v1/orders", json=order_payload, headers=idempotency_headers)
    assert replay_res.status_code == 201
    assert replay_res.headers.get("Idempotent-Replay") == "true"
    order2 = replay_res.json()["data"]
    assert order2["id"] == order1_id  # Returns the exact same order

    # Verify no duplicate orders created in database
    total_orders = len(db_session.scalars(select(Order).where(Order.customer_id == registered_customer.id)).all())
    assert total_orders == 1, f"Expected 1 order, found {total_orders}"

    # 3. Third request: SAME Idempotency-Key but DIFFERENT payload (quantity 5 instead of 2)
    conflicting_payload = {
        "customer_id": registered_customer.id,
        "customer_notes": "Changed note",
        "items": [{"product_id": prod.id, "quantity": 5}],
    }
    conflict_res = client.post("/api/v1/orders", json=conflicting_payload, headers=idempotency_headers)
    assert conflict_res.status_code == 409
    assert conflict_res.json()["error"]["code"] == "CONFLICT"
    assert "Idempotency key conflict" in conflict_res.json()["error"]["message"]


def test_concurrent_idempotent_order_submissions(
    client: TestClient,
    registered_customer: Customer,
    db_session: Session,
):
    """Ensure concurrent identical submissions with the same key do not create duplicate orders."""
    import concurrent.futures
    from tests.conftest import TestingSessionLocal
    from app.api.deps import get_db_session
    from app.main import app

    cat = Category(name="Batteries Concurrent", display_order=2, is_active=True)
    db_session.add(cat)
    db_session.commit()

    prod = Product(
        sku="BAT-CONCUR-1",
        name="Concurrent Test Battery",
        category_id=cat.id,
        selling_price=Decimal("1500.00"),
        available_quantity=50,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()

    payload = {
        "customer_id": registered_customer.id,
        "items": [{"product_id": prod.id, "quantity": 1}],
    }
    headers = {"Idempotency-Key": "concurrent-race-key-9999"}

    # In production, each request thread receives its own distinct DB session from the pool
    def per_request_db():
        s = TestingSessionLocal()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db_session] = per_request_db

    def make_request():
        return client.post("/api/v1/orders", json=payload, headers=headers)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_request) for _ in range(3)]
        results = [f.result() for f in futures]

    # Restore session override
    def restore_db():
        yield db_session
    app.dependency_overrides[get_db_session] = restore_db

    # All should return 201 (either original or idempotent replay)
    for res in results:
        assert res.status_code == 201

    # Exactly 1 order must exist in DB for this customer & SKU
    orders = db_session.scalars(select(Order).where(Order.customer_id == registered_customer.id)).all()
    matching_orders = [o for o in orders if any(it.product_sku == "BAT-CONCUR-1" for it in o.items)]
    assert len(matching_orders) == 1, f"Expected exactly 1 order, found {len(matching_orders)}"
