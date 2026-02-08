"""
Dividend Screener API endpoints.

Provides stock analysis using Alpha Vantage API data.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import requests
import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
import json

from app.config import get_settings
from app.utils.logging_config import get_logger

logger = get_logger()

# TTL-based cache for API responses (24 hours for fundamental data)
_response_cache: Dict[str, tuple[Any, datetime]] = {}
_CACHE_TTL_MINUTES = 1440  # 24 hours


def _get_cache_key(prefix: str, symbol: str) -> str:
    """Generate a unique cache key."""
    return f"{prefix}:{symbol.upper()}"


def _get_cached(key: str) -> Optional[Any]:
    """Get cached value if not expired."""
    if key in _response_cache:
        value, timestamp = _response_cache[key]
        if datetime.now() - timestamp < timedelta(minutes=_CACHE_TTL_MINUTES):
            return value
        # Expired, remove it
        del _response_cache[key]
    return None


def _set_cache(key: str, value: Any) -> None:
    """Store value in cache."""
    _response_cache[key] = (value, datetime.now())

router = APIRouter()

# Rate limiting state for Alpha Vantage
_last_av_request: Optional[datetime] = None
_av_lock = asyncio.Lock()


class CompanyOverview(BaseModel):
    """Company overview response."""
    symbol: str
    name: str
    description: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    dividend_per_share: Optional[float] = None
    eps: Optional[float] = None
    beta: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    book_value: Optional[float] = None
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_equity: Optional[float] = None
    revenue_ttm: Optional[float] = None
    gross_profit_ttm: Optional[float] = None
    ex_dividend_date: Optional[str] = None
    payout_ratio: Optional[float] = None


class DividendHistory(BaseModel):
    """Dividend payment record."""
    ex_date: str
    amount: float
    declaration_date: Optional[str] = None
    record_date: Optional[str] = None
    payment_date: Optional[str] = None


class IncomeStatement(BaseModel):
    """Income statement data."""
    fiscal_date: str
    total_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    ebitda: Optional[float] = None


class BalanceSheet(BaseModel):
    """Balance sheet data."""
    fiscal_date: str
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    inventory: Optional[float] = None
    # Calculated ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None


class CashFlow(BaseModel):
    """Cash flow data."""
    fiscal_date: str
    operating_cashflow: Optional[float] = None
    capital_expenditure: Optional[float] = None
    free_cashflow: Optional[float] = None
    dividend_payout: Optional[float] = None


class DividendMetrics(BaseModel):
    """Dividend-specific analysis metrics."""
    dividend_growth_rate: Optional[float] = None  # Average annual growth %
    fcf_coverage_ratio: Optional[float] = None  # FCF / Dividend Payout
    consecutive_growth_years: Optional[int] = None  # Years of consecutive increases
    dividend_consistency: Optional[str] = None  # Rating: Excellent/Good/Fair/Poor
    avg_dividend_amount: Optional[float] = None
    total_dividends_paid: Optional[float] = None


class RiskFactors(BaseModel):
    """Individual risk factor scores."""
    yield_risk: Optional[float] = None
    payout_risk: Optional[float] = None
    valuation_risk: Optional[float] = None
    leverage_risk: Optional[float] = None
    volatility_risk: Optional[float] = None
    coverage_risk: Optional[float] = None


class ScreenerAnalysis(BaseModel):
    """Complete screener analysis response."""
    overview: CompanyOverview
    dividends: List[DividendHistory]
    income_statements: List[IncomeStatement]
    balance_sheets: List[BalanceSheet]
    cash_flows: List[CashFlow]
    dividend_metrics: Optional[DividendMetrics] = None
    risk_factors: Optional[RiskFactors] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    risk_grade: Optional[str] = None  # A, B, C, D, F
    investment_summary: Optional[str] = None


def safe_float(value: Any, default: float = None) -> Optional[float]:
    """Safely convert value to float."""
    if value is None or value == "None" or value == "-" or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


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


@lru_cache(maxsize=100)
def _fetch_alpha_vantage_sync(function: str, symbol: str) -> Optional[Dict[str, Any]]:
    """
    Synchronous fetch from Alpha Vantage API with caching.
    Supports both standard and time series endpoints.
    """
    settings = get_settings()

    try:
        params = {
            "function": function,
            "symbol": symbol.upper(),
            "apikey": settings.alpha_vantage_api_key,
        }

        # Add outputsize for time series endpoints
        if "TIME_SERIES" in function:
            params["outputsize"] = "compact"  # Last 100 data points

        response = requests.get(settings.api_base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Check for API errors
        if "Error Message" in data:
            logger.warning(f"Alpha Vantage API error for {symbol}: {data.get('Error Message')}")
            return None
        if "Note" in data:  # Rate limit hit
            logger.warning(f"Alpha Vantage rate limit hit: {data.get('Note')}")
            return None
        if "Information" in data:  # API limit message
            logger.info(f"Alpha Vantage: {data.get('Information')}")
            return None

        return data
    except Exception as e:
        logger.error(f"Fetch error for {function}/{symbol}: {e}", exc_info=True)
        return None


async def fetch_alpha_vantage(function: str, symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch data from Alpha Vantage API with rate limiting and caching.
    """
    # Apply rate limiting
    await rate_limit_async()
    # Call the cached synchronous function
    return _fetch_alpha_vantage_sync(function, symbol)


