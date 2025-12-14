"""
Pydantic models for portfolio and dividend data.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DividendRecord(BaseModel):
    """Individual dividend record from CSV."""

    action: str = Field(..., description="Action type")
    time: datetime = Field(..., description="Dividend payment time")
    isin: str = Field(..., description="ISIN code")
    ticker: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Company name")
    no_of_shares: float = Field(..., alias="No. of shares")
    price_per_share: float = Field(..., alias="Price / share")
    currency_price: str = Field(..., alias="Currency (Price / share)")
    exchange_rate: Optional[str] = Field(None, alias="Exchange rate")
    total: float = Field(..., description="Total dividend amount")
    currency_total: str = Field(..., alias="Currency (Total)")
    withholding_tax: float = Field(..., alias="Withholding tax")
    currency_tax: str = Field(..., alias="Currency (Withholding tax)")

    class Config:
        populate_by_name = True


class MonthlyData(BaseModel):
    """Monthly aggregated dividend data."""

    year: int
    month: int
    month_name: str
    total: float
    count: int
    stocks: List[str]


class YearlyData(BaseModel):
    """Yearly aggregated dividend data."""

    year: int
    total: float
    count: int
    average_per_month: float
    monthly_breakdown: List[MonthlyData]


class PortfolioSummary(BaseModel):
    """Overall portfolio summary statistics."""

    total_dividends: float
    total_dividends_ytd: float
    total_count: int
    unique_stocks: int
    average_dividend: float
    highest_dividend: float
    lowest_dividend: float
    first_dividend_date: Optional[datetime]
    last_dividend_date: Optional[datetime]
    ytd_vs_last_year_change: Optional[float] = None
    ytd_vs_last_year_percent: Optional[float] = None


class StockSummary(BaseModel):
    """Summary statistics for a single stock."""

    ticker: str
    name: str
    isin: str
    total_dividends: float
    dividend_count: int
    average_dividend: float
    last_dividend_date: Optional[datetime]
    last_dividend_amount: float
    percentage_of_portfolio: float


class RecentDividend(BaseModel):
    """Recent dividend payment information."""

    ticker: str
    name: str
    amount: float
    date: datetime
    shares: float


class ChartData(BaseModel):
    """Generic chart data structure."""

    labels: List[str]
    values: List[float]
    colors: Optional[List[str]] = None


class TimeSeriesData(BaseModel):
    """Time series chart data."""

    dates: List[str]
    values: List[float]
    label: str = "Value"


class OverviewResponse(BaseModel):
    """Complete overview tab response."""

    summary: PortfolioSummary
    ytd_chart: TimeSeriesData
    monthly_chart: ChartData
    top_stocks: List[StockSummary]
    recent_dividends: List[RecentDividend]


class AnnualStats(BaseModel):
    """Annual statistics for a single year."""

    year: int
    total: float
    count: int
    average: float
    unique_stocks: int
    growth: Optional[float] = None


class DividendStreakInfo(BaseModel):
    """Information about consecutive dividend payments."""

    current_streak: int = Field(..., description="Current streak of consecutive months with dividends")
    longest_streak: int = Field(..., description="Longest streak of consecutive months")
    months_with_dividends: int = Field(..., description="Total months that had dividends")
    total_months_span: int = Field(..., description="Total months span of dividend history")


class YoYMonthData(BaseModel):
    """Year-over-year comparison data for a single month."""

    month: str
    data: dict  # Year -> value mapping


class YoYComparisonData(BaseModel):
    """Year-over-year comparison response."""

    months: List[YoYMonthData]
    years: List[int]


class FICalculatorResponse(BaseModel):
    """Financial Independence calculator response."""

    monthly_goal: float = Field(..., description="Target monthly dividend income")
    current_monthly_avg: float = Field(..., description="Current average monthly dividends")
    annual_growth_rate: float = Field(..., description="Estimated annual growth rate (percentage)")
    years_to_goal: Optional[float] = Field(None, description="Estimated years to reach goal (None if already reached or infinite)")
    goal_reached: bool = Field(..., description="Whether the goal has been reached")
