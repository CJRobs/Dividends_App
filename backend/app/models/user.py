"""
User authentication models.

Pydantic models for user authentication, tokens, and credentials.
"""

from pydantic import BaseModel, Field
from typing import Optional


class Token(BaseModel):
    """JWT token response model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Data encoded in JWT token."""

    username: Optional[str] = None


class UserCredentials(BaseModel):
    """User login credentials."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")


class User(BaseModel):
    """User model."""

    username: str = Field(..., description="Unique username")
    disabled: bool = Field(default=False, description="Whether user account is disabled")


class UserInDB(User):
    """User model with hashed password (for database storage)."""

    hashed_password: str = Field(..., description="Bcrypt hashed password")