@router.get("/overview/{symbol}", response_model=CompanyOverview)
async def get_company_overview(symbol: str):
    """
    Get company overview data from Alpha Vantage.
    Uses 24-hour TTL cache to minimize API calls.
    """
    cache_key = _get_cache_key("overview", symbol)
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    data = await fetch_alpha_vantage("OVERVIEW", symbol)

    if not data or "Symbol" not in data:
        raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")

    result = CompanyOverview(
        symbol=data.get("Symbol", symbol),
        name=data.get("Name", "Unknown"),
        description=data.get("Description"),
        sector=data.get("Sector"),
        industry=data.get("Industry"),
        market_cap=safe_float(data.get("MarketCapitalization")),
        pe_ratio=safe_float(data.get("PERatio")),
        dividend_yield=safe_float(data.get("DividendYield")),
        dividend_per_share=safe_float(data.get("DividendPerShare")),
        eps=safe_float(data.get("EPS")),
        beta=safe_float(data.get("Beta")),
        fifty_two_week_high=safe_float(data.get("52WeekHigh")),
        fifty_two_week_low=safe_float(data.get("52WeekLow")),
        forward_pe=safe_float(data.get("ForwardPE")),
        peg_ratio=safe_float(data.get("PEGRatio")),
        book_value=safe_float(data.get("BookValue")),
        profit_margin=safe_float(data.get("ProfitMargin")),
        operating_margin=safe_float(data.get("OperatingMarginTTM")),
        return_on_equity=safe_float(data.get("ReturnOnEquityTTM")),
        revenue_ttm=safe_float(data.get("RevenueTTM")),
        gross_profit_ttm=safe_float(data.get("GrossProfitTTM")),
        ex_dividend_date=data.get("ExDividendDate"),
        payout_ratio=safe_float(data.get("PayoutRatio")),
    )

    _set_cache(cache_key, result)
    return result


@router.get("/dividends/{symbol}", response_model=List[DividendHistory])
async def get_dividend_history(symbol: str):
    """
    Get dividend history from Alpha Vantage using TIME_SERIES_MONTHLY_ADJUSTED.
    This uses the free tier endpoint instead of premium DIVIDENDS endpoint.
    Extracts dividends from the "7. dividend amount" field in monthly data.
    Uses 24-hour TTL cache to minimize API calls.
    """
    cache_key = _get_cache_key("dividends", symbol)
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    # Use TIME_SERIES_MONTHLY_ADJUSTED (free tier) instead of DIVIDENDS (premium)
    data = await fetch_alpha_vantage("TIME_SERIES_MONTHLY_ADJUSTED", symbol)

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
                declaration_date=None,  # Not available in this endpoint
                record_date=None,
                payment_date=None,
            ))

    # Sort by date descending and limit to last 20
    dividends.sort(key=lambda x: x.ex_date, reverse=True)
    result = dividends[:20]

    _set_cache(cache_key, result)
    return result


