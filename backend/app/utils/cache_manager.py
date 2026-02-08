"""
Unified Cache Manager with TTL and LRU Eviction.

Provides thread-safe caching with time-to-live and least-recently-used eviction
to prevent unbounded memory growth.
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
import threading
import functools
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Thread-safe cache with TTL (time-to-live) and LRU (least-recently-used) eviction.

    Features:
    - Automatic expiration based on TTL
    - LRU eviction when max_size is reached
    - Thread-safe operations
    - Hit/miss statistics tracking
    """

    def __init__(self, max_size: int = 1000, default_ttl_minutes: int = 5):
        """
        Initialize TTL cache.

        Args:
            max_size: Maximum number of entries before LRU eviction
            default_ttl_minutes: Default time-to-live in minutes
        """
        self.max_size = max_size
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self._cache: OrderedDict[str, tuple[Any, datetime]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if exists and not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, expiry = self._cache[key]

            # Check if expired
            if datetime.now() >= expiry:
                # Expired - remove it
                del self._cache[key]
                self._misses += 1
                return None

            # Hit - move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL (uses default if not specified)
        """
        with self._lock:
            # Evict oldest if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)  # Remove oldest (first) item

            # Set expiry time
            expiry = datetime.now() + (ttl if ttl is not None else self.default_ttl)

            # Store value with expiry
            self._cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """
        Delete a specific key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key existed and was deleted, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        """Clear all cache entries and reset statistics."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.info(f"Cache cleared: {count} entries removed")

    def clear_expired(self):
        """Remove all expired entries from cache."""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items()
                if now >= expiry
            ]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"Cleared {len(expired_keys)} expired cache entries")

    def stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with size, hits, misses, and hit rate
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.2f}%",
                "total_requests": total
            }

    def size(self) -> int:
        """Get current number of cached entries."""
        with self._lock:
            return len(self._cache)


# Global cache instances
api_cache = TTLCache(max_size=500, default_ttl_minutes=5)
screener_cache = TTLCache(max_size=1000, default_ttl_minutes=1440)  # 24 hours


def cached(
    ttl_minutes: int = 5,
    cache_instance: TTLCache = None,
    key_prefix: str = ""
):
    """
    Decorator for caching function results.

    Args:
        ttl_minutes: Time-to-live in minutes
        cache_instance: Cache instance to use (defaults to api_cache)
        key_prefix: Optional prefix for cache keys

    Example:
        @cached(ttl_minutes=60, key_prefix="stocks:")
        async def get_stock_data(ticker: str):
            ...
    """
    if cache_instance is None:
        cache_instance = api_cache

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_data = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            key_str = json.dumps(key_data, sort_keys=True)
            cache_key = f"{key_prefix}{hashlib.md5(key_str.encode()).hexdigest()}"

            # Try cache first
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached_value

            # Execute function
            logger.debug(f"Cache miss: {func.__name__}")
            result = await func(*args, **kwargs)

            # Store in cache
            cache_instance.set(
                cache_key,
                result,
                ttl=timedelta(minutes=ttl_minutes)
            )

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            key_data = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            key_str = json.dumps(key_data, sort_keys=True)
            cache_key = f"{key_prefix}{hashlib.md5(key_str.encode()).hexdigest()}"

            # Try cache first
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached_value

            # Execute function
            logger.debug(f"Cache miss: {func.__name__}")
            result = func(*args, **kwargs)

            # Store in cache
            cache_instance.set(
                cache_key,
                result,
                ttl=timedelta(minutes=ttl_minutes)
            )

            return result

        # Return appropriate wrapper based on whether function is async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def clear_all_caches():
    """Clear all global cache instances."""
    api_cache.clear()
    screener_cache.clear()
    logger.info("All caches cleared")


def get_cache_stats() -> dict:
    """Get statistics for all cache instances."""
    return {
        "api_cache": api_cache.stats(),
        "screener_cache": screener_cache.stats()
    }
