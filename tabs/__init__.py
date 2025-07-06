# This file makes the tabs directory a Python package
# Import tab modules for easier access
from tabs.overview import show_overview_tab
from tabs.monthly_analysis import show_monthly_analysis_tab
from tabs.stock_analysis import show_stock_analysis_tab
from tabs.dividend_screener import show_dividend_screener_tab  # Updated import
from tabs.forecast import show_forecast_tab

__all__ = [
    'show_overview_tab',
    'show_monthly_analysis_tab',
    'show_stock_analysis_tab',
    'show_dividend_screener_tab',  # Updated export
    'show_forecast_tab'
]