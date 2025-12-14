"""
In-memory caching utilities with TTL support.
"""

from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Tuple
import hashlib
import json


# Global cache storage
_cache: Dict[str, Tuple[Any, datetime]] = {}


def _make_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Create a unique cache key from function name and arguments.
    """
    # Convert args and kwargs to a hashable string
    key_data = {
        "func": func_name,
        "args": str(args),
        "kwargs": str(sorted(kwargs.items()))
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached_response(ttl_minutes: int = 5):
    """
    Decorator to cache async function responses with TTL.

    Args:
        ttl_minutes: Time-to-live for cached responses in minutes

    Usage:
        @cached_response(ttl_minutes=5)
        async def get_expensive_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Create cache key
            cache_key = _make_cache_key(func.__name__, args, kwargs)

            # Check cache
            if cache_key in _cache:
                result, timestamp = _cache[cache_key]
                if datetime.now() - timestamp < timedelta(minutes=ttl_minutes):
                    return result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            _cache[cache_key] = (result, datetime.now())
            return result

        return wrapper
    return decorator


def clear_cache(func_name: str = None) -> int:
    """
    Clear cached responses.

    Args:
        func_name: If provided, only clear cache for this function.
                   If None, clear all cache.

    Returns:
        Number of cache entries cleared
    """
    global _cache

    if func_name is None:
        count = len(_cache)
        _cache = {}
        return count

    # Clear only entries for specific function
    keys_to_remove = [
        key for key in _cache.keys()
        if func_name in key  # Rough match since key is hashed
    ]
    for key in keys_to_remove:
        del _cache[key]
    return len(keys_to_remove)


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache stats
    """
    now = datetime.now()
    return {
        "total_entries": len(_cache),
        "entries": [
            {
                "key": key[:8] + "...",
                "age_seconds": (now - timestamp).total_seconds()
            }
            for key, (_, timestamp) in _cache.items()
        ]
    }
