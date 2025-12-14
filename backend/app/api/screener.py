"""
Dividend Screener API endpoints.

Provides stock analysis using Alpha Vantage API data.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import requests
import asyncio
from datetime import datetime
from functools import lru_cache

from app.config import get_settings

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


class CashFlow(BaseModel):
    """Cash flow data."""
    fiscal_date: str
    operating_cashflow: Optional[float] = None
    capital_expenditure: Optional[float] = None
    free_cashflow: Optional[float] = None
    dividend_payout: Optional[float] = None


class ScreenerAnalysis(BaseModel):
    """Complete screener analysis response."""
    overview: CompanyOverview
    dividends: List[DividendHistory]
    income_statements: List[IncomeStatement]
    balance_sheets: List[BalanceSheet]
    cash_flows: List[CashFlow]
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
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
            print(f"Alpha Vantage API error for {symbol}: {data.get('Error Message')}")
            return None
        if "Note" in data:  # Rate limit hit
            print(f"Alpha Vantage rate limit: {data.get('Note')}")
            return None
        if "Information" in data:  # API limit message
            print(f"Alpha Vantage info: {data.get('Information')}")
            return None

        return data
    except Exception as e:
        print(f"Fetch error for {function}/{symbol}: {e}")
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
    """
    data = await fetch_alpha_vantage("OVERVIEW", symbol)

    if not data or "Symbol" not in data:
        raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")

    return CompanyOverview(
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


@router.get("/dividends/{symbol}", response_model=List[DividendHistory])
async def get_dividend_history(symbol: str):
    """
    Get dividend history from Alpha Vantage using TIME_SERIES_MONTHLY_ADJUSTED.
    This uses the free tier endpoint instead of premium DIVIDENDS endpoint.
    Extracts dividends from the "7. dividend amount" field in monthly data.
    """
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
    return dividends[:20]


@router.get("/income/{symbol}", response_model=List[IncomeStatement])
async def get_income_statement(symbol: str):
    """
    Get income statement data from Alpha Vantage.
    """
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

    return statements


@router.get("/balance/{symbol}", response_model=List[BalanceSheet])
async def get_balance_sheet(symbol: str):
    """
    Get balance sheet data from Alpha Vantage.
    """
    data = await fetch_alpha_vantage("BALANCE_SHEET", symbol)

    if not data or "annualReports" not in data:
        return []

    sheets = []
    for item in data.get("annualReports", [])[:5]:
        sheets.append(BalanceSheet(
            fiscal_date=item.get("fiscalDateEnding", ""),
            total_assets=safe_float(item.get("totalAssets")),
            total_liabilities=safe_float(item.get("totalLiabilities")),
            total_equity=safe_float(item.get("totalShareholderEquity")),
            total_debt=safe_float(item.get("longTermDebt")),
            cash_and_equivalents=safe_float(item.get("cashAndCashEquivalentsAtCarryingValue")),
        ))

    return sheets


@router.get("/cashflow/{symbol}", response_model=List[CashFlow])
async def get_cash_flow(symbol: str):
    """
    Get cash flow data from Alpha Vantage.
    """
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

    return flows


@router.get("/analysis/{symbol}", response_model=ScreenerAnalysis)
async def get_full_analysis(symbol: str):
    """
    Get comprehensive stock analysis.
    """
    # Fetch all data
    overview = await get_company_overview(symbol)
    dividends = await get_dividend_history(symbol)
    income = await get_income_statement(symbol)
    balance = await get_balance_sheet(symbol)
    cashflow = await get_cash_flow(symbol)

    # Calculate risk score (simple scoring system)
    risk_score = 50.0  # Base score

    # Dividend yield factor
    if overview.dividend_yield:
        if overview.dividend_yield > 0.06:  # >6% yield is risky
            risk_score += 15
        elif overview.dividend_yield > 0.04:  # 4-6% is moderate
            risk_score += 5
        elif overview.dividend_yield > 0.02:  # 2-4% is healthy
            risk_score -= 10

    # Payout ratio factor
    if overview.payout_ratio:
        if overview.payout_ratio > 0.9:  # >90% is risky
            risk_score += 20
        elif overview.payout_ratio > 0.7:  # 70-90% is moderate
            risk_score += 10
        elif overview.payout_ratio < 0.5:  # <50% is healthy
            risk_score -= 10

    # PE ratio factor
    if overview.pe_ratio:
        if overview.pe_ratio > 30:
            risk_score += 10
        elif overview.pe_ratio < 15 and overview.pe_ratio > 0:
            risk_score -= 10

    # Debt factor (from balance sheet)
    if balance and len(balance) > 0:
        latest = balance[0]
        if latest.total_debt and latest.total_equity:
            debt_ratio = latest.total_debt / latest.total_equity if latest.total_equity > 0 else 0
            if debt_ratio > 2:
                risk_score += 15
            elif debt_ratio < 0.5:
                risk_score -= 10

    # Clamp risk score
    risk_score = max(0, min(100, risk_score))

    # Determine risk level
    if risk_score >= 70:
        risk_level = "High"
    elif risk_score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Generate investment summary
    summary_parts = []
    if overview.dividend_yield:
        yield_pct = overview.dividend_yield * 100
        summary_parts.append(f"Dividend yield: {yield_pct:.2f}%")
    if overview.payout_ratio:
        payout_pct = overview.payout_ratio * 100
        summary_parts.append(f"Payout ratio: {payout_pct:.1f}%")
    if overview.pe_ratio:
        summary_parts.append(f"P/E ratio: {overview.pe_ratio:.1f}")

    investment_summary = ". ".join(summary_parts) if summary_parts else None

    return ScreenerAnalysis(
        overview=overview,
        dividends=dividends,
        income_statements=income,
        balance_sheets=balance,
        cash_flows=cashflow,
        risk_score=risk_score,
        risk_level=risk_level,
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
