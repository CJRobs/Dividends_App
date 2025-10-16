"""
Pydantic models for dividend analysis, screening, and forecasting.
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


class StockInfo(BaseModel):
    """Detailed stock information."""

    ticker: str
    name: str
    isin: str
    total_dividends: float
    dividend_count: int
    average_dividend: float
    min_dividend: float
    max_dividend: float
    first_dividend_date: Optional[datetime]
    last_dividend_date: Optional[datetime]
    dividend_frequency: Optional[str] = None
    yield_estimate: Optional[float] = None


class StockHistory(BaseModel):
    """Dividend history for a stock."""

    ticker: str
    name: str
    dividends: List[Dict]  # List of dividend payments with date, amount, shares


class MonthlyComparison(BaseModel):
    """Month-over-month or year-over-year comparison."""

    period: str  # e.g., "2024-01" or "January"
    current_value: float
    previous_value: Optional[float]
    change: Optional[float]
    change_percent: Optional[float]


class ScreenerFilterOperator(str, Enum):
    """Filter operators for screener."""

    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUAL = "eq"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    BETWEEN = "between"


class ScreenerFilter(BaseModel):
    """Individual filter for dividend screener."""

    field: str
    operator: ScreenerFilterOperator
    value: float
    value2: Optional[float] = None  # For "between" operator


class ScreenerCriteria(BaseModel):
    """Complete screener search criteria."""

    filters: List[ScreenerFilter] = []
    sort_by: Optional[str] = "total_dividends"
    sort_order: str = "desc"  # "asc" or "desc"
    limit: Optional[int] = 100


class ScreenerResult(BaseModel):
    """Screener search result."""

    stocks: List[StockInfo]
    total_count: int
    criteria: ScreenerCriteria


class ForecastMethod(str, Enum):
    """Forecasting method."""

    LINEAR = "linear"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL = "exponential"
    PROPHET = "prophet"  # Optional, requires prophet library


class ForecastScenario(str, Enum):
    """Forecast scenario type."""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    OPTIMISTIC = "optimistic"


class ForecastRequest(BaseModel):
    """Forecast generation request."""

    months: int = Field(default=12, ge=1, le=60)
    method: ForecastMethod = ForecastMethod.LINEAR
    scenario: Optional[ForecastScenario] = ForecastScenario.MODERATE
    include_confidence_interval: bool = True


class ForecastDataPoint(BaseModel):
    """Single forecast data point."""

    date: str  # ISO format date
    value: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class ForecastResponse(BaseModel):
    """Forecast generation response."""

    historical: List[ForecastDataPoint]
    forecast: List[ForecastDataPoint]
    total_forecast: float
    method: ForecastMethod
    scenario: Optional[ForecastScenario]
    confidence_level: Optional[float] = 0.95


class ReportTemplate(str, Enum):
    """Available PDF report templates."""

    SUMMARY = "summary"
    DETAILED = "detailed"
    MONTHLY = "monthly"
    STOCK_ANALYSIS = "stock_analysis"
    YEARLY = "yearly"


class ReportRequest(BaseModel):
    """PDF report generation request."""

    template: ReportTemplate
    year: Optional[int] = None
    month: Optional[int] = None
    ticker: Optional[str] = None
    include_charts: bool = True
    include_tables: bool = True


class ReportResponse(BaseModel):
    """PDF report generation response."""

    report_id: str
    filename: str
    download_url: str
    created_at: datetime
