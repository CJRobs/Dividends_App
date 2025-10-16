"""
Models package for the Dividend Portfolio Dashboard API.
"""

from .portfolio import (
    DividendRecord,
    MonthlyData,
    YearlyData,
    PortfolioSummary,
    StockSummary,
    RecentDividend,
    ChartData,
    TimeSeriesData,
    OverviewResponse,
)

from .dividend import (
    StockInfo,
    StockHistory,
    MonthlyComparison,
    ScreenerFilterOperator,
    ScreenerFilter,
    ScreenerCriteria,
    ScreenerResult,
    ForecastMethod,
    ForecastScenario,
    ForecastRequest,
    ForecastDataPoint,
    ForecastResponse,
    ReportTemplate,
    ReportRequest,
    ReportResponse,
)

__all__ = [
    # Portfolio models
    "DividendRecord",
    "MonthlyData",
    "YearlyData",
    "PortfolioSummary",
    "StockSummary",
    "RecentDividend",
    "ChartData",
    "TimeSeriesData",
    "OverviewResponse",
    # Dividend models
    "StockInfo",
    "StockHistory",
    "MonthlyComparison",
    "ScreenerFilterOperator",
    "ScreenerFilter",
    "ScreenerCriteria",
    "ScreenerResult",
    "ForecastMethod",
    "ForecastScenario",
    "ForecastRequest",
    "ForecastDataPoint",
    "ForecastResponse",
    "ReportTemplate",
    "ReportRequest",
    "ReportResponse",
]
