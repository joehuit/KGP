"""Authentication and administrative user schemas."""

from datetime import datetime
import re
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.core.security import AdminRole
from app.schemas.customer import CustomerResponse


class AdminLoginRequest(BaseModel):
    """Credentials submitted for administrative login."""
    email: EmailStr = Field(..., description="Administrator email address")
    password: str = Field(..., min_length=8, description="Account password")


class TokenResponse(BaseModel):
    """Bearer access token payload returned upon successful authentication."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(..., description="Token lifespan in seconds")
    role: str
    user_id: int
    full_name: str
    permissions: List[str] = Field(default_factory=list)


class TokenPayload(BaseModel):
    """Decoded JWT claims representation."""
    sub: str
    role: str
    type: str  # "admin" or "customer"
    exp: int
    iat: int
    jti: str


class AdminUserBase(BaseModel):
    """Base fields for administrator user."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    role: AdminRole = Field(default=AdminRole.OPERATOR, description="Administrative RBAC role")
    is_active: bool = Field(default=True)


class AdminUserCreate(AdminUserBase):
    """Payload to provision a new administrative user."""
    password: str = Field(..., min_length=8, description="Initial secure password")


class AdminUserUpdate(BaseModel):
    """Payload to update an administrative user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[AdminRole] = None
    is_active: Optional[bool] = None


class AdminUserResponse(AdminUserBase):
    """Public administrator user record response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class CustomerOTPRequest(BaseModel):
    """Request a one-time SMS verification code."""
    phone_number: str = Field(..., description="Algerian phone number (05, 06, 07)")

    @field_validator("phone_number")
    @classmethod
    def validate_and_normalize(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\.]", "", v)
        pattern = r"^(?:\+213|00213|0)([5-7][0-9]{8})$"
        match = re.match(pattern, cleaned)
        if not match:
            raise ValueError("Invalid Algerian mobile phone number. Must start with 05, 06, 07 or +213.")
        return f"0{match.group(1)}"


class CustomerOTPVerify(BaseModel):
    """Submit SMS verification code to obtain customer access token."""
    phone_number: str = Field(..., description="Algerian phone number")
    code: str = Field(..., min_length=4, max_length=8, description="Received OTP code")

    @field_validator("phone_number")
    @classmethod
    def validate_and_normalize(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\.]", "", v)
        pattern = r"^(?:\+213|00213|0)([5-7][0-9]{8})$"
        match = re.match(pattern, cleaned)
        if not match:
            raise ValueError("Invalid Algerian mobile phone number.")
        return f"0{match.group(1)}"


class CustomerTokenResponse(BaseModel):
    """Bearer access token payload returned upon successful customer verification."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    customer: CustomerResponse
