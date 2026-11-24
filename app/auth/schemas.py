"""Pydantic schemas for authentication and user accounts."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user fields."""

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Alphanumeric username (letters, numbers, underscore, hyphen)",
    )
    full_name: Optional[str] = Field(None, max_length=150, description="Optional full name")


class UserCreate(UserBase):
    """Payload to register a new user."""

    password: str = Field(
        ...,
        min_length=6,
        max_length=72,
        description="User password (between 6 and 72 characters)",
    )


class UserLogin(BaseModel):
    """JSON login payload."""

    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Password")


class UserUpdate(BaseModel):
    """Payload for updating user profile."""

    full_name: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    """Payload for changing account password."""

    old_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=6, max_length=72, description="New password"
    )


class UserOut(UserBase):
    """Public user response schema."""

    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT Access Token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class TokenPayload(BaseModel):
    """Decoded JWT payload data."""

    sub: Optional[str] = None
    user_id: Optional[int] = None
    exp: Optional[int] = None
