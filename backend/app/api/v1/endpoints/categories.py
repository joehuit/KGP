"""Category management API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_db_session, require_roles
from app.core.errors import ConflictError, NotFoundError
from app.core.security import AdminRole
from app.models.admin_user import AdminUser
from app.models.audit_log import AuditActorType
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.common import ResponseEnvelope
from app.services.audit_service import AuditService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=ResponseEnvelope[List[CategoryResponse]])
def list_categories(
    db: Session = Depends(get_db_session),
    active_only: bool = True,
) -> ResponseEnvelope[List[CategoryResponse]]:
    """List product categories ordered by display_order (public catalog operation)."""
    query = select(Category)
    if active_only:
        query = query.where(Category.is_active.is_(True))
    categories = list(db.scalars(query.order_by(Category.display_order.asc(), Category.name.asc())).all())
    return ResponseEnvelope(data=categories)


@router.post("", response_model=ResponseEnvelope[CategoryResponse], status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[CategoryResponse]:
    """Create a new product category (privileged administrative operation)."""
    existing = db.scalar(select(Category).where(Category.name == data.name))
    if existing:
        raise ConflictError(f"Category with name '{data.name}' already exists.")

    category = Category(
        name=data.name,
        display_order=data.display_order,
        is_active=data.is_active,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return ResponseEnvelope(
        data=category,
        message="Category created successfully.",
    )


@router.get("/{category_id}", response_model=ResponseEnvelope[CategoryResponse])
def get_category(
    category_id: int,
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[CategoryResponse]:
    """Retrieve category by ID (public catalog operation)."""
    category = db.get(Category, category_id)
    if not category:
        raise NotFoundError(f"Category with ID {category_id} not found.")
    return ResponseEnvelope(data=category)


@router.patch("/{category_id}", response_model=ResponseEnvelope[CategoryResponse])
def update_category(
    category_id: int,
    data: CategoryUpdate,
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[CategoryResponse]:
    """Update category properties (privileged administrative operation)."""
    category = db.get(Category, category_id)
    if not category:
        raise NotFoundError(f"Category with ID {category_id} not found.")

    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] is not None:
        conflict = db.scalar(
            select(Category).where(Category.name == update_data["name"], Category.id != category_id)
        )
        if conflict:
            raise ConflictError(f"Category with name '{update_data['name']}' already exists.")

    for field, val in update_data.items():
        setattr(category, field, val)

    db.commit()
    db.refresh(category)
    return ResponseEnvelope(data=category, message="Category updated successfully.")


@router.delete("/{category_id}", response_model=ResponseEnvelope[dict])
def delete_category(
    category_id: int,
    request: Request,
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[dict]:
    """Delete a category only if no products are assigned to it."""
    category = db.get(Category, category_id)
    if not category:
        raise NotFoundError(f"Category with ID {category_id} not found.")

    # Check for assigned products
    product_count = db.scalar(
        select(func.count()).select_from(Product).where(Product.category_id == category_id)
    ) or 0

    if product_count > 0:
        raise ConflictError(
            f"Cannot delete category '{category.name}' because {product_count} product(s) are assigned to it. "
            "Please reassign or delete those products first."
        )

    db.delete(category)
    db.commit()

    client_ip = request.client.host if request.client else "unknown"
    AuditService.log_event(
        db=db,
        actor_type=AuditActorType.ADMIN,
        actor_id=str(_admin.id),
        action="DELETE",
        entity_type="CATEGORY",
        entity_id=str(category_id),
        details={"name": category.name},
        ip_address=client_ip,
    )

    return ResponseEnvelope(
        data={"deleted": True, "category_id": category_id},
        message=f"Category '{category.name}' deleted successfully.",
    )

