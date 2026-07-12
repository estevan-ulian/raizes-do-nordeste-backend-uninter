from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.auth.models import Role


class UserRegister(BaseModel):
    """Schema for public user registration. Role is always CLIENTE."""

    name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=32)
    phone: Optional[str] = None
    privacy_consent: bool = Field(
        description="Consentimento obrigatório para tratamento mínimo de dados (LGPD)."
    )
    marketing_consent: bool = Field(
        default=False,
        description="Consentimento opcional para marketing e fidelidade (LGPD).",
    )


class UserCreate(BaseModel):
    """Schema for administrative user creation — allows defining a role."""

    name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=32)
    phone: Optional[str] = None
    role: Role


class UserSelfUpdate(BaseModel):
    """Schema for users updating their own profile data."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)


class UserStatusUpdate(BaseModel):
    """Schema for administrative user activation/deactivation."""

    is_active: bool


class UserResponse(BaseModel):
    """Schema for user data returned in responses. Does not include password hash."""

    id: UUID
    name: str
    email: str
    phone: Optional[str] = None
    role: Role
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Schema for paginated user lists."""

    items: list[UserResponse]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """Schema for login requests."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=32)


class TokenResponse(BaseModel):
    """Schema for token responses returned after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class LogoutRequest(BaseModel):
    """Schema for logout requests."""

    refresh_token: str


class PasswordResetRequestSchema(BaseModel):
    email: EmailStr


class PasswordResetConfirmSchema(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=32)
    password_confirm: str = Field(min_length=8, max_length=32)