@router.get("/income/{symbol}", response_model=List[IncomeStatement])
async def get_income_statement(symbol: str):
    """
    Get income statement data from Alpha Vantage.
    Uses 24-hour TTL cache to minimize API calls.
    """
    cache_key = _get_cache_key("income", symbol)
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    data = await fetch_alpha_vantage("INCOME_STATEMENT", symbol)

    if not data or "annualReports" not in data:
        return []

    statements = []
    for item in data.get("annualReports", [])[:5]:  # Last 5 years
        statements.append(IncomeStatement(
            fiscal_date=item.get("fiscalDateEnding", ""),
            total_revenue=safe_float(item.get("totalRevenue")),
            gross_profit=safe_float(item.get("grossProfit")),
            operating_income=safe_float(item.get("operatingIncome")),
            net_income=safe_float(item.get("netIncome")),
            ebitda=safe_float(item.get("ebitda")),
        ))

    _set_cache(cache_key, statements)
    return statements


@router.get("/balance/{symbol}", response_model=List[BalanceSheet])
async def get_balance_sheet(symbol: str):
    """
    Get balance sheet data from Alpha Vantage with liquidity ratios.
    Uses 24-hour TTL cache to minimize API calls.
    """
    cache_key = _get_cache_key("balance", symbol)
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    data = await fetch_alpha_vantage("BALANCE_SHEET", symbol)

    if not data or "annualReports" not in data:
        return []

    sheets = []
    for item in data.get("annualReports", [])[:5]:
        total_assets = safe_float(item.get("totalAssets"))
        total_liabilities = safe_float(item.get("totalLiabilities"))
        total_equity = safe_float(item.get("totalShareholderEquity"))
        total_debt = safe_float(item.get("longTermDebt"))
        current_assets = safe_float(item.get("totalCurrentAssets"))
        current_liabilities = safe_float(item.get("totalCurrentLiabilities"))
        inventory = safe_float(item.get("inventory"))

        # Calculate liquidity ratios
        current_ratio = None
        quick_ratio = None
        debt_to_equity = None

        if current_assets and current_liabilities and current_liabilities > 0:
            current_ratio = current_assets / current_liabilities
            # Quick ratio = (Current Assets - Inventory) / Current Liabilities
            inv = inventory if inventory else 0
            quick_ratio = (current_assets - inv) / current_liabilities

        if total_debt and total_equity and total_equity > 0:
            debt_to_equity = total_debt / total_equity

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

    _set_cache(cache_key, sheets)
    return sheets


@router.get("/cashflow/{symbol}", response_model=List[CashFlow])
async def get_cash_flow(symbol: str):
    """
    Get cash flow data from Alpha Vantage.
    Uses 24-hour TTL cache to minimize API calls.
    """
    cache_key = _get_cache_key("cashflow", symbol)
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    data = await fetch_alpha_vantage("CASH_FLOW", symbol)

    if not data or "annualReports" not in data:
        return []

    flows = []
    for item in data.get("annualReports", [])[:5]:
        operating = safe_float(item.get("operatingCashflow"))
        capex = safe_float(item.get("capitalExpenditures"))
        fcf = None
        if operating is not None and capex is not None:
            fcf = operating - abs(capex)

        flows.append(CashFlow(
            fiscal_date=item.get("fiscalDateEnding", ""),
            operating_cashflow=operating,
            capital_expenditure=capex,
            free_cashflow=fcf,
            dividend_payout=safe_float(item.get("dividendPayout")),
        ))

    _set_cache(cache_key, flows)
    return flows


