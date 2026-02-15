"""
Persistent File-Based Cache for Alpha Vantage API Responses.

Provides disk-backed caching with:
- JSON file storage organized by cache type (overview, dividends, income, balance, cashflow)
- Freshness checking with type-specific TTLs
- Metadata tracking for API call savings and statistics
- Thread-safe file I/O operations
- Cache warming on application startup
"""

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class AlphaVantageCache:
    """
    Disk-backed cache for Alpha Vantage API responses.

    Features:
    - Persistent storage in JSON files
    - Type-specific TTLs (overview: 24h, dividends: 48h, financials: 7 days)
    - Automatic freshness checking
    - Metadata tracking for monitoring
    - Thread-safe operations
    """

    def __init__(self, cache_dir: Path, memory_cache):
        """
        Initialize the disk cache.

        Args:
            cache_dir: Base directory for cache storage
            memory_cache: Reference to in-memory TTLCache instance
        """
        self.cache_dir = Path(cache_dir)
        self.memory_cache = memory_cache
        self._lock = threading.Lock()

        # Cache type subdirectories
        self.cache_types = {
            "overview": "overview",
            "dividends": "dividends",
            "income": "income",
            "balance": "balance",
            "cashflow": "cashflow",
            "earnings": "earnings",
            "income_quarterly": "income_quarterly",
            "balance_quarterly": "balance_quarterly",
            "cashflow_quarterly": "cashflow_quarterly",
        }

        # Type-specific TTLs (in hours)
        self.ttl_config = {
            "overview": 24,      # Company fundamentals change daily
            "dividends": 48,     # Dividend payments monthly/quarterly
            "income": 168,       # 7 days - annual/quarterly reports
            "balance": 168,      # 7 days - annual/quarterly reports
            "cashflow": 168,     # 7 days - annual/quarterly reports
            "earnings": 168,     # 7 days - quarterly earnings
            "income_quarterly": 168,
            "balance_quarterly": 168,
            "cashflow_quarterly": 168,
        }

        # Metadata file path
        self.metadata_file = self.cache_dir / "metadata.json"

        # Initialize metadata structure
        self.metadata = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "statistics": {
                "total_cached_symbols": 0,
                "total_cache_files": 0,
                "total_disk_size_bytes": 0,
                "api_calls_saved": 0,
                "api_calls_made": 0,
                "cache_hit_rate": 0.0
            },
            "by_type": {},
            "symbols": {}
        }

    def initialize_directories(self):
        """Create cache directory structure if it doesn't exist."""
        try:
            # Create base cache directory
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            # Create type subdirectories
            for cache_type in self.cache_types.values():
                (self.cache_dir / cache_type).mkdir(exist_ok=True)

            # Load or create metadata
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            else:
                self.save_metadata()

            logger.info(f"Cache directories initialized at {self.cache_dir}")

        except Exception as e:
            logger.error(f"Failed to initialize cache directories: {e}")
            raise

    def get(self, cache_type: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from disk cache if fresh.

        Args:
            cache_type: Type of cache (overview, dividends, income, balance, cashflow)
            symbol: Stock symbol

        Returns:
            Cached data if fresh, None otherwise
        """
        result = self.get_with_metadata(cache_type, symbol)
        if result is None:
            return None
        return result[0]

    def get_with_metadata(self, cache_type: str, symbol: str) -> Optional[tuple]:
        """
        Retrieve data and metadata from disk cache if fresh.

        Returns:
            Tuple of (data, metadata_dict) if fresh, None otherwise.
            metadata_dict contains cached_at, expires_at, ttl_hours.
        """
        try:
            cache_file = self._get_cache_file_path(cache_type, symbol)

            if not cache_file.exists():
                return None

            with self._lock:
                with open(cache_file, 'r') as f:
                    cache_entry = json.load(f)

            metadata = cache_entry.get("metadata", {})
            if self._is_fresh(metadata):
                logger.debug(f"Disk cache hit: {cache_type}:{symbol}")
                self._update_stats(cache_type, symbol, hit=True)

                if self.memory_cache:
                    cache_key = f"{cache_type}:{symbol.upper()}"
                    ttl_hours = metadata.get("ttl_hours", 24)
                    self.memory_cache.set(
                        cache_key,
                        cache_entry["data"],
                        ttl=timedelta(hours=ttl_hours)
                    )

                return (cache_entry["data"], metadata)
            else:
                logger.debug(f"Disk cache expired: {cache_type}:{symbol}")
                cache_file.unlink()
                return None

        except Exception as e:
            logger.warning(f"Error reading cache file {cache_type}:{symbol}: {e}")
            return None

    def set(self, cache_type: str, symbol: str, data: Dict[str, Any], ttl_hours: Optional[int] = None):
        """
        Save data to disk cache.

        Args:
            cache_type: Type of cache
            symbol: Stock symbol
            data: API response data to cache
            ttl_hours: Optional custom TTL (uses default if not specified)
        """
        try:
            # Use default TTL if not specified
            if ttl_hours is None:
                ttl_hours = self.ttl_config.get(cache_type, 24)

            # Construct cache entry
            now = datetime.now()
            cache_entry = {
                "metadata": {
                    "symbol": symbol.upper(),
                    "cache_type": cache_type,
                    "cached_at": now.isoformat(),
                    "expires_at": (now + timedelta(hours=ttl_hours)).isoformat(),
                    "ttl_hours": ttl_hours,
                    "version": "1.0"
                },
                "data": data
            }

            # Write to file atomically (write to temp, then rename)
            cache_file = self._get_cache_file_path(cache_type, symbol)
            temp_file = cache_file.with_suffix('.tmp')

            with self._lock:
                with open(temp_file, 'w') as f:
                    json.dump(cache_entry, f, indent=2)

                # Atomic rename
                temp_file.replace(cache_file)

            logger.debug(f"Cached {cache_type}:{symbol} to disk (TTL: {ttl_hours}h)")
            self._update_stats(cache_type, symbol, hit=False)

        except Exception as e:
            logger.error(f"Failed to write cache file {cache_type}:{symbol}: {e}")

    def _is_fresh(self, metadata: Dict[str, Any]) -> bool:
        """
        Check if cache entry is still fresh.

        Args:
            metadata: Cache entry metadata

        Returns:
            True if fresh, False if expired
        """
        try:
            expires_at_str = metadata.get("expires_at")
            if not expires_at_str:
                return False

            expires_at = datetime.fromisoformat(expires_at_str)
            return datetime.now() < expires_at

        except Exception as e:
            logger.warning(f"Error checking cache freshness: {e}")
            return False

    def _get_cache_file_path(self, cache_type: str, symbol: str) -> Path:
        """
        Get file path for cached symbol.

        Args:
            cache_type: Type of cache
            symbol: Stock symbol

        Returns:
            Path to cache file
        """
        subdir = self.cache_types.get(cache_type, cache_type)
        return self.cache_dir / subdir / f"{symbol.upper()}.json"

    def warm_cache_from_disk(self) -> int:
        """
        Load fresh cache entries from disk into memory on startup.

        Returns:
            Number of entries loaded
        """
        loaded_count = 0

        try:
            for cache_type in self.cache_types.values():
                type_dir = self.cache_dir / cache_type

                if not type_dir.exists():
                    continue

                for cache_file in type_dir.glob("*.json"):
                    try:
                        with open(cache_file, 'r') as f:
                            cache_entry = json.load(f)

                        # Check if fresh
                        if self._is_fresh(cache_entry.get("metadata", {})):
                            symbol = cache_entry["metadata"].get("symbol", cache_file.stem)

                            # Load into memory cache
                            if self.memory_cache:
                                cache_key = f"{cache_type}:{symbol}"
                                ttl_hours = cache_entry["metadata"].get("ttl_hours", 24)
                                self.memory_cache.set(
                                    cache_key,
                                    cache_entry["data"],
                                    ttl=timedelta(hours=ttl_hours)
                                )
                                loaded_count += 1
                        else:
                            # Remove stale cache
                            cache_file.unlink()

                    except Exception as e:
                        logger.warning(f"Error loading cache file {cache_file}: {e}")
                        continue

            logger.info(f"Cache warming complete: {loaded_count} entries loaded from disk")
            return loaded_count

        except Exception as e:
            logger.error(f"Error during cache warming: {e}")
            return loaded_count

    def _update_stats(self, cache_type: str, symbol: str, hit: bool):
        """
        Update cache statistics.

        Args:
            cache_type: Type of cache
            symbol: Stock symbol
            hit: True if cache hit, False if API call made
        """
        try:
            # Update global stats
            if hit:
                self.metadata["statistics"]["api_calls_saved"] += 1
            else:
                self.metadata["statistics"]["api_calls_made"] += 1

            # Update hit rate
            total = (self.metadata["statistics"]["api_calls_saved"] +
                    self.metadata["statistics"]["api_calls_made"])
            if total > 0:
                hit_rate = self.metadata["statistics"]["api_calls_saved"] / total
                self.metadata["statistics"]["cache_hit_rate"] = round(hit_rate, 4)

            # Update type stats
            if cache_type not in self.metadata["by_type"]:
                self.metadata["by_type"][cache_type] = {
                    "cached_symbols": 0,
                    "api_calls_saved": 0,
                    "total_size_bytes": 0
                }

            if hit:
                self.metadata["by_type"][cache_type]["api_calls_saved"] += 1

            # Update symbol stats
            symbol_upper = symbol.upper()
            if symbol_upper not in self.metadata["symbols"]:
                self.metadata["symbols"][symbol_upper] = {
                    "last_accessed": datetime.now().isoformat(),
                    "total_requests": 0,
                    "cache_hits": 0,
                    "cached_types": []
                }

            self.metadata["symbols"][symbol_upper]["total_requests"] += 1
            self.metadata["symbols"][symbol_upper]["last_accessed"] = datetime.now().isoformat()

            if hit:
                self.metadata["symbols"][symbol_upper]["cache_hits"] += 1

            if cache_type not in self.metadata["symbols"][symbol_upper]["cached_types"]:
                self.metadata["symbols"][symbol_upper]["cached_types"].append(cache_type)

            self.metadata["last_updated"] = datetime.now().isoformat()

        except Exception as e:
            logger.warning(f"Error updating cache stats: {e}")

    def get_metadata_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics and metadata.

        Returns:
            Dictionary with cache statistics
        """
        try:
            # Update file counts and sizes
            total_files = 0
            total_size = 0

            for cache_type in self.cache_types.values():
                type_dir = self.cache_dir / cache_type
                if type_dir.exists():
                    files = list(type_dir.glob("*.json"))
                    total_files += len(files)
                    total_size += sum(f.stat().st_size for f in files)

                    # Update per-type stats
                    if cache_type in self.metadata["by_type"]:
                        self.metadata["by_type"][cache_type]["cached_symbols"] = len(files)
                        self.metadata["by_type"][cache_type]["total_size_bytes"] = sum(
                            f.stat().st_size for f in files
                        )

            self.metadata["statistics"]["total_cache_files"] = total_files
            self.metadata["statistics"]["total_disk_size_bytes"] = total_size
            self.metadata["statistics"]["total_cached_symbols"] = len(self.metadata["symbols"])

            return self.metadata

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return self.metadata

    def save_metadata(self):
        """Save metadata to disk."""
        try:
            with self._lock:
                with open(self.metadata_file, 'w') as f:
                    json.dump(self.metadata, f, indent=2)

            logger.debug("Cache metadata saved")

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def clear_type(self, cache_type: str) -> int:
        """
        Clear all cache files of a specific type.

        Args:
            cache_type: Type of cache to clear

        Returns:
            Number of files deleted
        """
        try:
            type_dir = self.cache_dir / self.cache_types.get(cache_type, cache_type)

            if not type_dir.exists():
                return 0

            files = list(type_dir.glob("*.json"))
            count = len(files)

            for file in files:
                file.unlink()

            logger.info(f"Cleared {count} cache files for type: {cache_type}")
            return count

        except Exception as e:
            logger.error(f"Error clearing cache type {cache_type}: {e}")
            return 0

    def clear_symbol(self, symbol: str) -> int:
        """
        Clear all cache files for a specific symbol.

        Args:
            symbol: Stock symbol to clear

        Returns:
            Number of files deleted
        """
        try:
            count = 0
            symbol_upper = symbol.upper()

            for cache_type in self.cache_types.values():
                cache_file = self._get_cache_file_path(cache_type, symbol_upper)
                if cache_file.exists():
                    cache_file.unlink()
                    count += 1

            logger.info(f"Cleared {count} cache files for symbol: {symbol}")
            return count

        except Exception as e:
            logger.error(f"Error clearing cache for symbol {symbol}: {e}")
            return 0


# Global cache instance (initialized in main.py)
av_cache: Optional[AlphaVantageCache] = None


def init_cache(settings):
    """
    Initialize the global Alpha Vantage cache instance.

    Args:
        settings: Application settings with cache configuration
    """
    global av_cache

    try:
        from app.utils.cache_manager import screener_cache

        cache_dir = Path(settings.cache_dir if hasattr(settings, 'cache_dir') else "backend/data/api_cache")
        av_cache = AlphaVantageCache(cache_dir, screener_cache)
        av_cache.initialize_directories()

        logger.info("Alpha Vantage disk cache initialized")

    except Exception as e:
        logger.error(f"Failed to initialize Alpha Vantage cache: {e}")
        raise


def get_ttl_for_type(cache_type: str, settings=None) -> int:
    """
    Get TTL hours for a cache type.

    Args:
        cache_type: Type of cache
        settings: Optional settings object with custom TTLs

    Returns:
        TTL in hours
    """
    if settings:
        if cache_type == "overview" and hasattr(settings, 'cache_ttl_overview_hours'):
            return settings.cache_ttl_overview_hours
        elif cache_type == "dividends" and hasattr(settings, 'cache_ttl_dividends_hours'):
            return settings.cache_ttl_dividends_hours
        elif cache_type in ["income", "balance", "cashflow"] and hasattr(settings, 'cache_ttl_financials_hours'):
            return settings.cache_ttl_financials_hours

    # Default TTLs
    default_ttls = {
        "overview": 24,
        "dividends": 48,
        "income": 168,
        "balance": 168,
        "cashflow": 168
    }

    return default_ttls.get(cache_type, 24)
