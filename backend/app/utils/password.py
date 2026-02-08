"""
Password hashing and verification utilities.

This module provides secure password hashing using bcrypt directly.
Fixed for compatibility with bcrypt 5.x and Python 3.13.
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string (bcrypt hash as string)
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')

    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored bcrypt hash (as string)

    Returns:
        True if password matches, False otherwise
    """
    try:
        # Convert both to bytes
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')

        # Verify
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        # If verification fails for any reason, return False
        return False
