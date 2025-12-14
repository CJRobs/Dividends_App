"""
Pydantic models for stock analysis data.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PeriodData(BaseModel):
    """Period data point for stacked bar chart."""
    period: str
    period_key: str
    stocks: dict[str, float] = Field(default_factory=dict)
    total: float = 0


class PeriodAnalysisResponse(BaseModel):
    """Response for time period analysis."""
    periods: List[str]
    stocks: List[str]
    data: List[PeriodData]
    period_type: str


class GrowthData(BaseModel):
    """Growth rate data point."""
    period: str
    total: float
    growth_percent: Optional[float] = None


class GrowthAnalysisResponse(BaseModel):
    """Response for growth analysis."""
    data: List[GrowthData]
    average_growth: Optional[float] = None


class ConcentrationData(BaseModel):
    """Concentration risk metrics."""
    top_1_percent: float
    top_3_percent: float
    top_5_percent: float
    top_10_percent: float
    top_1_risk: str
    top_3_risk: str
    top_5_risk: str
    top_10_risk: str


class StockDistribution(BaseModel):
    """Stock distribution for pie chart."""
    name: str
    total: float
    percentage: float


class StockListItem(BaseModel):
    """Stock item for list view."""
    ticker: str
    name: str
    total_dividends: float
    dividend_count: int
    average_dividend: float
    percentage_of_portfolio: float
    last_dividend_date: Optional[datetime] = None
    last_dividend_amount: float


class StockDetail(BaseModel):
    """Detailed stock information."""
    ticker: str
    name: str
    isin: str
    total_dividends: float
    dividend_count: int
    average_dividend: float
    min_dividend: float
    max_dividend: float
    first_dividend_date: Optional[datetime] = None
    last_dividend_date: Optional[datetime] = None
    last_dividend_amount: float
    payment_cadence: str
    payments_per_year: float


class PaymentHistory(BaseModel):
    """Individual payment record."""
    date: datetime
    amount: float
    shares: float


class YearlyTotal(BaseModel):
    """Yearly total for a stock."""
    year: int
    total: float


class MonthlyGrowth(BaseModel):
    """Monthly growth data."""
    month: str
    total: float
    percent_change: Optional[float] = None


class StockAnalysisResponse(BaseModel):
    """Complete stock detail response."""
    detail: StockDetail
    yearly_totals: List[YearlyTotal]
    payment_history: List[PaymentHistory]
    monthly_growth: List[MonthlyGrowth]


class StockOverviewResponse(BaseModel):
    """Response for stocks overview page."""
    stocks: List[StockListItem]
    distribution: List[StockDistribution]
    concentration: ConcentrationData
    total_stocks: int
    total_dividends: float
