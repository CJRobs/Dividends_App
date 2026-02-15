"""
Upcoming dividend calendar service.

Fetches upcoming ex-dividend dates for portfolio stocks.
Tries FMP's dividends-calendar endpoint first, falls back to
yfinance per-stock lookups.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import httpx

from app.config import get_settings
from app.utils.logging_config import get_logger
from app.models.calendar import UpcomingDividendLive

logger = get_logger()


async def fetch_upcoming_dividends(
    tickers: List[str],
    company_names: Dict[str, str],
    days: int = 90,
) -> List[UpcomingDividendLive]:
    """
    Fetch upcoming dividend dates for portfolio tickers.

    Strategy: Try FMP dividends-calendar first (single API call for all stocks).
    If FMP is unavailable (no key, 402 premium, error), fall back to yfinance
    per-stock lookups.
    """
    settings = get_settings()
    ticker_set = {t.upper() for t in tickers}
    cutoff = datetime.now().date() + timedelta(days=days)
    today = datetime.now().date()

    # Try FMP first
    if settings.fmp_api_key:
        fmp_results = await _fetch_fmp_calendar(
            ticker_set, company_names, today, cutoff, settings
        )
        if fmp_results is not None:
            return fmp_results
        logger.info("FMP calendar unavailable, falling back to yfinance")

    # Fallback: yfinance per-stock
    return await _fetch_yfinance_upcoming(
        list(ticker_set), company_names, today, cutoff
    )


async def _fetch_fmp_calendar(
    ticker_set: set,
    company_names: Dict[str, str],
    today,
    cutoff,
    settings,
) -> Optional[List[UpcomingDividendLive]]:
    """
    Fetch from FMP dividends-calendar endpoint.
    Returns None if the endpoint is unavailable (premium, error).
    """
    url = f"{settings.fmp_base_url}/dividends-calendar"
    params = {"apikey": settings.fmp_api_key}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)

            if response.status_code == 402:
                logger.warning("FMP dividends-calendar requires premium (402)")
                return None

            if response.status_code == 403:
                logger.warning("FMP authentication failed (403)")
                return None

            if response.status_code == 429:
                logger.warning("FMP rate limit hit")
                return None

            response.raise_for_status()
            data = response.json()

        if not isinstance(data, list):
            logger.warning(f"FMP calendar returned unexpected format: {type(data)}")
            return None

        results = []
        for item in data:
            symbol = (item.get("symbol") or "").upper()
            if symbol not in ticker_set:
                continue

            ex_date_str = item.get("date", "")
            if not ex_date_str:
                continue

            try:
                ex_date = datetime.strptime(ex_date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            if ex_date < today or ex_date > cutoff:
                continue

            results.append(UpcomingDividendLive(
                ticker=symbol,
                company_name=company_names.get(symbol, symbol),
                ex_date=ex_date_str,
                amount=_safe_float(item.get("dividend")),
                payment_date=item.get("paymentDate") or None,
                record_date=item.get("recordDate") or None,
                declaration_date=item.get("declarationDate") or None,
                source="fmp",
            ))

        logger.info(f"FMP calendar: {len(results)} upcoming dividends for portfolio")
        return sorted(results, key=lambda r: r.ex_date)

    except httpx.HTTPError as e:
        logger.error(f"FMP calendar HTTP error: {e}")
        return None
    except Exception as e:
        logger.error(f"FMP calendar error: {e}")
        return None


async def _fetch_yfinance_upcoming(
    tickers: List[str],
    company_names: Dict[str, str],
    today,
    cutoff,
) -> List[UpcomingDividendLive]:
    """
    Fetch upcoming ex-dividend dates from yfinance per-stock.
    Runs all lookups in parallel via asyncio.to_thread.
    """

    async def _check_ticker(symbol: str) -> Optional[UpcomingDividendLive]:
        try:
            def _sync():
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                info = ticker.info
                if not info:
                    return None

                ex_div_ts = info.get("exDividendDate")
                if ex_div_ts is None:
                    return None

                # Convert Unix timestamp to date
                if isinstance(ex_div_ts, (int, float)):
                    ex_date = datetime.fromtimestamp(ex_div_ts).date()
                else:
                    return None

                if ex_date < today or ex_date > cutoff:
                    return None

                amount = None
                div_rate = info.get("dividendRate")
                if div_rate is not None:
                    try:
                        amount = float(div_rate)
                    except (ValueError, TypeError):
                        pass

                return UpcomingDividendLive(
                    ticker=symbol,
                    company_name=company_names.get(symbol, info.get("shortName", symbol)),
                    ex_date=ex_date.isoformat(),
                    amount=amount,
                    source="yfinance",
                )

            return await asyncio.to_thread(_sync)
        except Exception as e:
            logger.debug(f"yfinance upcoming check failed for {symbol}: {e}")
            return None

    tasks = [_check_ticker(t) for t in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    upcoming = []
    for r in results:
        if isinstance(r, UpcomingDividendLive):
            upcoming.append(r)

    logger.info(f"yfinance: {len(upcoming)} upcoming dividends from {len(tickers)} tickers")
    return sorted(upcoming, key=lambda r: r.ex_date)


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        f = float(val)
        return f if f > 0 else None
    except (ValueError, TypeError):
        return None
