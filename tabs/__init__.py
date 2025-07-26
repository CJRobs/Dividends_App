"""Tabs Package for Dividend Portfolio Dashboard.

This package contains all the tab modules for the dividend portfolio dashboard.
Each module provides a specific view or functionality for analyzing dividend data.

Modules:
    overview: Main dashboard overview with key metrics and summaries
    monthly_analysis: Monthly breakdown and analysis of dividend income
    stock_analysis: Individual stock performance and analysis
    dividend_screener: Stock screening and discovery tools
    forecast: Predictive modeling and forecasting capabilities
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Import tab modules for easier access
from tabs.overview import show_overview_tab
from tabs.monthly_analysis import show_monthly_analysis_tab
from tabs.stock_analysis import show_stock_analysis_tab
from tabs.dividend_screener import show_dividend_screener_tab
from tabs.forecast import show_forecast_tab

__all__ = [
    "show_overview_tab",
    "show_monthly_analysis_tab",
    "show_stock_analysis_tab",
    "show_dividend_screener_tab",
    "show_forecast_tab",
]

__version__ = "2.0.0"
__author__ = "Dividend Portfolio Dashboard Team"
