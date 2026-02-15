"""
Alpha Vantage provider implementation.

Wraps the existing Alpha Vantage fetcher and mappers into the
BaseProvider interface. Primary provider (priority 0).
"""

import httpx
from typing import Optional

from app.config import get_settings
from app.utils.logging_config import get_logger
from app.services.alpha_vantage_fetcher import (
    map_overview, map_dividends, map_income_statements,
    map_balance_sheets, map_cash_flows, map_earnings,
    rate_limit_async,
)
from .base import BaseProvider, ProviderResult, ProviderStatus

logger = get_logger()


class AlphaVantageProvider(BaseProvider):
    name = "alpha_vantage"
    priority = 0

    def __init__(self, settings):
        super().__init__(settings)
        self._daily_limit = 25

    async def _fetch_raw(
        self, function: str, symbol: str, client: Optional[httpx.AsyncClient]
    ) -> tuple[Optional[dict], ProviderStatus]:
        """
        Make raw AV API call with rate limiting and error detection.
        Returns (data, status) tuple.
        """
        await rate_limit_async()
        self.record_call()

        try:
            params = {
                "function": function,
                "symbol": symbol.upper(),
                "apikey": self.settings.alpha_vantage_api_key,
            }
            if "TIME_SERIES" in function:
                params["outputsize"] = "compact"

            if client:
                response = await client.get(self.settings.api_base_url, params=params)
            else:
                async with httpx.AsyncClient(timeout=30.0) as c:
                    response = await c.get(self.settings.api_base_url, params=params)

            response.raise_for_status()
            data = response.json()

            if "Note" in data or "Information" in data:
                msg = data.get("Note") or data.get("Information")
                logger.warning(f"AV rate limit: {msg}")
                self.mark_exhausted(cooldown_minutes=60)
                return None, ProviderStatus.RATE_LIMITED
            if "Error Message" in data:
                logger.info(f"AV no data for {symbol}: {data['Error Message']}")
                return None, ProviderStatus.NO_DATA

            return data, ProviderStatus.SUCCESS

        except httpx.HTTPError as e:
            logger.error(f"AV HTTP error for {function}/{symbol}: {e}")
            return None, ProviderStatus.PROVIDER_ERROR
        except Exception as e:
            logger.error(f"AV fetch error for {function}/{symbol}: {e}")
            return None, ProviderStatus.PROVIDER_ERROR

    async def fetch_overview(self, symbol, client, **kwargs):
        data, status = await self._fetch_raw("OVERVIEW", symbol, client)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        if not data or "Symbol" not in data:
            return ProviderResult(status=ProviderStatus.NO_DATA)
        return ProviderResult(status=ProviderStatus.SUCCESS, data=map_overview(data))

    async def fetch_dividends(self, symbol, client, **kwargs):
        data, status = await self._fetch_raw("TIME_SERIES_MONTHLY_ADJUSTED", symbol, client)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        dividends = map_dividends(data) if data else []
        return ProviderResult(status=ProviderStatus.SUCCESS, data=dividends)

    async def fetch_income(self, symbol, client, **kwargs):
        data, status = await self._fetch_raw("INCOME_STATEMENT", symbol, client)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        shares = kwargs.get("shares_outstanding")
        period = kwargs.get("period", "annual")
        statements = map_income_statements(data, shares, period=period) if data else []
        return ProviderResult(status=ProviderStatus.SUCCESS, data=statements)

    async def fetch_balance(self, symbol, client, **kwargs):
        data, status = await self._fetch_raw("BALANCE_SHEET", symbol, client)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        period = kwargs.get("period", "annual")
        sheets = map_balance_sheets(data, period=period) if data else []
        return ProviderResult(status=ProviderStatus.SUCCESS, data=sheets)

    async def fetch_cashflow(self, symbol, client, **kwargs):
        data, status = await self._fetch_raw("CASH_FLOW", symbol, client)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        shares = kwargs.get("shares_outstanding")
        price = kwargs.get("current_price")
        revenue_by_year = kwargs.get("revenue_by_year")
        period = kwargs.get("period", "annual")
        flows = map_cash_flows(data, shares, price, revenue_by_year, period=period) if data else []
        return ProviderResult(status=ProviderStatus.SUCCESS, data=flows)

    async def fetch_earnings(self, symbol, client, **kwargs):
        data, status = await self._fetch_raw("EARNINGS", symbol, client)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        if data:
            quarterly, annual = map_earnings(data)
        else:
            quarterly, annual = [], []
        return ProviderResult(status=ProviderStatus.SUCCESS, data=(quarterly, annual))
