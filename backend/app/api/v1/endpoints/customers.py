"""Customer registration and profile API endpoints."""

from math import ceil
import re
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.api.deps import (
    PaginationParams,
    get_current_customer,
    get_db_session,
    require_roles,
)
from app.core.errors import ConflictError, NotFoundError
from app.core.rate_limit import enforce_rate_limit
from app.core.security import AdminRole
from app.models.admin_user import AdminUser
from app.models.audit_log import AuditActorType
from app.models.customer import Customer
from app.schemas.common import PaginatedResponse, PaginationMeta, ResponseEnvelope
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.schemas.order import OrderResponse
from app.services.audit_service import AuditService
from app.services.order_service import OrderService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=ResponseEnvelope[CustomerResponse], status_code=status.HTTP_201_CREATED)
def register_customer(
    data: CustomerCreate,
    request: Request,
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[CustomerResponse]:
    """Register a new repair shop technician or retail spare-parts customer.
    Rate limited to 10 registrations per minute per IP.
    """
    client_ip = request.client.host if request.client else "unknown"
    enforce_rate_limit(key=f"cust_reg:{client_ip}", limit=10, window_seconds=60, action_name="customer registration")

    # Check phone number uniqueness
    existing = db.scalar(select(Customer).where(Customer.phone_number == data.phone_number))
    if existing:
        raise ConflictError(f"A customer account with phone number '{data.phone_number}' is already registered.")

    customer = Customer(
        full_name=data.full_name,
        phone_number=data.phone_number,
        business_name=data.business_name,
        wilaya=data.wilaya,
        address=data.address,
        is_active=data.is_active,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return ResponseEnvelope(
        data=CustomerResponse.model_validate(customer),
        message="Customer registered successfully.",
    )


@router.get("", response_model=ResponseEnvelope[PaginatedResponse[CustomerResponse]])
def list_customers(
    search: Optional[str] = Query(None, description="Search by name, phone, wilaya, or business name"),
    wilaya: Optional[str] = Query(None, description="Filter by Algerian wilaya"),
    active_only: bool = Query(False, description="Filter active customers only"),
    pagination: PaginationParams = Depends(),
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[PaginatedResponse[CustomerResponse]]:
    """List registered customers with search and pagination (Admin only)."""
    query = select(Customer)

    if active_only:
        query = query.where(Customer.is_active.is_(True))

    if wilaya:
        query = query.where(Customer.wilaya == wilaya)

    if search:
        search_term = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(Customer.full_name).like(search_term),
                func.lower(Customer.phone_number).like(search_term),
                func.lower(Customer.business_name).like(search_term),
                func.lower(Customer.wilaya).like(search_term),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    total_pages = ceil(total / pagination.page_size) if total > 0 else 0
    offset = (pagination.page - 1) * pagination.page_size

    customers = list(
        db.scalars(
            query.order_by(Customer.created_at.desc()).offset(offset).limit(pagination.page_size)
        ).all()
    )

    paginated_data = PaginatedResponse[CustomerResponse](
        items=[CustomerResponse.model_validate(c) for c in customers],
        meta=PaginationMeta(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )
    return ResponseEnvelope(data=paginated_data)


@router.get("/me", response_model=ResponseEnvelope[CustomerResponse])
def get_my_customer_profile(
    current_customer: Customer = Depends(get_current_customer),
) -> ResponseEnvelope[CustomerResponse]:
    """Retrieve current authenticated customer profile."""
    return ResponseEnvelope(data=CustomerResponse.model_validate(current_customer))


@router.get("/{customer_id}", response_model=ResponseEnvelope[CustomerResponse])
def get_customer_by_id(
    customer_id: int,
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[CustomerResponse]:
    """Retrieve customer profile by ID (privileged administrative operation).
    Public callers cannot query personal customer details.
    """
    customer = db.get(Customer, customer_id)
    if not customer:
        raise NotFoundError(f"Customer with ID {customer_id} not found.")
    return ResponseEnvelope(data=CustomerResponse.model_validate(customer))


@router.get("/by-phone/{phone_number}", response_model=ResponseEnvelope[CustomerResponse])
def get_customer_by_phone(
    phone_number: str,
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[CustomerResponse]:
    """Lookup customer profile by Algerian phone number (privileged administrative operation).
    Public callers cannot query personal customer details by phone number.
    """
    cleaned = re.sub(r"[\s\-\.]", "", phone_number)
    match = re.match(r"^(?:\+213|00213|0)([5-7][0-9]{8})$", cleaned)
    if match:
        cleaned = f"0{match.group(1)}"

    customer = db.scalar(select(Customer).where(Customer.phone_number == cleaned))
    if not customer:
        raise NotFoundError(f"Customer with phone number '{phone_number}' not found.")
    return ResponseEnvelope(data=CustomerResponse.model_validate(customer))


@router.get("/{customer_id}/orders", response_model=ResponseEnvelope[PaginatedResponse[OrderResponse]])
def get_customer_order_history(
    customer_id: int,
    pagination: PaginationParams = Depends(),
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.OPERATOR])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[PaginatedResponse[OrderResponse]]:
    """Retrieve all orders placed by a specific customer (Admin and Operator)."""
    customer = db.get(Customer, customer_id)
    if not customer:
        raise NotFoundError(f"Customer with ID {customer_id} not found.")

    items, total = OrderService.list_orders(
        db=db,
        page=pagination.page,
        page_size=pagination.page_size,
        customer_id=customer_id,
    )
    total_pages = ceil(total / pagination.page_size) if total > 0 else 0
    paginated_data = PaginatedResponse[OrderResponse](
        items=[OrderResponse.model_validate(o) for o in items],
        meta=PaginationMeta(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )
    return ResponseEnvelope(data=paginated_data)


@router.patch("/{customer_id}", response_model=ResponseEnvelope[CustomerResponse])
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    request: Request,
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[CustomerResponse]:
    """Update customer profile information or active status (Admin only)."""
    customer = db.get(Customer, customer_id)
    if not customer:
        raise NotFoundError(f"Customer with ID {customer_id} not found.")

    update_dict = data.model_dump(exclude_unset=True)
    if "phone_number" in update_dict and update_dict["phone_number"] is not None:
        conflict = db.scalar(
            select(Customer).where(Customer.phone_number == update_dict["phone_number"], Customer.id != customer_id)
        )
        if conflict:
            raise ConflictError(f"Phone number '{update_dict['phone_number']}' is already in use by another customer.")

    for field, val in update_dict.items():
        setattr(customer, field, val)

    db.commit()
    db.refresh(customer)

    # Log audit event
    client_ip = request.client.host if request.client else "unknown"
    AuditService.log_event(
        db=db,
        actor_type=AuditActorType.ADMIN,
        actor_id=str(_admin.id),
        action="UPDATE",
        entity_type="CUSTOMER",
        entity_id=str(customer_id),
        details={"updated_fields": list(update_dict.keys())},
        ip_address=client_ip,
    )

    return ResponseEnvelope(data=CustomerResponse.model_validate(customer), message="Customer updated successfully.")

