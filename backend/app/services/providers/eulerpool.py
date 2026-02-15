"""
Eulerpool provider implementation (stub-first).

Tertiary provider (priority 2). Uses ISIN-based identification.
Limited public documentation -- overview endpoint implemented,
other methods gracefully fall through to next provider.
"""

import json
import httpx
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.utils.logging_config import get_logger
from app.models.screener import CompanyOverview, safe_float
from .base import BaseProvider, ProviderResult, ProviderStatus

logger = get_logger()

# Common US stock ISIN prefixes (ticker -> ISIN lookup fallback)
# ISINs follow: country(2) + CUSIP(9) + check(1)
KNOWN_ISINS = {
    "AAPL": "US0378331005",
    "MSFT": "US5949181045",
    "GOOGL": "US02079K3059",
    "AMZN": "US0231351067",
    "META": "US30303M1027",
    "TSLA": "US88160R1014",
    "JNJ": "US4781601046",
    "KO": "US1912161007",
    "PG": "US7427181091",
    "JPM": "US46625H1005",
}


class EulerpoolProvider(BaseProvider):
    name = "eulerpool"
    priority = 2

    def __init__(self, settings):
        super().__init__(settings)
        self._daily_limit = 330  # ~10k/month
        self._api_key = settings.eulerpool_api_key
        self._base_url = getattr(settings, 'eulerpool_base_url', 'https://api.eulerpool.com/api/1')
        self._isin_cache: dict[str, str] = {}
        self._load_isin_cache()

    def _load_isin_cache(self):
        """Load ticker->ISIN mapping from disk cache."""
        self._isin_cache = dict(KNOWN_ISINS)
        try:
            settings = get_settings()
            cache_file = Path(settings.cache_dir) / "isin_map.json"
            if cache_file.exists():
                with open(cache_file) as f:
                    stored = json.load(f)
                self._isin_cache.update(stored)
        except Exception:
            pass

    def _save_isin(self, ticker: str, isin: str):
        """Persist a new ticker->ISIN mapping."""
        self._isin_cache[ticker.upper()] = isin
        try:
            settings = get_settings()
            cache_file = Path(settings.cache_dir) / "isin_map.json"
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump(self._isin_cache, f, indent=2)
        except Exception:
            pass

    def _get_isin(self, ticker: str) -> Optional[str]:
        return self._isin_cache.get(ticker.upper())

    async def _fetch_eulerpool(
        self, endpoint: str, client: Optional[httpx.AsyncClient],
    ) -> tuple[Optional[dict], ProviderStatus]:
        self.record_call()
        url = f"{self._base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {self._api_key}"}

        try:
            if client:
                response = await client.get(url, headers=headers)
            else:
                async with httpx.AsyncClient(timeout=30.0) as c:
                    response = await c.get(url, headers=headers)

            if response.status_code == 429:
                self.mark_exhausted(cooldown_minutes=60)
                return None, ProviderStatus.RATE_LIMITED
            if response.status_code in (401, 403):
                logger.warning("Eulerpool auth failed")
                self.mark_exhausted(cooldown_minutes=1440)
                return None, ProviderStatus.PROVIDER_ERROR
            if response.status_code == 404:
                return None, ProviderStatus.NO_DATA

            response.raise_for_status()
            data = response.json()
            return data, ProviderStatus.SUCCESS

        except httpx.HTTPError as e:
            logger.error(f"Eulerpool HTTP error: {e}")
            return None, ProviderStatus.PROVIDER_ERROR
        except Exception as e:
            logger.error(f"Eulerpool error: {e}")
            return None, ProviderStatus.PROVIDER_ERROR

    async def fetch_overview(self, symbol, client, **kwargs):
        isin = self._get_isin(symbol)
        if not isin:
            logger.info(f"Eulerpool: no ISIN for {symbol}, skipping")
            return ProviderResult(status=ProviderStatus.PROVIDER_ERROR, error_message="No ISIN mapping")

        data, status = await self._fetch_eulerpool(f"equity/profile/{isin}", client)
        if status != ProviderStatus.SUCCESS or not data:
            return ProviderResult(status=status)

        return ProviderResult(
            status=ProviderStatus.SUCCESS,
            data=CompanyOverview(
                symbol=symbol.upper(),
                name=data.get("name", "Unknown"),
                sector=data.get("sector"),
                industry=data.get("industry"),
                exchange=data.get("exchange"),
                currency=data.get("currency"),
                current_price=safe_float(data.get("price")),
                market_cap=safe_float(data.get("market_cap") or data.get("marketCap")),
                pe_ratio=safe_float(data.get("pe_ratio") or data.get("peRatio")),
                dividend_yield=safe_float(data.get("dividend_yield") or data.get("dividendYield")),
            ),
        )

    async def fetch_dividends(self, symbol, client, **kwargs):
        # Eulerpool dividend endpoints not yet confirmed
        return ProviderResult(
            status=ProviderStatus.PROVIDER_ERROR,
            error_message="Eulerpool dividends not yet implemented",
        )

    async def fetch_income(self, symbol, client, **kwargs):
        return ProviderResult(
            status=ProviderStatus.PROVIDER_ERROR,
            error_message="Eulerpool income not yet implemented",
        )

    async def fetch_balance(self, symbol, client, **kwargs):
        return ProviderResult(
            status=ProviderStatus.PROVIDER_ERROR,
            error_message="Eulerpool balance not yet implemented",
        )

    async def fetch_cashflow(self, symbol, client, **kwargs):
        return ProviderResult(
            status=ProviderStatus.PROVIDER_ERROR,
            error_message="Eulerpool cashflow not yet implemented",
        )

    async def fetch_earnings(self, symbol, client, **kwargs):
        return ProviderResult(
            status=ProviderStatus.PROVIDER_ERROR,
            error_message="Eulerpool earnings not yet implemented",
        )
