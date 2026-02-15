"""
Alpha Vantage API data fetching service.

Handles API communication, rate limiting, disk caching,
and mapping raw JSON responses to Pydantic models.
"""

import httpx
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from app.config import get_settings
from app.utils.logging_config import get_logger
from app.models.screener import (
    CompanyOverview, DividendHistory, IncomeStatement,
    BalanceSheet, CashFlow, EarningsData, AnnualEarnings,
    safe_float,
)

logger = get_logger()

# Rate limiting state for Alpha Vantage free tier
_last_av_request: Optional[datetime] = None
_av_lock = asyncio.Lock()


def function_to_cache_type(function: str) -> str:
    """Map Alpha Vantage function name to cache type."""
    if function == "OVERVIEW":
        return "overview"
    elif "TIME_SERIES" in function or "DIVIDEND" in function:
        return "dividends"
    elif "INCOME_STATEMENT" in function:
        return "income"
    elif "BALANCE_SHEET" in function:
        return "balance"
    elif "CASH_FLOW" in function:
        return "cashflow"
    elif function == "EARNINGS":
        return "earnings"
    else:
        return "overview"


async def rate_limit_async():
    """
    Async rate limit for Alpha Vantage API.
    Free tier: 5 calls/min, 25 calls/day. We enforce 1 call/second minimum.
    """
    global _last_av_request

    async with _av_lock:
        if _last_av_request:
            elapsed = (datetime.now() - _last_av_request).total_seconds()
            if elapsed < 1.0:
                await asyncio.sleep(1.0 - elapsed)
        _last_av_request = datetime.now()


