"""
Authentication API endpoints.

Provides login, logout, and user management endpoints.
"""

import json
import os
from pathlib import Path
from datetime import timedelta
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import Token, User, UserInDB, UserCredentials
from app.middleware.auth import create_access_token, require_auth
from app.utils.password import hash_password, verify_password
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Simple file-based user storage for single-user deployment
# Path should be: backend/data/users.json (not backend/app/data/users.json)
USER_DB_PATH = Path(__file__).parent.parent.parent / "data" / "users.json"


def load_users() -> Dict[str, UserInDB]:
    """Load users from JSON file."""
    if not USER_DB_PATH.exists():
        # Create default admin user on first run
        USER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        default_user = {
            "admin": {
                "username": "admin",
                "hashed_password": hash_password("admin123"),
                "disabled": False
            }
        }
        save_users(default_user)
        return {k: UserInDB(**v) for k, v in default_user.items()}

    with open(USER_DB_PATH, 'r') as f:
        users_data = json.load(f)

    return {k: UserInDB(**v) for k, v in users_data.items()}


def save_users(users: Dict):
    """Save users to JSON file."""
    USER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Convert UserInDB models to dicts if needed
    users_data = {}
    for username, user in users.items():
        if isinstance(user, UserInDB):
            users_data[username] = user.model_dump()
        else:
            users_data[username] = user

    with open(USER_DB_PATH, 'w') as f:
        json.dump(users_data, f, indent=2)


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database."""
    users = load_users()
    return users.get(username)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate a user with username and password.

    Args:
        username: Username
        password: Plain text password

    Returns:
        UserInDB if authentication successful, None otherwise
    """
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """
    Login endpoint using OAuth2 password flow.

    Returns JWT access token on successful authentication.

    **Default credentials (change after first login):**
    - Username: admin
    - Password: admin123
    """
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout(user: dict = Depends(require_auth)):
    """
    Logout endpoint.

    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the token. This endpoint just confirms the token is valid.
    """
    return {
        "message": "Successfully logged out",
        "username": user["username"]
    }


@router.get("/me", response_model=User)
async def get_current_user_info(user: dict = Depends(require_auth)) -> User:
    """Get current authenticated user information."""
    user_db = get_user(user["username"])

    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return User(username=user_db.username, disabled=user_db.disabled)


@router.post("/change-password")
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(..., min_length=8),
    user: dict = Depends(require_auth)
):
    """
    Change the current user's password.

    Requires current password verification.
    """
    username = user["username"]

    # Verify current password
    user_db = authenticate_user(username, current_password)
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Update password
    users = load_users()
    users[username].hashed_password = hash_password(new_password)
    save_users({k: v.model_dump() for k, v in users.items()})

    return {"message": "Password changed successfully"}


@router.post("/register")
async def register_user(
    credentials: UserCredentials,
    admin: dict = Depends(require_auth)  # Only authenticated users can create new users
):
    """
    Register a new user.

    Requires authentication (only existing users can create new users).
    """
    users = load_users()

    if credentials.username in users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Create new user
    new_user = UserInDB(
        username=credentials.username,
        hashed_password=hash_password(credentials.password),
        disabled=False
    )

    users[credentials.username] = new_user
    save_users({k: v.model_dump() for k, v in users.items()})

    return {
        "message": "User created successfully",
        "username": credentials.username
    }
