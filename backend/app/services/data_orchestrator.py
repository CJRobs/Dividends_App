"""
Data orchestration service for multi-provider fallback.

Coordinates fetching financial data across multiple providers,
checking the normalized disk cache first, then trying providers
in priority order. Only falls back on provider errors or rate
limits, NOT on "no data for symbol" responses.
"""

import asyncio
from typing import Optional, List, Dict, Any, Tuple

import httpx

from app.config import get_settings
from app.utils.logging_config import get_logger
from app.services.providers.base import (
    BaseProvider, ProviderResult, ProviderStatus, DataType,
)
from app.models.screener import (
    CompanyOverview, DividendHistory, IncomeStatement,
    BalanceSheet, CashFlow, EarningsData, AnnualEarnings,
)

logger = get_logger()

# Sentinel value stored in disk cache to represent "all providers failed"
_NEGATIVE_CACHE_SENTINEL = {"__negative_cache__": True}
_NEGATIVE_CACHE_TTL_HOURS = 1


class DataOrchestrator:
    def __init__(self, providers: List[BaseProvider]):
        self.providers = sorted(providers, key=lambda p: p.priority)

    def get_providers_status(self) -> List[dict]:
        return [p.get_status() for p in self.providers]

    @staticmethod
    def _cache_type_key(data_type: DataType, period: str = "annual") -> str:
        """Build cache type key, appending _quarterly when needed."""
        base = data_type.value
        return f"{base}_quarterly" if period == "quarterly" else base

    async def fetch_data(
        self,
        data_type: DataType,
        symbol: str,
        client: Optional[httpx.AsyncClient] = None,
        **kwargs,
    ) -> ProviderResult:
        """Fetch data with fallback across providers."""
        period = kwargs.get("period", "annual")
        cache_key = self._cache_type_key(data_type, period)

        # Check normalized disk cache first
        cache_result = self._check_cache(data_type, symbol, cache_key)
        if cache_result is not None:
            cached_data, cache_meta = cache_result
            if cached_data is _NEGATIVE_CACHE_SENTINEL:
                logger.debug(f"Negative cache hit for {cache_key}:{symbol}")
                return ProviderResult(
                    status=ProviderStatus.PROVIDER_ERROR,
                    error_message="All providers failed (cached, retrying later)",
                )
            return ProviderResult(
                status=ProviderStatus.SUCCESS,
                data=cached_data,
                provider_name="cache",
                cached_at=cache_meta.get("cached_at") if cache_meta else None,
                expires_at=cache_meta.get("expires_at") if cache_meta else None,
            )

        # Try providers in priority order
        for provider in self.providers:
            if not provider.is_available():
                logger.debug(f"Skipping {provider.name} for {cache_key}:{symbol} (exhausted)")
                continue

            logger.info(f"Trying {provider.name} for {cache_key}:{symbol}")
            try:
                result = await provider.fetch(data_type, symbol, client, **kwargs)
            except Exception as e:
                logger.error(f"{provider.name} exception for {cache_key}:{symbol}: {e}")
                continue

            if result.status == ProviderStatus.SUCCESS:
                self._save_to_cache(data_type, symbol, result, cache_key)
                logger.info(f"{provider.name} success for {cache_key}:{symbol}")
                return result

            if result.status == ProviderStatus.NO_DATA:
                logger.info(f"{provider.name}: no data for {symbol} ({cache_key}), not falling back")
                return result

            # RATE_LIMITED or PROVIDER_ERROR: try next
            logger.warning(
                f"{provider.name} failed for {cache_key}:{symbol}: "
                f"{result.status.value} - {result.error_message or ''}"
            )

        # Save negative cache entry to avoid re-trying immediately
        self._save_negative_cache(symbol, cache_key)

        return ProviderResult(
            status=ProviderStatus.PROVIDER_ERROR,
            error_message="All providers exhausted",
        )

    async def fetch_full_analysis(
        self,
        symbol: str,
        client: Optional[httpx.AsyncClient] = None,
        period: str = "annual",
    ) -> Dict[str, ProviderResult]:
        """
        Fetch all data types for a full analysis.

        Phase 1: Fetch overview first (needed for cross-refs: shares, price).
        Phase 2: Fetch income, dividends, balance, earnings in parallel.
        Phase 3: Fetch cashflow with revenue_by_year extracted from income.
        """
        # Phase 1: Overview (sequential — always annual)
        overview_result = await self.fetch_data(DataType.OVERVIEW, symbol, client)

        shares = None
        price = None
        if overview_result.status == ProviderStatus.SUCCESS and overview_result.data:
            overview = overview_result.data
            shares = getattr(overview, 'shares_outstanding', None)
            price = getattr(overview, 'current_price', None)

        # Phase 2: Income, dividends, balance, earnings in parallel
        phase2 = await asyncio.gather(
            self.fetch_data(DataType.DIVIDENDS, symbol, client),
            self.fetch_data(DataType.INCOME, symbol, client, shares_outstanding=shares, period=period),
            self.fetch_data(DataType.BALANCE, symbol, client, period=period),
            self.fetch_data(DataType.EARNINGS, symbol, client),
            return_exceptions=True,
        )

        def _safe_result(r, idx: int) -> ProviderResult:
            if isinstance(r, Exception):
                logger.error(f"gather exception at index {idx}: {r}")
                return ProviderResult(status=ProviderStatus.PROVIDER_ERROR, error_message=str(r))
            return r

        dividends_result = _safe_result(phase2[0], 0)
        income_result = _safe_result(phase2[1], 1)
        balance_result = _safe_result(phase2[2], 2)
        earnings_result = _safe_result(phase2[3], 3)

        # Phase 3: Cashflow with revenue_by_year from income data
        revenue_by_year = self._extract_revenue_by_year(income_result)
        cashflow_result = await self.fetch_data(
            DataType.CASHFLOW, symbol, client,
            shares_outstanding=shares, current_price=price,
            revenue_by_year=revenue_by_year, period=period,
        )

        return {
            "overview": overview_result,
            "dividends": dividends_result,
            "income": income_result,
            "balance": balance_result,
            "cashflow": cashflow_result,
            "earnings": earnings_result,
        }

    def _extract_revenue_by_year(self, income_result: ProviderResult) -> Optional[Dict[str, float]]:
        """Extract year -> revenue mapping from income statement data."""
        if income_result.status != ProviderStatus.SUCCESS or not income_result.data:
            return None
        revenue_by_year = {}
        for stmt in income_result.data:
            fiscal_date = getattr(stmt, 'fiscal_date', '')
            revenue = getattr(stmt, 'total_revenue', None)
            if fiscal_date and revenue is not None:
                revenue_by_year[fiscal_date[:4]] = revenue
        return revenue_by_year if revenue_by_year else None

    def _check_cache(self, data_type: DataType, symbol: str, cache_key: str = "") -> Optional[Tuple[Any, Optional[dict]]]:
        """Check disk cache. Returns (data, metadata) tuple or None."""
        if not cache_key:
            cache_key = data_type.value
        settings = get_settings()
        if not settings.cache_enabled:
            return None
        try:
            from app.services.alpha_vantage_cache import av_cache
            if av_cache:
                result = av_cache.get_with_metadata(cache_key, symbol)
                if result is not None:
                    data, metadata = result
                    if isinstance(data, dict) and data.get("__negative_cache__"):
                        return (_NEGATIVE_CACHE_SENTINEL, metadata)
                    return (self._deserialize_from_cache(data_type, data), metadata)
        except Exception:
            pass
        return None

    def _deserialize_from_cache(self, data_type: DataType, data: Any) -> Any:
        """Convert cached dicts back into Pydantic model instances."""
        model_map = {
            DataType.OVERVIEW: CompanyOverview,
            DataType.DIVIDENDS: DividendHistory,
            DataType.INCOME: IncomeStatement,
            DataType.BALANCE: BalanceSheet,
            DataType.CASHFLOW: CashFlow,
        }

        if data_type == DataType.EARNINGS:
            if isinstance(data, dict) and "quarterly" in data:
                quarterly = [EarningsData(**item) if isinstance(item, dict) else item for item in data.get("quarterly", [])]
                annual = [AnnualEarnings(**item) if isinstance(item, dict) else item for item in data.get("annual", [])]
                return (quarterly, annual)
            return data

        model_cls = model_map.get(data_type)
        if model_cls is None:
            return data

        if isinstance(data, dict):
            return model_cls(**data)
        if isinstance(data, list):
            return [model_cls(**item) if isinstance(item, dict) else item for item in data]
        return data

    def _save_negative_cache(self, symbol: str, cache_key: str):
        """Cache a negative result to avoid re-trying immediately."""
        settings = get_settings()
        if not settings.cache_enabled:
            return
        try:
            from app.services.alpha_vantage_cache import av_cache
            if av_cache:
                av_cache.set(cache_key, symbol, _NEGATIVE_CACHE_SENTINEL, _NEGATIVE_CACHE_TTL_HOURS)
                logger.info(f"Negative cache set for {cache_key}:{symbol} (TTL: {_NEGATIVE_CACHE_TTL_HOURS}h)")
        except Exception as e:
            logger.warning(f"Failed to set negative cache for {cache_key}:{symbol}: {e}")

    def _save_to_cache(self, data_type: DataType, symbol: str, result: ProviderResult, cache_key: str = ""):
        if not cache_key:
            cache_key = data_type.value
        settings = get_settings()
        if not settings.cache_enabled or result.data is None:
            return
        try:
            from app.services.alpha_vantage_cache import av_cache, get_ttl_for_type
            if av_cache:
                ttl = get_ttl_for_type(cache_key, settings)
                # Serialize Pydantic models for disk cache
                data = self._serialize_for_cache(result.data)
                av_cache.set(cache_key, symbol, data, ttl)
        except Exception as e:
            logger.warning(f"Failed to cache {cache_key}:{symbol}: {e}")

    def _serialize_for_cache(self, data: Any) -> Any:
        """Convert Pydantic models to dicts for JSON serialization."""
        if hasattr(data, 'model_dump'):
            return data.model_dump()
        if isinstance(data, list):
            return [
                item.model_dump() if hasattr(item, 'model_dump') else item
                for item in data
            ]
        if isinstance(data, tuple) and len(data) == 2:
            # Earnings tuple: (quarterly, annual)
            return {
                "quarterly": [
                    item.model_dump() if hasattr(item, 'model_dump') else item
                    for item in data[0]
                ],
                "annual": [
                    item.model_dump() if hasattr(item, 'model_dump') else item
                    for item in data[1]
                ],
            }
        return data


# Global instance (initialized in main.py lifespan)
orchestrator: Optional[DataOrchestrator] = None
