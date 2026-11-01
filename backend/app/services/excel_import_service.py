"""Excel / XLSX spreadsheet parser and validator for bulk product catalog imports."""

from decimal import Decimal, InvalidOperation
import io
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import openpyxl
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.errors import ValidationError
from app.models.category import Category
from app.models.product import Product
from app.schemas.product import (
    ExcelImportCommitRequest,
    ExcelImportCommitSummary,
    ExcelImportPreviewResponse,
    ProductImportRow,
)


class ExcelImportService:
    """Service to parse, validate, preview, and commit Excel product catalogs."""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB maximum upload size
    MAX_IMPORT_ROWS = 5000            # 5,000 products per import batch

    @staticmethod
    def _sanitize_formula(val: Optional[str]) -> Optional[str]:
        """Neutralize potential CSV/spreadsheet formula injection triggers (=, +, -, @)."""
        if val is None:
            return None
        s = str(val).strip()
        if s and s[0] in ("=", "+", "-", "@"):
            return "'" + s
        return s

    # Multi-lingual header mappings (French, Arabic, English)
    HEADER_MAPPINGS = {
        "sku": [
            "sku", "code", "référence", "reference", "ref", "code article",
            "الرمز", "الكود", "رمز المنتج", "كود القطعة",
        ],
        "name": [
            "name", "nom", "désignation", "designation", "produit", "article", "libellé",
            "الاسم", "اسم المنتج", "السلعة", "القطعة", "تعيين",
        ],
        "category": [
            "category", "catégorie", "categorie", "famille", "type",
            "الفئة", "فئة", "التصنيف", "تصنيف", "النوع",
        ],
        "selling_price": [
            "price", "prix", "selling_price", "prix de vente", "pv", "tarif", "montant",
            "السعر", "سعر", "سعر البيع", "الثمن",
        ],
        "available_quantity": [
            "quantity", "quantité", "quantite", "stock", "qte", "qté", "disponible",
            "الكمية", "كمية", "المخزون", "الرصيد",
        ],
        "description": [
            "description", "détails", "details", "remarque", "notes", "observation",
            "الوصف", "وصف", "ملاحظات", "تفاصيل",
        ],
    }

    @classmethod
    def _detect_column_mapping(cls, headers: List[str]) -> Dict[str, Optional[str]]:
        """Map raw spreadsheet headers to standard product fields."""
        mapping: Dict[str, Optional[str]] = {
            "sku": None,
            "name": None,
            "category": None,
            "selling_price": None,
            "available_quantity": None,
            "description": None,
        }

        normalized_headers = {h.strip().lower(): h for h in headers if h}

        for field, variants in cls.HEADER_MAPPINGS.items():
            for variant in variants:
                for norm_h, original_h in normalized_headers.items():
                    if norm_h == variant or variant in norm_h:
                        if mapping[field] is None:
                            mapping[field] = original_h
                            break
                if mapping[field] is not None:
                    break

        return mapping

    @classmethod
    def parse_and_preview(
        cls,
        file_bytes: bytes,
        filename: str,
        db: Session,
        custom_mapping: Optional[Dict[str, str]] = None,
    ) -> ExcelImportPreviewResponse:
        """Parse uploaded XLSX spreadsheet and validate all rows against the database."""
        if len(file_bytes) > cls.MAX_FILE_SIZE:
            raise ValidationError(
                f"Spreadsheet file size ({len(file_bytes) / (1024 * 1024):.1f} MB) exceeds maximum allowed limit of {cls.MAX_FILE_SIZE // (1024 * 1024)} MB."
            )

        try:
            workbook = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        except Exception as exc:
            raise ValidationError(f"Invalid spreadsheet format. Please upload a valid .xlsx file: {str(exc)}")

        sheet = workbook.active
        if sheet is None:
            raise ValidationError("Spreadsheet contains no active sheets.")

        # Read rows
        rows_iter = sheet.iter_rows(values_only=True)
        try:
            first_row = next(rows_iter)
        except StopIteration:
            raise ValidationError("Spreadsheet is empty.")

        raw_headers = [str(cell).strip() if cell is not None else "" for cell in first_row]
        detected_columns = [h for h in raw_headers if h]

        mapping = custom_mapping or cls._detect_column_mapping(detected_columns)

        # Check required fields can be resolved
        required_fields = ["sku", "name", "selling_price"]
        missing_mappings = [f for f in required_fields if not mapping.get(f)]
        if missing_mappings:
            raise ValidationError(
                f"Could not map required columns: {', '.join(missing_mappings)}. "
                f"Spreadsheet columns found: {', '.join(detected_columns)}"
            )

        # Index existing database records for fast lookup
        existing_products = {p.sku.upper(): p for p in db.scalars(select(Product)).all()}
        existing_categories = {c.name.strip().lower(): c for c in db.scalars(select(Category)).all()}

        # Build column index lookup
        col_indices = {raw_headers[i]: i for i in range(len(raw_headers)) if raw_headers[i]}

        parsed_rows: List[ProductImportRow] = []
        seen_skus_in_file: Set[str] = set()
        new_categories: Set[str] = set()

        row_num = 1
        for row_data in rows_iter:
            row_num += 1
            if not any(cell is not None for cell in row_data):
                continue  # Skip completely empty rows

            if len(parsed_rows) >= cls.MAX_IMPORT_ROWS:
                raise ValidationError(
                    f"Spreadsheet exceeds maximum allowed limit of {cls.MAX_IMPORT_ROWS} rows. Please split the catalog into smaller files."
                )

            row_errors: List[str] = []

            # Extract cell by mapped header
            def get_val(field: str) -> Optional[Any]:
                header_name = mapping.get(field)
                if not header_name or header_name not in col_indices:
                    return None
                idx = col_indices[header_name]
                if idx < len(row_data):
                    return row_data[idx]
                return None

            raw_sku = str(get_val("sku") or "").strip().upper()
            raw_name = cls._sanitize_formula(str(get_val("name") or "").strip()) or ""
            raw_category = cls._sanitize_formula(str(get_val("category") or "").strip()) or "Général"
            raw_price = get_val("selling_price")
            raw_qty = get_val("available_quantity")
            raw_desc = cls._sanitize_formula(str(get_val("description") or "").strip()) or None

            # Validate SKU
            if not raw_sku:
                row_errors.append("Product code (SKU) is required.")
            elif not re.match(r"^[A-Z0-9_\-\./]+$", raw_sku):
                row_errors.append(f"Invalid SKU format '{raw_sku}'. Use alphanumeric characters, hyphens, slashes.")
            elif raw_sku in seen_skus_in_file:
                row_errors.append(f"Duplicate SKU '{raw_sku}' appears multiple times in this spreadsheet.")
            else:
                seen_skus_in_file.add(raw_sku)

            # Validate Name
            if not raw_name:
                row_errors.append("Product name is required.")
            elif len(raw_name) < 2:
                row_errors.append("Product name must be at least 2 characters long.")

            # Validate Price
            price_decimal = Decimal("0.00")
            if raw_price is None or str(raw_price).strip() == "":
                row_errors.append("Price is required.")
            else:
                try:
                    cleaned_price = str(raw_price).replace(",", ".").replace("DZD", "").replace("DA", "").strip()
                    price_decimal = Decimal(cleaned_price)
                    if price_decimal < Decimal("0.00"):
                        row_errors.append("Price cannot be negative.")
                    if price_decimal.as_tuple().exponent < -2:
                        row_errors.append("Price cannot exceed 2 decimal places.")
                except (InvalidOperation, ValueError):
                    row_errors.append(f"Invalid price value '{raw_price}'.")

            # Validate Quantity
            qty_int: Optional[int] = None
            if raw_qty is not None and str(raw_qty).strip() != "":
                try:
                    qty_int = int(float(str(raw_qty).strip()))
                    if qty_int < 0:
                        row_errors.append("Quantity cannot be negative.")
                except ValueError:
                    row_errors.append(f"Invalid quantity '{raw_qty}'. Must be an integer.")

            # Category check
            if raw_category.lower() not in existing_categories:
                new_categories.add(raw_category)

            # Determine status
            if row_errors:
                status = "invalid"
            elif raw_sku in existing_products:
                status = "update"
            else:
                status = "new"

            parsed_rows.append(
                ProductImportRow(
                    row_index=row_num,
                    sku=raw_sku,
                    name=raw_name,
                    category_name=raw_category,
                    selling_price=price_decimal,
                    available_quantity=qty_int,
                    description=raw_desc,
                    status=status,
                    errors=row_errors,
                )
            )

        valid_count = sum(1 for r in parsed_rows if r.status != "invalid")
        invalid_count = sum(1 for r in parsed_rows if r.status == "invalid")
        new_count = sum(1 for r in parsed_rows if r.status == "new")
        update_count = sum(1 for r in parsed_rows if r.status == "update")

        return ExcelImportPreviewResponse(
            filename=filename,
            detected_columns=detected_columns,
            column_mapping=mapping,
            total_rows=len(parsed_rows),
            valid_count=valid_count,
            invalid_count=invalid_count,
            new_products_count=new_count,
            update_products_count=update_count,
            new_categories=sorted(list(new_categories)),
            rows=parsed_rows,
        )

    @classmethod
    def commit_import(
        cls,
        db: Session,
        request: ExcelImportCommitRequest,
    ) -> ExcelImportCommitSummary:
        """Atomically commit validated spreadsheet rows into the product catalog with strict server-side re-validation."""
        if len(request.items) > cls.MAX_IMPORT_ROWS:
            raise ValidationError(
                f"Cannot commit more than {cls.MAX_IMPORT_ROWS} items in a single transaction (received {len(request.items)})."
            )

        summary = ExcelImportCommitSummary(
            total_processed=len(request.items),
            created=0,
            updated=0,
            skipped=0,
            failed=0,
            errors=[],
        )

        try:
            # Cache existing categories and products
            category_map = {c.name.strip().lower(): c for c in db.scalars(select(Category)).all()}
            product_map = {p.sku.upper(): p for p in db.scalars(select(Product)).all()}

            # 1. Handle missing categories
            if request.create_missing_categories:
                needed_cats = {
                    cls._sanitize_formula(item.category_name.strip())
                    for item in request.items
                    if item.category_name and item.category_name.strip()
                }
                for cat_name in needed_cats:
                    if cat_name and cat_name.lower() not in category_map:
                        new_cat = Category(name=cat_name, display_order=len(category_map) + 1, is_active=True)
                        db.add(new_cat)
                        db.flush()
                        category_map[cat_name.lower()] = new_cat

            # 2. Process rows with strict server-side re-validation
            seen_skus_in_payload: Set[str] = set()

            for item in request.items:
                if item.status == "invalid" or item.errors:
                    summary.failed += 1
                    summary.errors.append(f"Row {item.row_index} ({item.sku}): Skipped due to pre-existing errors.")
                    continue

                # Server-side validation of SKU
                sku = (item.sku or "").strip().upper()
                if not sku or len(sku) > 100 or not re.match(r"^[A-Z0-9_\-\./]+$", sku):
                    summary.failed += 1
                    summary.errors.append(f"Row {item.row_index}: Invalid SKU format '{sku}'.")
                    continue

                if sku in seen_skus_in_payload:
                    summary.failed += 1
                    summary.errors.append(f"Row {item.row_index} ({sku}): Duplicate SKU in commit payload.")
                    continue
                seen_skus_in_payload.add(sku)

                # Server-side validation of Name
                name = cls._sanitize_formula((item.name or "").strip())
                if not name or len(name) < 2 or len(name) > 255:
                    summary.failed += 1
                    summary.errors.append(f"Row {item.row_index} ({sku}): Product name must be between 2 and 255 characters.")
                    continue

                # Server-side validation of Price
                if item.selling_price is None or item.selling_price < Decimal("0.00") or item.selling_price.as_tuple().exponent < -2:
                    summary.failed += 1
                    summary.errors.append(f"Row {item.row_index} ({sku}): Invalid price '{item.selling_price}'.")
                    continue

                # Server-side validation of Quantity
                if item.available_quantity is not None and item.available_quantity < 0:
                    summary.failed += 1
                    summary.errors.append(f"Row {item.row_index} ({sku}): Quantity cannot be negative.")
                    continue

                # Server-side validation of Category
                cat_name = cls._sanitize_formula((item.category_name or "").strip()) or "Général"
                cat = category_map.get(cat_name.lower())
                if not cat:
                    summary.failed += 1
                    summary.errors.append(f"Row {item.row_index} ({sku}): Category '{cat_name}' not found.")
                    continue

                desc = cls._sanitize_formula(item.description.strip()) if item.description else None
                existing_prod = product_map.get(sku)

                if existing_prod:
                    if request.update_existing_products:
                        # Update product properties
                        existing_prod.name = name
                        existing_prod.category_id = cat.id
                        existing_prod.selling_price = item.selling_price
                        if item.available_quantity is not None:
                            existing_prod.available_quantity = item.available_quantity
                        if desc:
                            existing_prod.description = desc
                        existing_prod.is_active = True
                        summary.updated += 1
                    else:
                        # Intentionally skip existing product to preserve existing data
                        summary.skipped += 1
                else:
                    # Create brand new product
                    new_prod = Product(
                        sku=sku,
                        name=name,
                        category_id=cat.id,
                        selling_price=item.selling_price,
                        available_quantity=item.available_quantity,
                        description=desc,
                        is_active=True,
                    )
                    db.add(new_prod)
                    db.flush()
                    product_map[sku] = new_prod
                    summary.created += 1

            db.commit()
            return summary
        except Exception:
            db.rollback()
            raise
