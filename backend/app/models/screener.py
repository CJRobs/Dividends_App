"""
Pydantic models for the Dividend Screener.

Contains all data models for Alpha Vantage API responses,
computed metrics, risk analysis, and the full analysis response.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


def safe_float(value: Any, default: float = None) -> Optional[float]:
    """Safely convert value to float."""
    if value is None or value == "None" or value == "-" or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


class CompanyOverview(BaseModel):
    """Company overview response from Alpha Vantage OVERVIEW endpoint."""
    symbol: str
    name: str
    description: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    current_price: Optional[float] = None
    shares_outstanding: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    trailing_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    dividend_per_share: Optional[float] = None
    dividend_date: Optional[str] = None
    eps: Optional[float] = None
    beta: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    book_value: Optional[float] = None
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_equity: Optional[float] = None
    revenue_ttm: Optional[float] = None
    gross_profit_ttm: Optional[float] = None
    ex_dividend_date: Optional[str] = None
    payout_ratio: Optional[float] = None
    # Valuation
    price_to_sales_ratio: Optional[float] = None
    price_to_book_ratio: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    # Analyst ratings
    analyst_target_price: Optional[float] = None
    analyst_rating_strong_buy: Optional[int] = None
    analyst_rating_buy: Optional[int] = None
    analyst_rating_hold: Optional[int] = None
    analyst_rating_sell: Optional[int] = None
    analyst_rating_strong_sell: Optional[int] = None
    # Growth
    quarterly_earnings_growth_yoy: Optional[float] = None
    quarterly_revenue_growth_yoy: Optional[float] = None


class DividendHistory(BaseModel):
    """Dividend payment record."""
    ex_date: str
    amount: float
    declaration_date: Optional[str] = None
    record_date: Optional[str] = None
    payment_date: Optional[str] = None


class IncomeStatement(BaseModel):
    """Income statement data with computed margins."""
    fiscal_date: str
    total_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    ebitda: Optional[float] = None
    # Additional line items
    cost_of_revenue: Optional[float] = None
    research_and_development: Optional[float] = None
    selling_general_admin: Optional[float] = None
    interest_expense: Optional[float] = None
    interest_income: Optional[float] = None
    # Computed margins (%)
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    # Computed growth (%)
    revenue_growth_yoy: Optional[float] = None
    net_income_growth_yoy: Optional[float] = None
    # Per-share
    eps: Optional[float] = None


class BalanceSheet(BaseModel):
    """Balance sheet data with liquidity ratios."""
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
    """Cash flow data with computed FCF metrics."""
    fiscal_date: str
    operating_cashflow: Optional[float] = None
    capital_expenditure: Optional[float] = None
    free_cashflow: Optional[float] = None
    dividend_payout: Optional[float] = None
    # Additional line items
    investing_cashflow: Optional[float] = None
    financing_cashflow: Optional[float] = None
    depreciation_amortization: Optional[float] = None
    # Computed per-share / yield
    fcf_per_share: Optional[float] = None
    fcf_yield: Optional[float] = None
    fcf_margin: Optional[float] = None


class EarningsData(BaseModel):
    """Quarterly earnings data from EARNINGS endpoint."""
    fiscal_date: str
    reported_eps: Optional[float] = None
    estimated_eps: Optional[float] = None
    surprise: Optional[float] = None
    surprise_percentage: Optional[float] = None


class AnnualEarnings(BaseModel):
    """Annual earnings data."""
    fiscal_date: str
    reported_eps: Optional[float] = None


class DividendMetrics(BaseModel):
    """Dividend-specific analysis metrics."""
    dividend_growth_rate: Optional[float] = None
    fcf_coverage_ratio: Optional[float] = None
    consecutive_growth_years: Optional[int] = None
    dividend_consistency: Optional[str] = None
    avg_dividend_amount: Optional[float] = None
    total_dividends_paid: Optional[float] = None


class RiskFactors(BaseModel):
    """Individual risk factor scores (0-100)."""
    yield_risk: Optional[float] = None
    payout_risk: Optional[float] = None
    valuation_risk: Optional[float] = None
    leverage_risk: Optional[float] = None
    volatility_risk: Optional[float] = None
    coverage_risk: Optional[float] = None


class GrowthMetrics(BaseModel):
    """Computed CAGR growth metrics."""
    revenue_cagr_3y: Optional[float] = None
    revenue_cagr_5y: Optional[float] = None
    eps_cagr_3y: Optional[float] = None
    eps_cagr_5y: Optional[float] = None
    fcf_cagr_3y: Optional[float] = None
    dividend_cagr_3y: Optional[float] = None
    dividend_cagr_5y: Optional[float] = None


class AnalystSentiment(BaseModel):
    """Analyst ratings summary."""
    target_price: Optional[float] = None
    strong_buy: Optional[int] = None
    buy: Optional[int] = None
    hold: Optional[int] = None
    sell: Optional[int] = None
    strong_sell: Optional[int] = None
    total_analysts: Optional[int] = None
    consensus: Optional[str] = None


class DataFreshnessEntry(BaseModel):
    """Cache freshness metadata for a single data type."""
    cached_at: Optional[str] = None
    expires_at: Optional[str] = None
    source: str = "provider"


class ScreenerAnalysis(BaseModel):
    """Complete screener analysis response."""
    overview: CompanyOverview
    dividends: List[DividendHistory]
    income_statements: List[IncomeStatement]
    balance_sheets: List[BalanceSheet]
    cash_flows: List[CashFlow]
    # Analysis
    dividend_metrics: Optional[DividendMetrics] = None
    risk_factors: Optional[RiskFactors] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    risk_grade: Optional[str] = None
    investment_summary: Optional[str] = None
    # New data
    quarterly_earnings: Optional[List[EarningsData]] = None
    annual_earnings: Optional[List[AnnualEarnings]] = None
    growth_metrics: Optional[GrowthMetrics] = None
    analyst_sentiment: Optional[AnalystSentiment] = None
    # Cache freshness
    data_freshness: Optional[Dict[str, DataFreshnessEntry]] = None