def calculate_dividend_metrics(dividends: List[DividendHistory], cashflow: List[CashFlow]) -> DividendMetrics:
    """Calculate dividend-specific metrics from history."""
    if not dividends:
        return DividendMetrics()

    # Calculate total and average
    amounts = [d.amount for d in dividends]
    total_paid = sum(amounts)
    avg_amount = total_paid / len(amounts) if amounts else None

    # Calculate growth rate (YoY comparison)
    growth_rates = []
    sorted_divs = sorted(dividends, key=lambda x: x.ex_date)
    for i in range(1, len(sorted_divs)):
        prev_amount = sorted_divs[i - 1].amount
        curr_amount = sorted_divs[i].amount
        if prev_amount > 0:
            growth = ((curr_amount - prev_amount) / prev_amount) * 100
            growth_rates.append(growth)

    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else None

    # Count consecutive growth years
    consecutive_years = 0
    for i in range(1, len(sorted_divs)):
        if sorted_divs[i].amount >= sorted_divs[i - 1].amount:
            consecutive_years += 1
        else:
            consecutive_years = 0

    # Calculate FCF coverage ratio
    fcf_coverage = None
    if cashflow and len(cashflow) > 0:
        latest_cf = cashflow[0]
        if latest_cf.free_cashflow and latest_cf.dividend_payout:
            div_payout = abs(latest_cf.dividend_payout)
            if div_payout > 0:
                fcf_coverage = latest_cf.free_cashflow / div_payout

    # Determine consistency rating
    if len(dividends) >= 12 and consecutive_years >= 8:
        consistency = "Excellent"
    elif len(dividends) >= 8 and consecutive_years >= 4:
        consistency = "Good"
    elif len(dividends) >= 4:
        consistency = "Fair"
    else:
        consistency = "Limited Data"

    return DividendMetrics(
        dividend_growth_rate=avg_growth,
        fcf_coverage_ratio=fcf_coverage,
        consecutive_growth_years=consecutive_years,
        dividend_consistency=consistency,
        avg_dividend_amount=avg_amount,
        total_dividends_paid=total_paid,
    )


