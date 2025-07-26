"""Dividend Portfolio Dashboard Main Application.

A comprehensive Streamlit application for tracking, analyzing,
and forecasting dividend income with advanced screening capabilities.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Import configuration and utilities
from config import load_config, AppConfig, format_currency, MONTH_ORDER
from utils import (
    setup_warnings, setup_page_config, load_css,
    load_data, preprocess_data, get_monthly_data,
    validate_dataframe, create_loading_spinner,
    apply_chart_theme, get_chart_theme
)

# Import tab modules
from tabs.overview import show_overview_tab
from tabs.monthly_analysis import show_monthly_analysis_tab
from tabs.stock_analysis import show_stock_analysis_tab
from tabs.dividend_screener import show_dividend_screener_tab
from tabs.forecast import show_forecast_tab
from tabs.pdf_reports import show_pdf_reports_tab

# Setup warnings filter
setup_warnings()


def main() -> None:
    """Main application function."""
    try:
        # Load configuration
        config = load_config()
        
        # Set page configuration
        setup_page_config(config)
        
        # Load CSS
        load_css()
        
        # App title
        st.title("📊 Dividend Portfolio Dashboard")
        st.markdown("Track, analyze, forecast and optimize your dividend income over time")
        
    except ValueError as e:
        st.error(f"⚙️ Configuration Error: {e}")
        st.info("💡 Please check your environment variables and .env file.")
        st.code("""
# Create a .env file in your project root with:
ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
DEFAULT_CURRENCY=GBP
        """)
        return
    except Exception as e:
        st.error(f"❌ Application startup error: {e}")
        st.info("🔄 Please refresh the page or contact support if the issue persists.")
        return
    
    # Navigation in sidebar
    st.sidebar.title("Navigation")
    
    # Use radio buttons for navigation instead of tabs - Updated to include Dividend Screener
    page = st.sidebar.radio(
        "Select Page",
        ["📈 Overview", "📅 Monthly Analysis", "🏢 Stock Analysis", 
         "🔍 Dividend Screener", "🔮 Forecast", "📄 PDF Reports"]  # Updated navigation
    )
    
    # Load and preprocess data with error handling
    with create_loading_spinner("Loading and processing data..."):
        try:
            df = load_data()
            
            if not validate_dataframe(df, ['Time', 'Total']):
                return
                
            df = preprocess_data(df)
            monthly_data = get_monthly_data(df)
            
        except Exception as e:
            st.error(f"Error loading or processing data: {e}")
            st.info("Please check your data source and try again.")
            return
    
    # Get current date for filtering
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    # Create a dict with common parameters to pass to each tab
    common_params: Dict[str, Any] = {
        'df': df,
        'monthly_data': monthly_data,
        'currency': config.default_currency,
        'theme': "Dark",  # Fixed dark theme
        'current_date': current_date,
        'current_year': current_year,
        'current_month': current_month,
        'config': config,
        'format_currency': format_currency,
        'get_month_order': lambda: MONTH_ORDER
    }
    
    # Main content based on selection - Updated to include Dividend Screener
    if page == "📈 Overview":
        show_overview_tab(**common_params)
    elif page == "📅 Monthly Analysis":
        show_monthly_analysis_tab(**common_params)
    elif page == "🏢 Stock Analysis":
        show_stock_analysis_tab(**common_params)
    elif page == "🔍 Dividend Screener":  # Updated to call dividend screener
        show_dividend_screener_tab(**common_params)
    elif page == "🔮 Forecast":
        show_forecast_tab(**common_params)
    elif page == "📄 PDF Reports":
        show_pdf_reports_tab(**common_params)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        import traceback
        st.error(traceback.format_exc())