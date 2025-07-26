"""
Utility functions for the Dividend Portfolio Dashboard.

This module contains common utility functions used across multiple tabs
to reduce code duplication and improve maintainability.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Union, Dict, Any, Callable
import io
import sys
import warnings
from config import AppConfig, format_currency as config_format_currency


class WarningFilter(io.StringIO):
    """Custom warning filter to suppress specific Streamlit warnings."""
    
    def write(self, s: str) -> None:
        """Write warning to stderr if it's not in the filter list."""
        if "missing ScriptRunContext" not in s and "No runtime found" not in s:
            sys.__stderr__.write(s)


def setup_warnings() -> None:
    """Setup warning filters for the application."""
    sys.stderr = WarningFilter()
    warnings.filterwarnings("ignore")


def setup_page_config(config: AppConfig) -> None:
    """Setup Streamlit page configuration."""
    st.set_page_config(
        page_title=config.page_title,
        page_icon=config.page_icon,
        layout=config.layout,
        initial_sidebar_state="expanded"
    )


def load_css(css_path: str = "static/styles.css") -> None:
    """Load and apply CSS styles."""
    try:
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Could not load CSS file. Using default styling.")


@st.cache_data(ttl=3600)
def parse_datetime(column: pd.Series) -> pd.Series:
    """
    Parse date columns with multiple potential formats.
    
    Args:
        column: Pandas Series containing date strings
        
    Returns:
        Pandas Series with parsed datetime values
    """
    try:
        return pd.to_datetime(column, format='%Y-%m-%d %H:%M:%S', dayfirst=True)
    except ValueError:
        pass
    try:
        return pd.to_datetime(column, format='%d/%m/%Y %H:%M', dayfirst=True)
    except ValueError:
        pass
    return pd.to_datetime(column, dayfirst=True, errors='coerce')


@st.cache_data(ttl=3600, show_spinner="Loading dividend data...")
def load_data() -> pd.DataFrame:
    """
    Load data using the imsciences module or fallback to demo data.
    
    Returns:
        DataFrame with dividend data
        
    Raises:
        Exception: If data loading fails completely
    """
    try:
        from imsciences import dataprocessing
        import os
        
        dp = dataprocessing()
        fp = dp.get_wd_levels(0)
        fp = os.path.join(fp, "dividends")
        df = dp.read_and_concatenate_files(fp, "csv")
        df['Time'] = df['Time'].apply(parse_datetime)
        return df
    except ImportError as e:
        st.error(f"Required module 'imsciences' not found: {e}")
        return pd.DataFrame(columns=['Time', 'Name', 'Total'])
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=['Time', 'Name', 'Total'])


@st.cache_data(show_spinner="Preprocessing data...")
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess the data for analysis.
    
    Args:
        df: Raw dividend DataFrame
        
    Returns:
        Preprocessed DataFrame with additional time-based columns
    """
    if df.empty:
        return df
    
    # Ensure Time is datetime
    if 'Time' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['Time']):
        df['Time'] = pd.to_datetime(df['Time'])
    
    # Extract time-based features
    df['Year'] = df['Time'].dt.year
    df['Month'] = df['Time'].dt.month
    df['MonthName'] = df['Time'].dt.month_name()
    df['Quarter'] = 'Q' + df['Time'].dt.quarter.astype(str) + ' ' + df['Year'].astype(str)
    df['Day'] = df['Time'].dt.day
    df['DayOfWeek'] = df['Time'].dt.day_name()
    df['WeekOfYear'] = df['Time'].dt.isocalendar().week
    
    return df


@st.cache_data(show_spinner="Aggregating monthly data...")
def get_monthly_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data to monthly level for reuse across tabs.
    
    Args:
        df: Preprocessed dividend DataFrame
        
    Returns:
        Monthly aggregated DataFrame
    """
    if df.empty:
        return df
    
    monthly_data = df.groupby(df['Time'].dt.to_period('M')).agg({
        'Total': ['sum', 'count', 'mean'],
        'Time': lambda x: x.iloc[0]
    }).reset_index(drop=True)
    
    # Flatten column names
    monthly_data.columns = ['Total_Sum', 'Total_Count', 'Total_Mean', 'Time']
    monthly_data = monthly_data.sort_values('Time')
    monthly_data['Date'] = monthly_data['Time']
    
    return monthly_data


def safe_divide(numerator: Union[float, int], denominator: Union[float, int]) -> float:
    """
    Safely divide two numbers, returning 0 if denominator is 0.
    
    Args:
        numerator: The numerator
        denominator: The denominator
        
    Returns:
        The result of division or 0 if denominator is 0
    """
    return numerator / denominator if denominator != 0 else 0.0


def calculate_growth_rate(current: float, previous: float) -> float:
    """
    Calculate growth rate between two values.
    
    Args:
        current: Current period value
        previous: Previous period value
        
    Returns:
        Growth rate as a percentage
    """
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a value as a percentage.
    
    Args:
        value: The value to format
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"


def create_metric_card(title: str, value: str, delta: Optional[str] = None) -> None:
    """
    Create a styled metric card.
    
    Args:
        title: Metric title
        value: Metric value
        delta: Optional delta value for comparison
    """
    if delta:
        st.metric(label=title, value=value, delta=delta)
    else:
        st.metric(label=title, value=value)


def handle_api_error(error: Exception, context: str = "API call") -> None:
    """
    Handle API errors with user-friendly messages.
    
    Args:
        error: The exception that occurred
        context: Context description for the error
    """
    error_msg = str(error).lower()
    
    if "rate limit" in error_msg or "429" in error_msg:
        st.error(f"⚠️ API rate limit exceeded. Please wait a moment before trying again.")
    elif "api key" in error_msg or "401" in error_msg:
        st.error(f"🔑 API authentication failed. Please check your API key configuration.")
    elif "network" in error_msg or "connection" in error_msg:
        st.error(f"🌐 Network error occurred. Please check your internet connection.")
    else:
        st.error(f"❌ {context} failed: {error}")


def validate_dataframe(df: pd.DataFrame, required_columns: list[str]) -> bool:
    """
    Validate that a DataFrame has the required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        
    Returns:
        True if valid, False otherwise
    """
    if df.empty:
        st.warning("No data available for analysis.")
        return False
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return False
    
    return True


def create_loading_spinner(message: str = "Loading..."):
    """
    Create a context manager for loading spinners.
    
    Args:
        message: Loading message to display
        
    Returns:
        Streamlit spinner context manager
    """
    return st.spinner(message)


def format_large_number(value: float, decimals: int = 2) -> str:
    """
    Format large numbers with appropriate suffixes (K, M, B).
    
    Args:
        value: The number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted number string
    """
    if abs(value) >= 1_000_000_000:
        return f"{value/1_000_000_000:.{decimals}f}B"
    elif abs(value) >= 1_000_000:
        return f"{value/1_000_000:.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:.{decimals}f}K"
    else:
        return f"{value:.{decimals}f}"


def get_date_range_filter(df: pd.DataFrame, date_column: str = 'Time') -> tuple[datetime, datetime]:
    """
    Create date range filter widget.
    
    Args:
        df: DataFrame containing the date column
        date_column: Name of the date column
        
    Returns:
        Tuple of (start_date, end_date)
    """
    if df.empty or date_column not in df.columns:
        return datetime.now(), datetime.now()
    
    min_date = df[date_column].min().date()
    max_date = df[date_column].max().date()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)
    
    return start_date, end_date