def calculate_risk_factors(
    overview: CompanyOverview,
    balance: List[BalanceSheet],
    cashflow: List[CashFlow],
    dividend_metrics: DividendMetrics
) -> tuple[RiskFactors, float, str, str]:
    """
    Calculate individual risk factors and overall risk score.
    Returns (risk_factors, risk_score, risk_level, risk_grade).
    """
    risk_factors = RiskFactors()

    # Initialize individual risk scores (0 = low risk, 100 = high risk)
    yield_risk = 50.0
    payout_risk = 50.0
    valuation_risk = 50.0
    leverage_risk = 50.0
    volatility_risk = 50.0
    coverage_risk = 50.0

    # 1. Yield Risk - very high yields can indicate trouble
    if overview.dividend_yield:
        if overview.dividend_yield > 0.08:  # >8% is very risky
            yield_risk = 90
        elif overview.dividend_yield > 0.06:  # >6%
            yield_risk = 70
        elif overview.dividend_yield > 0.04:  # 4-6%
            yield_risk = 50
        elif overview.dividend_yield > 0.02:  # 2-4% is healthy
            yield_risk = 30
        else:
            yield_risk = 40  # Very low yield

    # 2. Payout Risk - high payout ratios are unsustainable
    if overview.payout_ratio:
        if overview.payout_ratio > 1.0:  # >100% is dangerous
            payout_risk = 95
        elif overview.payout_ratio > 0.9:
            payout_risk = 80
        elif overview.payout_ratio > 0.7:
            payout_risk = 60
        elif overview.payout_ratio > 0.5:
            payout_risk = 40
        else:
            payout_risk = 25

    # 3. Valuation Risk - based on P/E and PEG
    if overview.pe_ratio:
        if overview.pe_ratio > 40:
            valuation_risk = 85
        elif overview.pe_ratio > 30:
            valuation_risk = 70
        elif overview.pe_ratio > 20:
            valuation_risk = 50
        elif overview.pe_ratio > 10 and overview.pe_ratio > 0:
            valuation_risk = 35
        elif overview.pe_ratio > 0:
            valuation_risk = 25

    # 4. Leverage Risk - based on debt-to-equity
    if balance and len(balance) > 0:
        latest = balance[0]
        if latest.debt_to_equity is not None:
            if latest.debt_to_equity > 3:
                leverage_risk = 90
            elif latest.debt_to_equity > 2:
                leverage_risk = 75
            elif latest.debt_to_equity > 1:
                leverage_risk = 55
            elif latest.debt_to_equity > 0.5:
                leverage_risk = 35
            else:
                leverage_risk = 20

    # 5. Volatility Risk - based on Beta
    if overview.beta:
        if overview.beta > 2.0:
            volatility_risk = 90
        elif overview.beta > 1.5:
            volatility_risk = 75
        elif overview.beta > 1.2:
            volatility_risk = 60
        elif overview.beta > 0.8:
            volatility_risk = 40
        else:
            volatility_risk = 25

    # 6. Coverage Risk - based on FCF coverage of dividends
    if dividend_metrics.fcf_coverage_ratio is not None:
        if dividend_metrics.fcf_coverage_ratio < 1.0:
            coverage_risk = 90  # FCF doesn't cover dividends
        elif dividend_metrics.fcf_coverage_ratio < 1.2:
            coverage_risk = 70
        elif dividend_metrics.fcf_coverage_ratio < 1.5:
            coverage_risk = 50
        elif dividend_metrics.fcf_coverage_ratio < 2.0:
            coverage_risk = 35
        else:
            coverage_risk = 20

    # Store individual factors
    risk_factors = RiskFactors(
        yield_risk=yield_risk,
        payout_risk=payout_risk,
        valuation_risk=valuation_risk,
        leverage_risk=leverage_risk,
        volatility_risk=volatility_risk,
        coverage_risk=coverage_risk,
    )

    # Calculate weighted overall score
    weights = {
        'yield': 0.15,
        'payout': 0.20,
        'valuation': 0.15,
        'leverage': 0.20,
        'volatility': 0.10,
        'coverage': 0.20,
    }

    overall_score = (
        yield_risk * weights['yield'] +
        payout_risk * weights['payout'] +
        valuation_risk * weights['valuation'] +
        leverage_risk * weights['leverage'] +
        volatility_risk * weights['volatility'] +
        coverage_risk * weights['coverage']
    )

    # Clamp score
    overall_score = max(0, min(100, overall_score))

    # Determine risk level
    if overall_score >= 70:
        risk_level = "High"
    elif overall_score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Determine grade
    if overall_score <= 25:
        risk_grade = "A"
    elif overall_score <= 40:
        risk_grade = "B"
    elif overall_score <= 55:
        risk_grade = "C"
    elif overall_score <= 70:
        risk_grade = "D"
    else:
        risk_grade = "F"

    return risk_factors, overall_score, risk_level, risk_grade


