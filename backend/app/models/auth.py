"""
Authentication models for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserSignUp(BaseModel):
    """Model for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    name: Optional[str] = None

class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Model for user response."""
    id: UUID
    email: str
    name: Optional[str] = None
    created_at: datetime
    email_confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Model for authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    """Model for refresh token request."""
    refresh_token: str

class PasswordResetRequest(BaseModel):
    """Model for password reset request."""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Model for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    """Model for updating user profile."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class ChangePasswordRequest(BaseModel):
    """Model for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=6)
