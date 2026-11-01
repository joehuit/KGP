"""Automated tests for Excel / XLSX product catalog import and preview."""

from decimal import Decimal
import io
from fastapi.testclient import TestClient
import openpyxl
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.product import Product


def _create_sample_excel() -> bytes:
    """Generate in-memory XLSX workbook with mixed valid, update, and invalid rows."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Spare Parts"

    # Multilingual header (French / Arabic / English compatible)
    ws.append(["Code", "Désignation", "Catégorie", "Prix", "Quantité", "Description"])

    # Row 1: Valid new product
    ws.append(["EXCEL-OLED-12", "Écran OLED iPhone 12", "Écrans", 16500.0, 15, "Grade AAA In-Cell"])

    # Row 2: Valid with Arabic category
    ws.append(["EXCEL-BAT-S21", "Batterie Samsung S21", "بطاريات", 3800.0, 25, "Original Service Pack"])

    # Row 3: Invalid price (negative)
    ws.append(["EXCEL-BAD-01", "Nappe Charge Type-C", "Connecteurs", -500.0, 10, "Defective row"])

    # Row 4: Duplicate SKU inside file
    ws.append(["EXCEL-OLED-12", "Duplicate entry", "Écrans", 16500.0, 5, "Duplicate SKU"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_excel_import_preview_workflow(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    """Test spreadsheet upload parses columns, detects errors, and returns preview."""
    # Ensure base category exists
    cat = Category(name="Écrans", display_order=1, is_active=True)
    db_session.add(cat)
    db_session.commit()

    file_bytes = _create_sample_excel()

    res = client.post(
        "/api/v1/products/import/preview",
        headers={"Authorization": f"Bearer {admin_token}"},
        files={"file": ("spare_parts.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["filename"] == "spare_parts.xlsx"
    assert data["total_rows"] == 4
    assert data["valid_count"] == 2
    assert data["invalid_count"] == 2
    assert "بطاريات" in data["new_categories"]

    # Verify detected errors on invalid rows
    invalid_rows = [r for r in data["rows"] if r["status"] == "invalid"]
    assert len(invalid_rows) == 2
    assert any("Price cannot be negative" in " ".join(r["errors"]) for r in invalid_rows)
    assert any("Duplicate SKU" in " ".join(r["errors"]) for r in invalid_rows)


def test_excel_import_commit_workflow(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    """Test committing validated rows creates new products and missing categories."""
    payload = {
        "items": [
            {
                "row_index": 2,
                "sku": "COMMIT-LCD-99",
                "name": "Écran Xiaomi Redmi Note 10",
                "category_name": "Écrans Xiaomi",
                "selling_price": "5200.00",
                "available_quantity": 30,
                "description": "Original",
                "status": "new",
                "errors": [],
            }
        ],
        "create_missing_categories": True,
        "update_existing_products": False,
    }

    res = client.post(
        "/api/v1/products/import/commit",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload,
    )
    assert res.status_code == 200
    summary = res.json()["data"]
    assert summary["created"] == 1
    assert summary["failed"] == 0

    # Verify product and category exist in DB
    created_prod = db_session.scalar(select(Product).where(Product.sku == "COMMIT-LCD-99"))
    assert created_prod is not None
    assert created_prod.name == "Écran Xiaomi Redmi Note 10"
    assert created_prod.category.name == "Écrans Xiaomi"


def test_excel_commit_tampered_payload_rejected_by_server_revalidation(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    """Test that client-submitted rows with invalid data (e.g. negative price, invalid SKU, duplicate batch SKU)
    are caught and rejected by server-side re-validation during commit, even if status is set to 'new'."""
    cat = Category(name="Connecteurs", display_order=2, is_active=True)
    db_session.add(cat)
    db_session.commit()

    tampered_payload = {
        "items": [
            {
                "row_index": 2,
                "sku": "TAMPER-01",
                "name": "Valid Name",
                "category_name": "Connecteurs",
                "selling_price": "-150.00",  # Negative price tampered by client
                "available_quantity": 10,
                "description": "Exploit attempt",
                "status": "new",  # Tampered status
                "errors": [],
            },
            {
                "row_index": 3,
                "sku": "INVALID SKU WITH SPACES",  # Bad format
                "name": "Another item",
                "category_name": "Connecteurs",
                "selling_price": "200.00",
                "available_quantity": 5,
                "description": None,
                "status": "new",
                "errors": [],
            },
            {
                "row_index": 4,
                "sku": "DUP-BATCH-01",
                "name": "First duplicate in batch",
                "category_name": "Connecteurs",
                "selling_price": "100.00",
                "available_quantity": 2,
                "status": "new",
                "errors": [],
            },
            {
                "row_index": 5,
                "sku": "DUP-BATCH-01",  # Duplicate SKU in same batch
                "name": "Second duplicate in batch",
                "category_name": "Connecteurs",
                "selling_price": "100.00",
                "available_quantity": 3,
                "status": "new",
                "errors": [],
            },
        ],
        "create_missing_categories": False,
        "update_existing_products": False,
    }

    res = client.post(
        "/api/v1/products/import/commit",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=tampered_payload,
    )
    assert res.status_code == 200
    summary = res.json()["data"]
    # 1 created (DUP-BATCH-01 first entry), 3 failed (negative price, invalid SKU, duplicate SKU)
    assert summary["created"] == 1
    assert summary["failed"] == 3
    assert any("Invalid price" in err for err in summary["errors"])
    assert any("Invalid SKU format" in err for err in summary["errors"])
    assert any("Duplicate SKU in commit payload" in err for err in summary["errors"])


def test_excel_formula_injection_sanitization(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    """Test that text fields starting with formula characters (=, +, -, @) are sanitized with prefix apostrophe."""
    payload = {
        "items": [
            {
                "row_index": 2,
                "sku": "INJECT-01",
                "name": "=cmd|' /C calc'!A0",  # Formula injection payload
                "category_name": "@AdminCategory",
                "selling_price": "500.00",
                "available_quantity": 10,
                "description": "+SUM(A1:A10)",
                "status": "new",
                "errors": [],
            }
        ],
        "create_missing_categories": True,
        "update_existing_products": False,
    }

    res = client.post(
        "/api/v1/products/import/commit",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload,
    )
    assert res.status_code == 200
    summary = res.json()["data"]
    assert summary["created"] == 1

    prod = db_session.scalar(select(Product).where(Product.sku == "INJECT-01"))
    assert prod is not None
    assert prod.name.startswith("'=")
    assert prod.description.startswith("'+")
    assert prod.category.name.startswith("'@")
