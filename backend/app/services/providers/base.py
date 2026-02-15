"""
Abstract base provider for financial data fetching.

Defines the common interface that all data providers must implement,
plus shared types for provider results, data categories, and
exhaustion tracking.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Any

import httpx


class DataType(str, Enum):
    OVERVIEW = "overview"
    DIVIDENDS = "dividends"
    INCOME = "income"
    BALANCE = "balance"
    CASHFLOW = "cashflow"
    EARNINGS = "earnings"


class ProviderStatus(str, Enum):
    SUCCESS = "success"
    NO_DATA = "no_data"
    PROVIDER_ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class ProviderResult:
    status: ProviderStatus
    data: Optional[Any] = None
    provider_name: str = ""
    error_message: Optional[str] = None
    cached_at: Optional[str] = None
    expires_at: Optional[str] = None


class BaseProvider(ABC):
    """
    Abstract base class for financial data providers.

    Subclasses implement fetch methods for each data type.
    The base class handles rate limit tracking and exhaustion state.
    """

    name: str = "base"
    priority: int = 0

    def __init__(self, settings):
        self.settings = settings
        self._exhausted_until: Optional[datetime] = None
        self._daily_calls: int = 0
        self._daily_reset: datetime = datetime.now()
        self._daily_limit: Optional[int] = None
        self._endpoint_blocked: dict[str, datetime] = {}

    def is_available(self) -> bool:
        if self._exhausted_until and datetime.now() < self._exhausted_until:
            return False
        now = datetime.now()
        if now.date() > self._daily_reset.date():
            self._daily_calls = 0
            self._daily_reset = now
        if self._daily_limit and self._daily_calls >= self._daily_limit:
            return False
        return True

    def mark_exhausted(self, cooldown_minutes: int = 60):
        self._exhausted_until = datetime.now() + timedelta(minutes=cooldown_minutes)

    def is_endpoint_available(self, endpoint: str) -> bool:
        """Check if a specific endpoint is available (not blocked)."""
        blocked_until = self._endpoint_blocked.get(endpoint)
        if blocked_until is None:
            return True
        if datetime.now() >= blocked_until:
            del self._endpoint_blocked[endpoint]
            return True
        return False

    def mark_endpoint_blocked(self, endpoint: str, cooldown_minutes: int = 1440):
        """Mark a specific endpoint as blocked (e.g., paywalled)."""
        self._endpoint_blocked[endpoint] = datetime.now() + timedelta(minutes=cooldown_minutes)

    def record_call(self):
        self._daily_calls += 1

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "priority": self.priority,
            "available": self.is_available(),
            "daily_calls": self._daily_calls,
            "daily_limit": self._daily_limit,
            "exhausted_until": self._exhausted_until.isoformat() if self._exhausted_until else None,
            "blocked_endpoints": len(self._endpoint_blocked),
        }

    async def fetch(
        self,
        data_type: DataType,
        symbol: str,
        client: Optional[httpx.AsyncClient] = None,
        **kwargs,
    ) -> ProviderResult:
        dispatch = {
            DataType.OVERVIEW: self.fetch_overview,
            DataType.DIVIDENDS: self.fetch_dividends,
            DataType.INCOME: self.fetch_income,
            DataType.BALANCE: self.fetch_balance,
            DataType.CASHFLOW: self.fetch_cashflow,
            DataType.EARNINGS: self.fetch_earnings,
        }
        handler = dispatch[data_type]
        result = await handler(symbol, client, **kwargs)
        result.provider_name = self.name
        return result

    @abstractmethod
    async def fetch_overview(self, symbol: str, client, **kwargs) -> ProviderResult:
        pass

    @abstractmethod
    async def fetch_dividends(self, symbol: str, client, **kwargs) -> ProviderResult:
        pass

    @abstractmethod
    async def fetch_income(self, symbol: str, client, **kwargs) -> ProviderResult:
        pass

    @abstractmethod
    async def fetch_balance(self, symbol: str, client, **kwargs) -> ProviderResult:
        pass

    @abstractmethod
    async def fetch_cashflow(self, symbol: str, client, **kwargs) -> ProviderResult:
        pass

    @abstractmethod
    async def fetch_earnings(self, symbol: str, client, **kwargs) -> ProviderResult:
        pass
