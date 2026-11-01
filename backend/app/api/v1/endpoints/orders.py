"""Customer orders API endpoints with order ownership enforcement and idempotency."""

from math import ceil
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.deps import (
    PaginationParams,
    extract_bearer_token,
    get_current_user_or_admin,
    get_db_session,
    require_roles,
)
from app.core.errors import AuthenticationError, ConflictError, NotFoundError
from app.core.rate_limit import enforce_rate_limit
from app.core.security import AdminRole, decode_access_token
from app.models.admin_user import AdminUser
from app.models.audit_log import AuditActorType
from app.models.customer import Customer
from app.models.order import OrderStatus
from app.schemas.common import PaginatedResponse, PaginationMeta, ResponseEnvelope
from app.schemas.order import (
    GuestOrderCreate,
    GuestOrderResponse,
    GuestOrderTrackRequest,
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from app.services.audit_service import AuditService
from app.services.idempotency_service import IdempotencyService, compute_request_hash
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=ResponseEnvelope[OrderResponse], status_code=status.HTTP_201_CREATED)
def place_order(
    data: OrderCreate,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    authorization: Optional[str] = Header(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    db: Session = Depends(get_db_session),
) -> Response:
    """Place a new spare-parts order.
    Features:
    - Order ownership enforcement: If caller is an authenticated customer, customer_id
      is derived strictly from the verified JWT claim (preventing IDOR and identity spoofing).
    - Idempotency support: Prevents duplicate order placement upon retries.
    - Server-calculated line totals and historical product snapshots.
    """
    effective_key = (idempotency_key or x_idempotency_key or "").strip() or None

    # Check caller authentication if token is provided
    raw_token = extract_bearer_token(authorization)
    authenticated_customer_id: Optional[int] = None
    is_admin = False

    if raw_token:
        try:
            payload = decode_access_token(raw_token)
            if payload.get("type") == "customer":
                authenticated_customer_id = int(payload["sub"])
                # Crucial security rule: override submitted customer_id with authenticated identity
                data.customer_id = authenticated_customer_id
            elif payload.get("type") == "admin":
                is_admin = True
        except Exception:
            # If token cannot be decoded, let downstream logic handle or proceed if public allowed
            pass

    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"order_place:{authenticated_customer_id or client_ip}"
    enforce_rate_limit(key=rate_key, limit=30, window_seconds=60, action_name="order placement")

    # In-process synchronization lock prevents concurrent race conditions on identical idempotency keys
    key_lock = IdempotencyService.get_lock_for_key(effective_key) if effective_key else None
    if key_lock:
        key_lock.acquire()

    try:
        # Idempotency check
        request_hash = ""
        if effective_key:
            request_hash = compute_request_hash(
                path="/api/v1/orders",
                customer_identifier=str(data.customer_id),
                payload=data.model_dump(),
            )
            existing = IdempotencyService.get_existing_response(
                db=db,
                key=effective_key,
                request_hash=request_hash,
            )
            if existing is not None:
                cached_status, cached_json = existing
                return JSONResponse(
                    status_code=cached_status,
                    content=cached_json,
                    headers={"Idempotent-Replay": "true"},
                )

        # Execute order creation via transactional service with atomic idempotency registration
        try:
            order = OrderService.create_order(
                db=db,
                data=data,
                idempotency_key=effective_key,
                request_hash=request_hash,
            )
        except IntegrityError:
            db.rollback()
            # Handle concurrent race condition: another concurrent transaction committed the same key
            if effective_key:
                existing = IdempotencyService.get_existing_response(
                    db=db,
                    key=effective_key,
                    request_hash=request_hash,
                )
                if existing is not None:
                    cached_status, cached_json = existing
                    return JSONResponse(
                        status_code=cached_status,
                        content=cached_json,
                        headers={"Idempotent-Replay": "true"},
                    )
            raise

        envelope = ResponseEnvelope(
            data=OrderResponse.model_validate(order),
            message="Order placed successfully.",
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=envelope.model_dump(mode="json"),
        )
    finally:
        if key_lock:
            key_lock.release()


@router.get("", response_model=ResponseEnvelope[PaginatedResponse[OrderResponse]])
def list_orders(
    customer_id: Optional[int] = Query(None, description="Filter orders by customer ID"),
    status_filter: Optional[OrderStatus] = Query(None, alias="status", description="Filter orders by status"),
    pagination: PaginationParams = Depends(),
    auth: tuple = Depends(get_current_user_or_admin),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[PaginatedResponse[OrderResponse]]:
    """List orders with strict role-based scoping:
    - Customer: Only allowed to view their own orders (customer_id forced to customer token ID).
    - Administrator/Operator: Allowed to view all orders across the business.
    """
    current_customer, current_admin = auth

    effective_customer_id = customer_id
    if current_customer:
        # Strictly scope to authenticated customer (IDOR prevention)
        effective_customer_id = current_customer.id

    items, total = OrderService.list_orders(
        db=db,
        page=pagination.page,
        page_size=pagination.page_size,
        customer_id=effective_customer_id,
        status_filter=status_filter,
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


@router.post("/guest", response_model=ResponseEnvelope[GuestOrderResponse], status_code=status.HTTP_201_CREATED)
def place_guest_order(
    data: GuestOrderCreate,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    db: Session = Depends(get_db_session),
) -> Response:
    """Place a new spare-parts order as a guest without requiring registration, password, or OTP.
    Features:
    - Server-side phone number and address validation.
    - Server-side price calculation and line-item snapshotting.
    - Idempotency key support for network retry safety.
    - Automatic collision-resistant tracking token generation for secure status tracking.
    """
    effective_key = (idempotency_key or x_idempotency_key or "").strip() or None
    client_ip = request.client.host if request.client else "unknown"

    # Rate limiting: 20 guest orders per minute per IP
    enforce_rate_limit(key=f"guest_order:{client_ip}", limit=20, window_seconds=60, action_name="guest order placement")

    key_lock = IdempotencyService.get_lock_for_key(effective_key) if effective_key else None
    if key_lock:
        key_lock.acquire()

    try:
        request_hash = ""
        if effective_key:
            request_hash = compute_request_hash(
                path="/api/v1/orders/guest",
                customer_identifier=data.phone_number,
                payload=data.model_dump(),
            )
            existing = IdempotencyService.get_existing_response(
                db=db,
                key=effective_key,
                request_hash=request_hash,
            )
            if existing is not None:
                cached_status, cached_json = existing
                return JSONResponse(
                    status_code=cached_status,
                    content=cached_json,
                    headers={"Idempotent-Replay": "true"},
                )

        try:
            order, customer = OrderService.create_guest_order(
                db=db,
                data=data,
                idempotency_key=effective_key,
                request_hash=request_hash,
            )
        except IntegrityError:
            db.rollback()
            if effective_key:
                existing = IdempotencyService.get_existing_response(
                    db=db,
                    key=effective_key,
                    request_hash=request_hash,
                )
                if existing is not None:
                    cached_status, cached_json = existing
                    return JSONResponse(
                        status_code=cached_status,
                        content=cached_json,
                        headers={"Idempotent-Replay": "true"},
                    )
            raise

        # Audit event
        AuditService.log_event(
            db=db,
            actor_type=AuditActorType.GUEST,
            actor_id=str(customer.id),
            action="GUEST_ORDER_CREATED",
            entity_type="ORDER",
            entity_id=str(order.id),
            details={
                "order_reference": order.order_reference,
                "total_amount": str(order.total_amount),
                "items_count": len(order.items),
                "wilaya": data.wilaya,
            },
            ip_address=client_ip,
        )

        guest_resp = GuestOrderResponse(
            id=order.id,
            order_reference=order.order_reference,
            tracking_token=order.tracking_token or "",
            status=order.status,
            total_amount=order.total_amount,
            customer_name=customer.full_name,
            customer_phone_masked=OrderService.mask_phone_number(customer.phone_number),
            wilaya=data.wilaya,
            commune=data.commune,
            delivery_address=data.delivery_address,
            customer_notes=data.customer_notes,
            items=[OrderItemResponse.model_validate(it) for it in order.items],
            created_at=order.created_at,
        )

        envelope = ResponseEnvelope(
            data=guest_resp,
            message="Order placed successfully.",
        )
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=envelope.model_dump(mode="json"),
        )
    finally:
        if key_lock:
            key_lock.release()


@router.post("/guest/track", response_model=ResponseEnvelope[GuestOrderResponse])
def track_guest_order_post(
    data: GuestOrderTrackRequest,
    request: Request,
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[GuestOrderResponse]:
    """Securely track a guest order status via POST body to prevent bearer token leakage in proxy URI logs."""
    client_ip = request.client.host if request.client else "unknown"
    enforce_rate_limit(key=f"guest_track:{client_ip}", limit=60, window_seconds=60, action_name="guest order tracking")

    order = OrderService.get_order_by_tracking_token(db=db, tracking_token=data.tracking_token)
    customer = order.customer

    name, wilaya, commune, delivery_address, notes = OrderService.parse_order_delivery_details(order, customer)

    guest_resp = GuestOrderResponse(
        id=order.id,
        order_reference=order.order_reference,
        tracking_token=order.tracking_token or data.tracking_token,
        status=order.status,
        total_amount=order.total_amount,
        customer_name=name,
        customer_phone_masked=OrderService.mask_phone_number(customer.phone_number),
        wilaya=wilaya,
        commune=commune,
        delivery_address=delivery_address,
        customer_notes=notes,
        items=[OrderItemResponse.model_validate(it) for it in order.items],
        created_at=order.created_at,
    )

    return ResponseEnvelope(data=guest_resp, message="Order details retrieved.")


@router.get("/guest/track/{tracking_token}", response_model=ResponseEnvelope[GuestOrderResponse])
def track_guest_order(
    tracking_token: str,
    request: Request,
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[GuestOrderResponse]:
    """Securely track a guest order status using the cryptographically unguessable tracking token."""
    client_ip = request.client.host if request.client else "unknown"
    enforce_rate_limit(key=f"guest_track:{client_ip}", limit=60, window_seconds=60, action_name="guest order tracking")

    order = OrderService.get_order_by_tracking_token(db=db, tracking_token=tracking_token)
    customer = order.customer

    name, wilaya, commune, delivery_address, notes = OrderService.parse_order_delivery_details(order, customer)

    guest_resp = GuestOrderResponse(
        id=order.id,
        order_reference=order.order_reference,
        tracking_token=order.tracking_token or tracking_token,
        status=order.status,
        total_amount=order.total_amount,
        customer_name=name,
        customer_phone_masked=OrderService.mask_phone_number(customer.phone_number),
        wilaya=wilaya,
        commune=commune,
        delivery_address=delivery_address,
        customer_notes=notes,
        items=[OrderItemResponse.model_validate(it) for it in order.items],
        created_at=order.created_at,
    )

    return ResponseEnvelope(data=guest_resp, message="Order details retrieved.")


@router.get("/{order_id}", response_model=ResponseEnvelope[OrderResponse])
def get_order(
    order_id: int,
    auth: tuple = Depends(get_current_user_or_admin),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[OrderResponse]:
    """Retrieve full order details:
    - Customer: Allowed only if order belongs to the authenticated customer.
    - Administrator/Operator: Allowed to inspect any order.
    """
    current_customer, current_admin = auth

    order = OrderService.get_order_by_id(db=db, order_id=order_id)

    # Customer authorization check: prevent unauthorized inspection of other customer orders
    if current_customer and order.customer_id != current_customer.id:
        raise NotFoundError(f"Order with ID {order_id} not found.")

    return ResponseEnvelope(data=OrderResponse.model_validate(order))


@router.patch("/{order_id}/status", response_model=ResponseEnvelope[OrderResponse])
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    request: Request,
    _admin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.OPERATOR])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[OrderResponse]:
    """Update order lifecycle status (Superadmin, Admin, or Operator role required)."""
    order = OrderService.update_order_status(db=db, order_id=order_id, data=data)

    # Log audit event
    client_ip = request.client.host if request.client else "unknown"
    AuditService.log_event(
        db=db,
        actor_type=AuditActorType.ADMIN,
        actor_id=str(_admin.id),
        action="STATUS_UPDATE",
        entity_type="ORDER",
        entity_id=str(order_id),
        details={"new_status": order.status.value, "order_reference": order.order_reference},
        ip_address=client_ip,
    )

    return ResponseEnvelope(
        data=OrderResponse.model_validate(order),
        message=f"Order status updated to {order.status.value}.",
    )
