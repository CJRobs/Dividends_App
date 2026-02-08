"""
In-memory caching utilities with TTL support.

This module now uses the unified cache_manager for improved performance
and LRU eviction. The API remains backward compatible.
"""

from functools import wraps
from typing import Any, Callable, Dict
from .cache_manager import api_cache, cached as cache_decorator, clear_all_caches


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
    # Use the new unified cache decorator
    return cache_decorator(ttl_minutes=ttl_minutes, cache_instance=api_cache)


def clear_cache(func_name: str = None) -> int:
    """
    Clear cached responses.

    Args:
        func_name: If provided, only clear cache for this function.
                   If None, clear all cache.

    Returns:
        Number of cache entries cleared
    """
    # If no function name specified, clear all
    if func_name is None:
        size_before = api_cache.size()
        api_cache.clear()
        return size_before

    # For function-specific clearing, we need to clear all
    # since the new cache uses MD5 hashes
    # This is a limitation of the hash-based approach
    size_before = api_cache.size()
    api_cache.clear()
    return size_before


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache stats
    """
    return api_cache.stats()