async def fetch_alpha_vantage(
    function: str,
    symbol: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Optional[Dict[str, Any]]:
    """
    Fetch from Alpha Vantage API with rate limiting and disk caching.

    Args:
        function: Alpha Vantage API function name
        symbol: Stock ticker symbol
        client: Optional shared httpx.AsyncClient for connection pooling
    """
    settings = get_settings()

    # Check disk cache first (before rate limiting)
    if hasattr(settings, 'cache_enabled') and settings.cache_enabled:
        try:
            from app.services.alpha_vantage_cache import av_cache, get_ttl_for_type

            if av_cache:
                cache_type = function_to_cache_type(function)
                cached_data = av_cache.get(cache_type, symbol)

                if cached_data:
                    logger.debug(f"Disk cache hit for {function}:{symbol}")
                    return cached_data
        except Exception as e:
            logger.warning(f"Error checking disk cache: {e}")

    # Apply rate limiting before API call
    await rate_limit_async()

    try:
        params = {
            "function": function,
            "symbol": symbol.upper(),
            "apikey": settings.alpha_vantage_api_key,
        }

        if "TIME_SERIES" in function:
            params["outputsize"] = "compact"

        if client:
            response = await client.get(settings.api_base_url, params=params)
        else:
            async with httpx.AsyncClient(timeout=30.0) as c:
                response = await c.get(settings.api_base_url, params=params)

        response.raise_for_status()
        data = response.json()

        # Check for API errors
        if "Error Message" in data:
            logger.warning(f"Alpha Vantage API error for {symbol}: {data.get('Error Message')}")
            return None
        if "Note" in data:
            logger.warning(f"Alpha Vantage rate limit hit: {data.get('Note')}")
            return None
        if "Information" in data:
            logger.info(f"Alpha Vantage: {data.get('Information')}")
            return None

        # Save successful response to disk cache
        if hasattr(settings, 'cache_enabled') and settings.cache_enabled:
            try:
                from app.services.alpha_vantage_cache import av_cache, get_ttl_for_type

                if av_cache:
                    cache_type = function_to_cache_type(function)
                    ttl_hours = get_ttl_for_type(cache_type, settings)
                    av_cache.set(cache_type, symbol, data, ttl_hours)
            except Exception as e:
                logger.warning(f"Error saving to disk cache: {e}")

        return data
    except httpx.HTTPError as e:
        logger.error(f"HTTP error for {function}/{symbol}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Fetch error for {function}/{symbol}: {e}", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Mapping functions: raw Alpha Vantage JSON -> Pydantic models
# ---------------------------------------------------------------------------

def map_overview(data: Dict[str, Any]) -> CompanyOverview:
    """Map raw OVERVIEW JSON to CompanyOverview with all available fields."""
    def safe_int(val: Any) -> Optional[int]:
        f = safe_float(val)
        return int(f) if f is not None else None

    return CompanyOverview(
        symbol=data.get("Symbol", ""),
        name=data.get("Name", "Unknown"),
        description=data.get("Description"),
        sector=data.get("Sector"),
        industry=data.get("Industry"),
        exchange=data.get("Exchange"),
        currency=data.get("Currency"),
        current_price=safe_float(data.get("50DayMovingAverage")),
        shares_outstanding=safe_float(data.get("SharesOutstanding")),
        market_cap=safe_float(data.get("MarketCapitalization")),
        pe_ratio=safe_float(data.get("PERatio")),
        forward_pe=safe_float(data.get("ForwardPE")),
        trailing_pe=safe_float(data.get("TrailingPE")),
        peg_ratio=safe_float(data.get("PEGRatio")),
        dividend_yield=safe_float(data.get("DividendYield")),
        dividend_per_share=safe_float(data.get("DividendPerShare")),
        dividend_date=data.get("DividendDate"),
        eps=safe_float(data.get("EPS")),
        beta=safe_float(data.get("Beta")),
        fifty_two_week_high=safe_float(data.get("52WeekHigh")),
        fifty_two_week_low=safe_float(data.get("52WeekLow")),
        book_value=safe_float(data.get("BookValue")),
        profit_margin=safe_float(data.get("ProfitMargin")),
        operating_margin=safe_float(data.get("OperatingMarginTTM")),
        return_on_equity=safe_float(data.get("ReturnOnEquityTTM")),
        revenue_ttm=safe_float(data.get("RevenueTTM")),
        gross_profit_ttm=safe_float(data.get("GrossProfitTTM")),
        ex_dividend_date=data.get("ExDividendDate"),
        payout_ratio=safe_float(data.get("PayoutRatio")),
        price_to_sales_ratio=safe_float(data.get("PriceToSalesRatioTTM")),
        price_to_book_ratio=safe_float(data.get("PriceToBookRatio")),
        ev_to_revenue=safe_float(data.get("EVToRevenue")),
        ev_to_ebitda=safe_float(data.get("EVToEBITDA")),
        analyst_target_price=safe_float(data.get("AnalystTargetPrice")),
        analyst_rating_strong_buy=safe_int(data.get("AnalystRatingStrongBuy")),
        analyst_rating_buy=safe_int(data.get("AnalystRatingBuy")),
        analyst_rating_hold=safe_int(data.get("AnalystRatingHold")),
        analyst_rating_sell=safe_int(data.get("AnalystRatingSell")),
        analyst_rating_strong_sell=safe_int(data.get("AnalystRatingStrongSell")),
        quarterly_earnings_growth_yoy=safe_float(data.get("QuarterlyEarningsGrowthYOY")),
        quarterly_revenue_growth_yoy=safe_float(data.get("QuarterlyRevenueGrowthYOY")),
    )


def map_dividends(data: Dict[str, Any]) -> List[DividendHistory]:
    """Map TIME_SERIES_MONTHLY_ADJUSTED response to dividend history."""
    if not data or "Monthly Adjusted Time Series" not in data:
        return []

    monthly_data = data["Monthly Adjusted Time Series"]
    dividends = []

    for date_str, values in monthly_data.items():
        dividend_amount = safe_float(values.get("7. dividend amount", 0))
        if dividend_amount and dividend_amount > 0:
            dividends.append(DividendHistory(
                ex_date=date_str,
                amount=dividend_amount,
            ))

    dividends.sort(key=lambda x: x.ex_date, reverse=True)
    return dividends[:20]


def map_income_statements(
    data: Dict[str, Any],
    shares_outstanding: Optional[float] = None,
    period: str = "annual",
) -> List[IncomeStatement]:
    """Map INCOME_STATEMENT response with computed margins and growth."""
    report_key = "quarterlyReports" if period == "quarterly" else "annualReports"
    if not data or report_key not in data:
        return []

    limit = 8 if period == "quarterly" else 5
    reports = data.get(report_key, [])[:limit]
    statements = []

    for i, item in enumerate(reports):
        total_revenue = safe_float(item.get("totalRevenue"))
        gross_profit = safe_float(item.get("grossProfit"))
        operating_income = safe_float(item.get("operatingIncome"))
        net_income = safe_float(item.get("netIncome"))

        # Compute margins
        gross_margin = None
        op_margin = None
        net_margin_val = None
        if total_revenue and total_revenue > 0:
            if gross_profit is not None:
                gross_margin = round(gross_profit / total_revenue * 100, 2)
            if operating_income is not None:
                op_margin = round(operating_income / total_revenue * 100, 2)
            if net_income is not None:
                net_margin_val = round(net_income / total_revenue * 100, 2)

        # YoY growth vs next item in list (which is the previous year)
        revenue_growth = None
        ni_growth = None
        if i < len(reports) - 1:
            prev = reports[i + 1]
            prev_revenue = safe_float(prev.get("totalRevenue"))
            prev_ni = safe_float(prev.get("netIncome"))
            if prev_revenue and prev_revenue != 0 and total_revenue:
                revenue_growth = round(((total_revenue - prev_revenue) / abs(prev_revenue)) * 100, 2)
            if prev_ni and prev_ni != 0 and net_income:
                ni_growth = round(((net_income - prev_ni) / abs(prev_ni)) * 100, 2)

        # EPS from net income / shares outstanding
        eps_val = None
        if net_income is not None and shares_outstanding and shares_outstanding > 0:
            eps_val = round(net_income / shares_outstanding, 2)

        statements.append(IncomeStatement(
            fiscal_date=item.get("fiscalDateEnding", ""),
            total_revenue=total_revenue,
            gross_profit=gross_profit,
            operating_income=operating_income,
            net_income=net_income,
            ebitda=safe_float(item.get("ebitda")),
            cost_of_revenue=safe_float(item.get("costOfRevenue")),
            research_and_development=safe_float(item.get("researchAndDevelopment")),
            selling_general_admin=safe_float(item.get("sellingGeneralAndAdministrative")),
            interest_expense=safe_float(item.get("interestExpense")),
            interest_income=safe_float(item.get("interestIncome")),
            gross_margin=gross_margin,
            operating_margin=op_margin,
            net_margin=net_margin_val,
            revenue_growth_yoy=revenue_growth,
            net_income_growth_yoy=ni_growth,
            eps=eps_val,
        ))

    return statements


def map_balance_sheets(data: Dict[str, Any], period: str = "annual") -> List[BalanceSheet]:
    """Map BALANCE_SHEET response with liquidity ratios."""
    report_key = "quarterlyReports" if period == "quarterly" else "annualReports"
    if not data or report_key not in data:
        return []

    limit = 8 if period == "quarterly" else 5
    sheets = []
    for item in data.get(report_key, [])[:limit]:
        total_assets = safe_float(item.get("totalAssets"))
        total_liabilities = safe_float(item.get("totalLiabilities"))
        total_equity = safe_float(item.get("totalShareholderEquity"))
        total_debt = safe_float(item.get("longTermDebt"))
        current_assets = safe_float(item.get("totalCurrentAssets"))
        current_liabilities = safe_float(item.get("totalCurrentLiabilities"))
        inventory = safe_float(item.get("inventory"))

        current_ratio = None
        quick_ratio = None
        debt_to_equity = None

        if current_assets and current_liabilities and current_liabilities > 0:
            current_ratio = round(current_assets / current_liabilities, 2)
            inv = inventory if inventory else 0
            quick_ratio = round((current_assets - inv) / current_liabilities, 2)

        if total_debt and total_equity and total_equity > 0:
            debt_to_equity = round(total_debt / total_equity, 2)

        sheets.append(BalanceSheet(
            fiscal_date=item.get("fiscalDateEnding", ""),
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            total_debt=total_debt,
            cash_and_equivalents=safe_float(item.get("cashAndCashEquivalentsAtCarryingValue")),
            current_assets=current_assets,
            current_liabilities=current_liabilities,
            inventory=inventory,
            current_ratio=current_ratio,
            quick_ratio=quick_ratio,
            debt_to_equity=debt_to_equity,
        ))

    return sheets


def map_cash_flows(
    data: Dict[str, Any],
    shares_outstanding: Optional[float] = None,
    current_price: Optional[float] = None,
    revenue_by_year: Optional[Dict[str, float]] = None,
    period: str = "annual",
) -> List[CashFlow]:
    """Map CASH_FLOW response with investing/financing cashflow and FCF metrics."""
    report_key = "quarterlyReports" if period == "quarterly" else "annualReports"
    if not data or report_key not in data:
        return []

    limit = 8 if period == "quarterly" else 5
    flows = []
    for item in data.get(report_key, [])[:limit]:
        operating = safe_float(item.get("operatingCashflow"))
        capex = safe_float(item.get("capitalExpenditures"))
        fcf = None
        if operating is not None and capex is not None:
            fcf = operating - abs(capex)

        # Computed metrics
        fcf_per_share = None
        fcf_yield_val = None
        fcf_margin_val = None

        if fcf is not None and shares_outstanding and shares_outstanding > 0:
            fcf_per_share = round(fcf / shares_outstanding, 2)
            if current_price and current_price > 0:
                fcf_yield_val = round(fcf_per_share / current_price * 100, 2)

        fiscal_year = item.get("fiscalDateEnding", "")[:4]
        if fcf is not None and revenue_by_year:
            revenue = revenue_by_year.get(fiscal_year)
            if revenue and revenue > 0:
                fcf_margin_val = round(fcf / revenue * 100, 2)

        flows.append(CashFlow(
            fiscal_date=item.get("fiscalDateEnding", ""),
            operating_cashflow=operating,
            capital_expenditure=capex,
            free_cashflow=fcf,
            dividend_payout=safe_float(item.get("dividendPayout")),
            investing_cashflow=safe_float(item.get("cashflowFromInvestment")),
            financing_cashflow=safe_float(item.get("cashflowFromFinancing")),
            depreciation_amortization=safe_float(item.get("depreciationDepletionAndAmortization")),
            fcf_per_share=fcf_per_share,
            fcf_yield=fcf_yield_val,
            fcf_margin=fcf_margin_val,
        ))

    return flows


def map_earnings(data: Dict[str, Any]) -> Tuple[List[EarningsData], List[AnnualEarnings]]:
    """Map EARNINGS response to quarterly and annual earnings."""
    if not data:
        return [], []

    quarterly = []
    for item in data.get("quarterlyEarnings", [])[:12]:
        quarterly.append(EarningsData(
            fiscal_date=item.get("fiscalDateEnding", ""),
            reported_eps=safe_float(item.get("reportedEPS")),
            estimated_eps=safe_float(item.get("estimatedEPS")),
            surprise=safe_float(item.get("surprise")),
            surprise_percentage=safe_float(item.get("surprisePercentage")),
        ))

    annual = []
    for item in data.get("annualEarnings", [])[:5]:
        annual.append(AnnualEarnings(
            fiscal_date=item.get("fiscalDateEnding", ""),
            reported_eps=safe_float(item.get("reportedEPS")),
        ))

    return quarterly, annual
