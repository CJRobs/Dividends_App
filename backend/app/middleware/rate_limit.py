"""
Rate Limiting Middleware

Provides request rate limiting using SlowAPI to protect against abuse and DoS attacks.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter
# Default limit: 100 requests per minute per IP address
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://",  # In-memory storage for single-instance deployment
)

# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    "general": "100/minute",      # General API endpoints
    "expensive": "10/minute",     # Expensive operations (forecast, screener)
    "auth": "5/minute",           # Authentication endpoints (prevent brute force)
    "admin": "30/minute",         # Admin operations
}


def get_rate_limit(limit_type: str = "general") -> str:
    """
    Get rate limit string for a given limit type.

    Args:
        limit_type: Type of rate limit (general, expensive, auth, admin)

    Returns:
        Rate limit string (e.g., "100/minute")
    """
    return RATE_LIMITS.get(limit_type, RATE_LIMITS["general"])