@router.get("/analysis/{symbol}", response_model=ScreenerAnalysis)
async def get_full_analysis(symbol: str):
    """
    Get comprehensive stock analysis with enhanced metrics and risk scoring.
    """
    # Fetch all data
    overview = await get_company_overview(symbol)
    dividends = await get_dividend_history(symbol)
    income = await get_income_statement(symbol)
    balance = await get_balance_sheet(symbol)
    cashflow = await get_cash_flow(symbol)

    # Calculate dividend metrics
    dividend_metrics = calculate_dividend_metrics(dividends, cashflow)

    # Calculate enhanced risk scoring
    risk_factors, risk_score, risk_level, risk_grade = calculate_risk_factors(
        overview, balance, cashflow, dividend_metrics
    )

    # Generate comprehensive investment summary
    summary_parts = []

    # Yield assessment
    if overview.dividend_yield:
        yield_pct = overview.dividend_yield * 100
        if yield_pct > 6:
            summary_parts.append(f"High yield of {yield_pct:.2f}% may signal risk")
        elif yield_pct > 3:
            summary_parts.append(f"Attractive yield of {yield_pct:.2f}%")
        else:
            summary_parts.append(f"Moderate yield of {yield_pct:.2f}%")

    # Payout assessment
    if overview.payout_ratio:
        payout_pct = overview.payout_ratio * 100
        if payout_pct > 90:
            summary_parts.append(f"payout ratio of {payout_pct:.0f}% is unsustainable")
        elif payout_pct > 70:
            summary_parts.append(f"payout ratio of {payout_pct:.0f}% is elevated")
        else:
            summary_parts.append(f"sustainable payout ratio of {payout_pct:.0f}%")

    # Coverage assessment
    if dividend_metrics.fcf_coverage_ratio:
        if dividend_metrics.fcf_coverage_ratio >= 2:
            summary_parts.append("strong free cash flow coverage")
        elif dividend_metrics.fcf_coverage_ratio >= 1.2:
            summary_parts.append("adequate FCF coverage")
        else:
            summary_parts.append("weak FCF coverage of dividends")

    # Beta assessment
    if overview.beta:
        if overview.beta > 1.5:
            summary_parts.append(f"high volatility (beta: {overview.beta:.2f})")
        elif overview.beta < 0.8:
            summary_parts.append(f"defensive stock (beta: {overview.beta:.2f})")

    investment_summary = ". ".join(summary_parts).capitalize() if summary_parts else None

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
    )


@router.post("/search")
async def search_dividends(
    min_yield: float = Query(default=0.0, description="Minimum dividend yield"),
    max_yield: float = Query(default=100.0, description="Maximum dividend yield"),
):
    """
    Search for dividend stocks.
    Note: Alpha Vantage free tier doesn't support stock screening.
    This endpoint returns instructions for using the analysis endpoint instead.
    """
    return {
        "message": "Stock screening requires Alpha Vantage premium. Use /analysis/{symbol} to analyze specific stocks.",
        "suggestion": "Enter a stock symbol in the screener to analyze it.",
        "filters": {
            "min_yield": min_yield,
            "max_yield": max_yield
        }
    }


@router.get("/cache/status")
async def get_cache_status():
    """
    Get current cache status and statistics.
    """
    now = datetime.now()
    entries = []
    for key, (_, timestamp) in _response_cache.items():
        age_minutes = (now - timestamp).total_seconds() / 60
        expires_in = _CACHE_TTL_MINUTES - age_minutes
        entries.append({
            "key": key,
            "age_minutes": round(age_minutes, 1),
            "expires_in_minutes": round(expires_in, 1),
            "expired": expires_in <= 0,
        })

    return {
        "total_entries": len(_response_cache),
        "ttl_minutes": _CACHE_TTL_MINUTES,
        "entries": entries,
    }


@router.delete("/cache/clear")
async def clear_cache(symbol: Optional[str] = None):
    """
    Clear cached responses.
    If symbol is provided, only clear cache for that symbol.
    Otherwise, clear all cache.
    """
    global _response_cache

    if symbol is None:
        count = len(_response_cache)
        _response_cache = {}
        return {"cleared": count, "message": "All cache entries cleared"}

    # Clear entries for specific symbol
    symbol_upper = symbol.upper()
    keys_to_remove = [k for k in _response_cache.keys() if k.endswith(f":{symbol_upper}")]
    for key in keys_to_remove:
        del _response_cache[key]

    return {"cleared": len(keys_to_remove), "symbol": symbol_upper}
