"""Authentication and identity API endpoints for administrators and customers."""

from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import (
    PaginationParams,
    extract_bearer_token,
    get_current_admin,
    get_db_session,
    require_roles,
)
from app.core.config import settings
from app.core.errors import AuthenticationError, ConflictError, NotFoundError
from app.core.logging import logger
from app.core.rate_limit import enforce_rate_limit
from app.core.security import (
    AdminRole,
    ROLE_PERMISSIONS,
    create_access_token,
    decode_access_token,
    get_password_hash,
    token_revocation_service,
    verify_password,
)
from app.models.admin_user import AdminUser
from app.models.customer import Customer
from app.schemas.auth import (
    AdminLoginRequest,
    AdminUserCreate,
    AdminUserResponse,
    AdminUserUpdate,
    CustomerOTPRequest,
    CustomerOTPVerify,
    CustomerTokenResponse,
    TokenResponse,
)
from app.schemas.common import PaginatedResponse, PaginationMeta, ResponseEnvelope
from app.schemas.customer import CustomerResponse
from app.services.sms_provider import otp_verification_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- Admin Authentication ---

@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
@router.post("/admin/login", response_model=ResponseEnvelope[TokenResponse])
def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[TokenResponse]:
    """Authenticate administrator using email and password.
    Issues a short-lived signed JWT access token.
    Rate limited to 5 attempts per minute per IP to protect against credential stuffing.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"admin_login:{client_ip}:{payload.email.lower()}"
    enforce_rate_limit(key=rate_key, limit=5, window_seconds=60, action_name="administrator login")

    # Look up admin user by normalized email
    admin = db.scalar(select(AdminUser).where(AdminUser.email == payload.email.lower()))

    # Constant-time safety: verify password even if user is missing using dummy hash
    dummy_hash = "$2b$12$e8Y50k/E3D480a6U2zMvce7M.i8aBms2f4lq/Pvh9283e7Z62b2/C"
    target_hash = admin.hashed_password if admin else dummy_hash
    password_valid = verify_password(payload.password, target_hash)

    if not admin or not password_valid:
        logger.warning("Failed admin login attempt for email: %s from IP: %s", payload.email, client_ip)
        raise AuthenticationError("Invalid email or password.")

    if not admin.is_active:
        logger.warning("Login attempted for deactivated admin account: %s", payload.email)
        raise AuthenticationError("Account is inactive. Please contact your system administrator.")

    # Generate JWT access token
    expires_delta = timedelta(minutes=settings.ADMIN_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": str(admin.id),
        "email": admin.email,
        "full_name": admin.full_name,
        "role": admin.role,
        "type": "admin",
    }
    access_token = create_access_token(data=token_data, expires_delta=expires_delta)
    permissions = [p.value for p in ROLE_PERMISSIONS.get(admin.role, set())]

    logger.info("Admin successfully authenticated: %s (Role: %s)", admin.email, admin.role)
    return ResponseEnvelope(
        data=TokenResponse(
            access_token=access_token,
            expires_in=settings.ADMIN_TOKEN_EXPIRE_MINUTES * 60,
            role=admin.role,
            user_id=admin.id,
            full_name=admin.full_name,
            permissions=permissions,
        ),
        message="Login successful.",
    )


@router.post("/logout", response_model=ResponseEnvelope[dict])
def logout(
    authorization: str = Header(..., description="Bearer JWT access token"),
) -> ResponseEnvelope[dict]:
    """Revoke the current access token immediately via the token blacklist service."""
    raw_token = extract_bearer_token(authorization)
    if not raw_token:
        raise AuthenticationError("Authorization Bearer token required for logout.")

    try:
        payload = decode_access_token(raw_token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti:
            token_revocation_service.revoke(jti=jti, expires_at=float(exp) if exp else None)
    except AuthenticationError:
        # If token is already expired/invalid, logout is effectively successful
        pass

    return ResponseEnvelope(
        data={"revoked": True},
        message="Successfully logged out. Access token has been revoked.",
    )


@router.get("/me", response_model=ResponseEnvelope[dict])
def get_current_user_profile(
    current_admin: AdminUser = Depends(get_current_admin),
) -> ResponseEnvelope[dict]:
    """Retrieve authenticated administrator profile and effective RBAC permissions."""
    permissions = [p.value for p in ROLE_PERMISSIONS.get(current_admin.role, set())]
    return ResponseEnvelope(
        data={
            "id": current_admin.id,
            "email": current_admin.email,
            "full_name": current_admin.full_name,
            "role": current_admin.role,
            "is_active": current_admin.is_active,
            "permissions": permissions,
            "created_at": current_admin.created_at.isoformat() if current_admin.created_at else None,
        }
    )


# --- Customer Identity & OTP Authentication ---

@router.post("/customer/request-otp", response_model=ResponseEnvelope[dict])
def request_customer_otp(
    payload: CustomerOTPRequest,
    request: Request,
) -> ResponseEnvelope[dict]:
    """Request a one-time SMS verification passcode for mobile customer login or registration.
    Rate limited to 3 requests per 10 minutes per phone number.
    """
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"otp_request:{payload.phone_number}"
    enforce_rate_limit(key=rate_key, limit=3, window_seconds=600, action_name="verification code request")

    success = otp_verification_service.generate_and_send_otp(payload.phone_number)
    if not success:
        logger.error("Failed to dispatch SMS verification to %s", payload.phone_number)
        raise AuthenticationError("Failed to dispatch SMS verification code. Please try again shortly.")

    return ResponseEnvelope(
        data={"phone_number": payload.phone_number, "expires_in_seconds": 300},
        message="Verification code dispatched via SMS. Valid for 5 minutes.",
    )


@router.post("/customer/verify-otp", response_model=ResponseEnvelope[CustomerTokenResponse])
def verify_customer_otp(
    payload: CustomerOTPVerify,
    request: Request,
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[CustomerTokenResponse]:
    """Verify one-time passcode and exchange for authenticated customer access token.
    Rate limited to 5 attempts per 10 minutes per phone number.
    """
    rate_key = f"otp_verify:{payload.phone_number}"
    enforce_rate_limit(key=rate_key, limit=5, window_seconds=600, action_name="verification attempt")

    # Validate OTP
    otp_verification_service.verify_otp(payload.phone_number, payload.code)

    # Locate customer account
    customer = db.scalar(select(Customer).where(Customer.phone_number == payload.phone_number))
    if not customer:
        raise NotFoundError(
            f"Phone number '{payload.phone_number}' verified, but no customer profile exists. "
            "Please complete customer registration."
        )

    if not customer.is_active:
        raise AuthenticationError("Customer account is deactivated. Please contact support.")

    # Generate customer JWT
    expires_delta = timedelta(minutes=settings.CUSTOMER_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": str(customer.id),
        "phone_number": customer.phone_number,
        "type": "customer",
        "role": "customer",
    }
    access_token = create_access_token(data=token_data, expires_delta=expires_delta)

    logger.info("Customer authenticated via OTP: ID=%d Phone=%s", customer.id, customer.phone_number)
    return ResponseEnvelope(
        data=CustomerTokenResponse(
            access_token=access_token,
            expires_in=settings.CUSTOMER_TOKEN_EXPIRE_MINUTES * 60,
            customer=CustomerResponse.model_validate(customer),
        ),
        message="Verification successful.",
    )


# --- RBAC Admin User Management (Superadmin Only) ---

admin_users_router = APIRouter(prefix="/admin/users", tags=["Admin User Management"])


@admin_users_router.get("", response_model=ResponseEnvelope[PaginatedResponse[AdminUserResponse]])
def list_admin_users(
    pagination: PaginationParams = Depends(),
    _superadmin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[PaginatedResponse[AdminUserResponse]]:
    """List administrative user accounts (Superadmin only)."""
    offset = (pagination.page - 1) * pagination.page_size
    query = select(AdminUser).order_by(AdminUser.id.asc()).offset(offset).limit(pagination.page_size)
    users = db.scalars(query).all()

    paginated = PaginatedResponse(
        items=[AdminUserResponse.model_validate(u) for u in users],
        meta=PaginationMeta(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=len(users),
            total_pages=1,
        ),
    )
    return ResponseEnvelope(data=paginated)


@admin_users_router.post("", response_model=ResponseEnvelope[AdminUserResponse], status_code=status.HTTP_201_CREATED)
def create_admin_user(
    payload: AdminUserCreate,
    _superadmin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[AdminUserResponse]:
    """Provision a new administrative user with assigned RBAC role (Superadmin only)."""
    existing = db.scalar(select(AdminUser).where(AdminUser.email == payload.email.lower()))
    if existing:
        raise ConflictError(f"An administrator with email '{payload.email}' already exists.")

    hashed_pw = get_password_hash(payload.password)
    new_user = AdminUser(
        email=payload.email.lower(),
        hashed_password=hashed_pw,
        full_name=payload.full_name,
        role=payload.role.value if isinstance(payload.role, AdminRole) else str(payload.role),
        is_active=payload.is_active,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info("New admin created: %s with role %s", new_user.email, new_user.role)
    return ResponseEnvelope(
        data=AdminUserResponse.model_validate(new_user),
        message=f"Administrator '{new_user.email}' provisioned successfully.",
    )


@admin_users_router.get("/{admin_id}", response_model=ResponseEnvelope[AdminUserResponse])
def get_admin_user(
    admin_id: int,
    _superadmin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[AdminUserResponse]:
    """Retrieve an administrator account by ID (Superadmin only)."""
    admin = db.get(AdminUser, admin_id)
    if not admin:
        raise NotFoundError(f"Administrator with ID {admin_id} not found.")
    return ResponseEnvelope(data=AdminUserResponse.model_validate(admin))


@admin_users_router.patch("/{admin_id}", response_model=ResponseEnvelope[AdminUserResponse])
def update_admin_user(
    admin_id: int,
    payload: AdminUserUpdate,
    _superadmin: AdminUser = Depends(require_roles([AdminRole.SUPERADMIN])),
    db: Session = Depends(get_db_session),
) -> ResponseEnvelope[AdminUserResponse]:
    """Update administrator details, role, or active status (Superadmin only)."""
    admin = db.get(AdminUser, admin_id)
    if not admin:
        raise NotFoundError(f"Administrator with ID {admin_id} not found.")

    if payload.email is not None and payload.email.lower() != admin.email:
        existing = db.scalar(select(AdminUser).where(AdminUser.email == payload.email.lower()))
        if existing:
            raise ConflictError(f"Email '{payload.email}' is already in use.")
        admin.email = payload.email.lower()

    if payload.full_name is not None:
        admin.full_name = payload.full_name

    if payload.role is not None:
        admin.role = payload.role.value if isinstance(payload.role, AdminRole) else str(payload.role)

    if payload.is_active is not None:
        admin.is_active = payload.is_active

    if payload.password is not None:
        admin.hashed_password = get_password_hash(payload.password)

    db.commit()
    db.refresh(admin)
    return ResponseEnvelope(
        data=AdminUserResponse.model_validate(admin),
        message="Administrator updated successfully.",
    )
