"""Product catalog API endpoints."""

from math import ceil
from typing import Optional
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from sqlalchemy.orm import Session
from app.api.deps import PaginationParams, get_db_session, require_roles
from app.core.security import AdminRole
from app.models.admin_user import AdminUser
from app.schemas.common import PaginatedResponse, PaginationMeta, ResponseEnvelope
from app.schemas.product import (
    ExcelImportCommitRequest,
    ExcelImportCommitSummary,
    ExcelImportPreviewResponse,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.services.audit_service import AuditService
from app.models.audit_log import AuditActorType
from app.services.excel_import_service import ExcelImportService
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ResponseEnvelope[PaginatedResponse[ProductResponse]])
def list_products(
    category_id: Optional[int] = Query(None, description="Filter products by category ID"),
    search: Optional[str] = Query(None, description="Search products by SKU or name"),
    active_only: bool = Query(True, description="Filter active products only"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[PaginatedResponse[ProductResponse]]:
    """List products with optional search, category filtering, and pagination (public catalog operation)."""
    items, total = ProductService.list_products(
        db=db,
        page=pagination.page,
        page_size=pagination.page_size,
        category_id=category_id,
        search=search,
        active_only=active_only,
    )

    total_pages = ceil(total / pagination.page_size) if total > 0 else 0
    paginated_data = PaginatedResponse[ProductResponse](
        items=[ProductResponse.model_validate(p) for p in items],
        meta=PaginationMeta(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )
    return ResponseEnvelope(data=paginated_data)


@router.post("", response_model=ResponseEnvelope[ProductResponse], status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[ProductResponse]:
    """Create a new spare-parts catalog product (privileged administrative operation)."""
    product = ProductService.create_product(db=db, data=data)
    return ResponseEnvelope(
        data=ProductResponse.model_validate(product),
        message="Product created successfully.",
    )


@router.post("/import/preview", response_model=ResponseEnvelope[ExcelImportPreviewResponse])
async def preview_excel_import(
    file: UploadFile = File(..., description="Uploaded .xlsx spreadsheet"),
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[ExcelImportPreviewResponse]:
    """Parse and validate Excel product catalog without saving (preview step)."""
    contents = await file.read()
    preview = ExcelImportService.parse_and_preview(
        file_bytes=contents,
        filename=file.filename or "import.xlsx",
        db=db,
    )
    return ResponseEnvelope(
        data=preview,
        message=f"Spreadsheet parsed: {preview.valid_count} valid rows, {preview.invalid_count} errors.",
    )


@router.post("/import/commit", response_model=ResponseEnvelope[ExcelImportCommitSummary])
def commit_excel_import(
    payload: ExcelImportCommitRequest,
    request: Request,
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[ExcelImportCommitSummary]:
    """Atomically commit validated spreadsheet rows into the product catalog."""
    summary = ExcelImportService.commit_import(db=db, request=payload)
    client_ip = request.client.host if request.client else "unknown"

    # Log audit trail event
    AuditService.log_event(
        db=db,
        actor_type=AuditActorType.ADMIN,
        actor_id=str(_admin.id),
        action="EXCEL_IMPORT",
        entity_type="PRODUCT",
        entity_id=None,
        details={
            "created": summary.created,
            "updated": summary.updated,
            "skipped": summary.skipped,
            "failed": summary.failed,
        },
        ip_address=client_ip,
    )

    return ResponseEnvelope(
        data=summary,
        message=f"Import complete: {summary.created} created, {summary.updated} updated, {summary.skipped} skipped.",
    )


@router.get("/{product_id}", response_model=ResponseEnvelope[ProductResponse])
def get_product(
    product_id: int,
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[ProductResponse]:
    """Retrieve single product details (public catalog operation)."""
    product = ProductService.get_product_by_id(db=db, product_id=product_id)
    return ResponseEnvelope(data=ProductResponse.model_validate(product))


@router.patch("/{product_id}", response_model=ResponseEnvelope[ProductResponse])
def update_product(
    product_id: int,
    data: ProductUpdate,
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[ProductResponse]:
    """Update product information, price, or stock (privileged administrative operation)."""
    product = ProductService.update_product(db=db, product_id=product_id, data=data)
    db.commit()
    return ResponseEnvelope(
        data=ProductResponse.model_validate(product),
        message="Product updated successfully.",
    )


@router.delete("/{product_id}", response_model=ResponseEnvelope[dict])
def delete_product(
    product_id: int,
    request: Request,
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[dict]:
    """Safely delete product or deactivate if historical orders exist."""
    result = ProductService.delete_product(db=db, product_id=product_id)
    client_ip = request.client.host if request.client else "unknown"

    AuditService.log_event(
        db=db,
        actor_type=AuditActorType.ADMIN,
        actor_id=str(_admin.id),
        action="DELETE" if result["deleted"] else "DEACTIVATE",
        entity_type="PRODUCT",
        entity_id=str(product_id),
        details={"result": result},
        ip_address=client_ip,
    )

    return ResponseEnvelope(
        data=result,
        message=result["message"],
    )

