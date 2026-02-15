"""
Dividend Screener API routes.

Thin routing layer that delegates to the multi-provider data orchestrator
and analyzer services. Falls back across providers automatically:
Alpha Vantage -> FMP -> Eulerpool -> yfinance.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional, List

from app.models.screener import (
    CompanyOverview, DividendHistory, IncomeStatement,
    BalanceSheet, CashFlow, ScreenerAnalysis, DataFreshnessEntry,
)
from app.services.providers.base import DataType, ProviderStatus
from app.services.screener_analyzer import (
    calculate_dividend_metrics, calculate_risk_factors,
    generate_investment_summary, compute_growth_metrics,
    compute_analyst_sentiment,
)
from app.utils.cache_manager import screener_cache
from app.utils.logging_config import get_logger
from app.utils.validators import validate_ticker

logger = get_logger()

router = APIRouter()


def _get_client(request: Request):
    """Get shared httpx client from app.state, or None."""
    return getattr(request.app.state, "http_client", None)


def _get_orchestrator(request: Request):
    """Get data orchestrator from app.state."""
    orch = getattr(request.app.state, "orchestrator", None)
    if orch is None:
        raise HTTPException(status_code=503, detail="Data orchestrator not initialized")
    return orch


@router.get("/overview/{symbol}", response_model=CompanyOverview)
async def get_company_overview(symbol: str, request: Request):
    """Get company overview data via multi-provider fallback."""
    symbol = validate_ticker(symbol)
    orchestrator = _get_orchestrator(request)
    client = _get_client(request)

    result = await orchestrator.fetch_data(DataType.OVERVIEW, symbol, client)

    if result.status == ProviderStatus.NO_DATA:
        raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")
    if result.status != ProviderStatus.SUCCESS:
        raise HTTPException(status_code=502, detail=f"Failed to fetch overview: {result.error_message}")

    return result.data


@router.get("/dividends/{symbol}", response_model=List[DividendHistory])
async def get_dividend_history(symbol: str, request: Request):
    """Get dividend history via multi-provider fallback."""
    symbol = validate_ticker(symbol)
    orchestrator = _get_orchestrator(request)
    client = _get_client(request)

    result = await orchestrator.fetch_data(DataType.DIVIDENDS, symbol, client)

    if result.status == ProviderStatus.SUCCESS:
        return result.data if result.data else []
    if result.status == ProviderStatus.NO_DATA:
        return []
    raise HTTPException(status_code=502, detail=f"Failed to fetch dividends: {result.error_message}")


@router.get("/income/{symbol}", response_model=List[IncomeStatement])
async def get_income_statement(
    symbol: str,
    request: Request,
    period: str = Query("annual", regex="^(annual|quarterly)$"),
):
    """Get income statement data via multi-provider fallback."""
    symbol = validate_ticker(symbol)
    orchestrator = _get_orchestrator(request)
    client = _get_client(request)

    result = await orchestrator.fetch_data(DataType.INCOME, symbol, client, period=period)

    if result.status == ProviderStatus.SUCCESS:
        return result.data if result.data else []
    if result.status == ProviderStatus.NO_DATA:
        return []
    raise HTTPException(status_code=502, detail=f"Failed to fetch income data: {result.error_message}")


@router.get("/balance/{symbol}", response_model=List[BalanceSheet])
async def get_balance_sheet(
    symbol: str,
    request: Request,
    period: str = Query("annual", regex="^(annual|quarterly)$"),
):
    """Get balance sheet data via multi-provider fallback."""
    symbol = validate_ticker(symbol)
    orchestrator = _get_orchestrator(request)
    client = _get_client(request)

    result = await orchestrator.fetch_data(DataType.BALANCE, symbol, client, period=period)

    if result.status == ProviderStatus.SUCCESS:
        return result.data if result.data else []
    if result.status == ProviderStatus.NO_DATA:
        return []
    raise HTTPException(status_code=502, detail=f"Failed to fetch balance sheet: {result.error_message}")


@router.get("/cashflow/{symbol}", response_model=List[CashFlow])
async def get_cash_flow(
    symbol: str,
    request: Request,
    period: str = Query("annual", regex="^(annual|quarterly)$"),
):
    """Get cash flow data via multi-provider fallback."""
    symbol = validate_ticker(symbol)
    orchestrator = _get_orchestrator(request)
    client = _get_client(request)

    result = await orchestrator.fetch_data(DataType.CASHFLOW, symbol, client, period=period)

    if result.status == ProviderStatus.SUCCESS:
        return result.data if result.data else []
    if result.status == ProviderStatus.NO_DATA:
        return []
    raise HTTPException(status_code=502, detail=f"Failed to fetch cash flow: {result.error_message}")


@router.get("/analysis/{symbol}", response_model=ScreenerAnalysis)
async def get_full_analysis(
    symbol: str,
    request: Request,
    refresh: bool = Query(False, description="Force refresh by clearing cached data"),
    period: str = Query("annual", regex="^(annual|quarterly)$", description="Annual or quarterly financial statements"),
):
    """
    Comprehensive stock analysis combining all data sources.

    Uses the multi-provider orchestrator to fetch all 6 data types
    with automatic fallback across providers. Overview is fetched first
    (needed for cross-references), then remaining types in parallel.
    """
    symbol = validate_ticker(symbol)
    orchestrator = _get_orchestrator(request)
    client = _get_client(request)

    # Force refresh: clear disk cache for this symbol
    if refresh:
        try:
            from app.services.alpha_vantage_cache import av_cache
            if av_cache:
                cleared = av_cache.clear_symbol(symbol)
                logger.info(f"Force refresh: cleared {cleared} cache files for {symbol}")
        except Exception as e:
            logger.warning(f"Failed to clear cache for refresh: {e}")

    # Orchestrator handles parallel fetch + cross-refs internally
    all_results = await orchestrator.fetch_full_analysis(symbol, client, period=period)

    # Overview is required
    overview_result = all_results["overview"]
    if overview_result.status != ProviderStatus.SUCCESS or not overview_result.data:
        raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")

    overview = overview_result.data

    # Extract remaining data (empty lists on failure)
    def _extract(key, default=None):
        r = all_results.get(key)
        if r and r.status == ProviderStatus.SUCCESS and r.data:
            return r.data
        return default if default is not None else []

    dividends = _extract("dividends", [])
    income = _extract("income", [])
    balance = _extract("balance", [])
    cashflow = _extract("cashflow", [])

    quarterly_earnings, annual_earnings = [], []
    earnings_result = all_results.get("earnings")
    if earnings_result and earnings_result.status == ProviderStatus.SUCCESS and earnings_result.data:
        earnings_data = earnings_result.data
        if isinstance(earnings_data, tuple) and len(earnings_data) == 2:
            quarterly_earnings, annual_earnings = earnings_data
        elif isinstance(earnings_data, dict):
            quarterly_earnings = earnings_data.get("quarterly", [])
            annual_earnings = earnings_data.get("annual", [])

    # Build data freshness metadata
    data_freshness = {}
    for key, result in all_results.items():
        data_freshness[key] = DataFreshnessEntry(
            cached_at=result.cached_at,
            expires_at=result.expires_at,
            source=result.provider_name or "unknown",
        )

    # Run analysis
    dividend_metrics = calculate_dividend_metrics(dividends, cashflow)
    risk_factors, risk_score, risk_level, risk_grade = calculate_risk_factors(
        overview, balance, cashflow, dividend_metrics
    )
    investment_summary = generate_investment_summary(overview, dividend_metrics)
    growth_metrics = compute_growth_metrics(income, cashflow, annual_earnings)
    analyst_sentiment = compute_analyst_sentiment(overview)

    return ScreenerAnalysis(
        overview=overview,
        dividends=dividends,
        income_statements=income,
        balance_sheets=balance,
        cash_flows=cashflow,
        dividend_metrics=dividend_metrics,
        risk_factors=risk_factors,
        risk_score=risk_score,
        risk_level=risk_level,
        risk_grade=risk_grade,
        investment_summary=investment_summary,
        quarterly_earnings=quarterly_earnings,
        annual_earnings=annual_earnings,
        growth_metrics=growth_metrics,
        analyst_sentiment=analyst_sentiment,
        data_freshness=data_freshness,
    )


@router.post("/search")
async def search_dividends(
    min_yield: float = Query(default=0.0, description="Minimum dividend yield"),
    max_yield: float = Query(default=100.0, description="Maximum dividend yield"),
):
    """
    Search for dividend stocks.
    Alpha Vantage free tier doesn't support stock screening.
    """
    return {
        "message": "Stock screening requires Alpha Vantage premium. Use /analysis/{symbol} to analyze specific stocks.",
        "suggestion": "Enter a stock symbol in the screener to analyze it.",
        "filters": {"min_yield": min_yield, "max_yield": max_yield},
    }


# ---------------------------------------------------------------------------
# Provider status endpoint
# ---------------------------------------------------------------------------

@router.get("/providers/status")
async def get_providers_status(request: Request):
    """Get status of all configured data providers."""
    orchestrator = _get_orchestrator(request)
    return {
        "providers": orchestrator.get_providers_status(),
        "fallback_enabled": True,
    }


# ---------------------------------------------------------------------------
# Cache management endpoints
# ---------------------------------------------------------------------------

@router.get("/cache/status")
async def get_cache_status():
    """Get current in-memory cache statistics."""
    return screener_cache.stats()


@router.delete("/cache/clear")
async def clear_screener_cache(symbol: Optional[str] = None):
    """Clear in-memory cached responses."""
    if symbol is None:
        stats = screener_cache.stats()
        count = stats["size"]
        screener_cache.clear()
        return {"cleared": count, "message": "All in-memory cache entries cleared"}

    symbol_upper = symbol.upper()
    cleared = 0
    for prefix in ["overview", "dividends", "income", "balance", "cashflow", "earnings", "analysis"]:
        if screener_cache.delete(f"{prefix}:{symbol_upper}"):
            cleared += 1

    return {"cleared": cleared, "symbol": symbol_upper}


@router.get("/cache/disk/stats")
async def get_disk_cache_stats():
    """Get disk cache statistics and metadata."""
    from app.config import get_settings
    settings = get_settings()

    if not (hasattr(settings, 'cache_enabled') and settings.cache_enabled):
        return {"enabled": False, "message": "Disk cache is disabled"}

    try:
        from app.services.alpha_vantage_cache import av_cache

        if not av_cache:
            return {"enabled": True, "initialized": False, "message": "Cache not initialized"}

        stats = av_cache.get_metadata_stats()
        return {"enabled": True, "initialized": True, **stats}

    except Exception as e:
        logger.error(f"Error getting disk cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cache statistics: {str(e)}")


@router.delete("/cache/disk/clear")
async def clear_disk_cache(
    cache_type: Optional[str] = Query(None, description="Cache type to clear"),
    symbol: Optional[str] = Query(None, description="Symbol to clear"),
):
    """Clear disk cache entries by type, symbol, or all."""
    from app.config import get_settings
    settings = get_settings()

    if not (hasattr(settings, 'cache_enabled') and settings.cache_enabled):
        return {"enabled": False, "message": "Disk cache is disabled"}

    try:
        from app.services.alpha_vantage_cache import av_cache

        if not av_cache:
            return {"enabled": True, "initialized": False, "message": "Cache not initialized"}

        if symbol:
            count = av_cache.clear_symbol(symbol)
            return {"cleared": count, "symbol": symbol.upper(), "message": f"Cleared {count} cache files for {symbol.upper()}"}

        if cache_type:
            valid_types = ["overview", "dividends", "income", "balance", "cashflow", "earnings"]
            if cache_type not in valid_types:
                raise HTTPException(status_code=400, detail=f"Invalid cache type: {cache_type}. Must be one of: {', '.join(valid_types)}")
            count = av_cache.clear_type(cache_type)
            return {"cleared": count, "cache_type": cache_type, "message": f"Cleared {count} cache files for type {cache_type}"}

        total_cleared = 0
        for type_name in ["overview", "dividends", "income", "balance", "cashflow", "earnings"]:
            total_cleared += av_cache.clear_type(type_name)

        return {"cleared": total_cleared, "message": f"Cleared all {total_cleared} disk cache files"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing disk cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.post("/cache/warm")
async def warm_cache_manually():
    """Manually trigger cache warming from disk."""
    from app.config import get_settings
    settings = get_settings()

    if not (hasattr(settings, 'cache_enabled') and settings.cache_enabled):
        return {"enabled": False, "message": "Disk cache is disabled"}

    try:
        from app.services.alpha_vantage_cache import av_cache

        if not av_cache:
            return {"enabled": True, "initialized": False, "message": "Cache not initialized"}

        loaded_count = av_cache.warm_cache_from_disk()
        return {"success": True, "entries_loaded": loaded_count, "message": f"Cache warmed: {loaded_count} entries loaded from disk"}

    except Exception as e:
        logger.error(f"Error warming cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")
