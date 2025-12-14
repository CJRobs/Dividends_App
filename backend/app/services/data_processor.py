"""
Data processing utilities for the Dividend Portfolio Dashboard API.

This module contains data loading, preprocessing, and aggregation functions
migrated from the original Streamlit utils.
"""

import pandas as pd
from datetime import datetime
from typing import Union, Optional
from pathlib import Path
from functools import lru_cache


def parse_datetime(column: pd.Series) -> pd.Series:
    """
    Parse date columns with multiple potential formats.

    Args:
        column: Pandas Series containing date strings

    Returns:
        Pandas Series with parsed datetime values
    """
    # Use mixed format parsing with dayfirst=True to handle various date formats
    return pd.to_datetime(column, format='mixed', dayfirst=True, errors="coerce")


def load_data(data_path: str) -> pd.DataFrame:
    """
    Load dividend data from CSV or directory of CSVs.

    Args:
        data_path: Path to CSV file or directory

    Returns:
        DataFrame with dividend data

    Raises:
        FileNotFoundError: If data path doesn't exist
        pd.errors.EmptyDataError: If CSV is empty
    """
    path = Path(data_path)

    if not path.exists():
        raise FileNotFoundError(f"Data path not found: {data_path}")

    # If it's a directory, read and concatenate all CSV files
    if path.is_dir():
        csv_files = list(path.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in: {data_path}")

        dfs = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                dfs.append(df)
            except Exception as e:
                print(f"Warning: Could not read {csv_file}: {e}")

        if not dfs:
            raise pd.errors.EmptyDataError("No valid CSV files could be read")

        df = pd.concat(dfs, ignore_index=True)
    else:
        # Single CSV file
        df = pd.read_csv(data_path)

    # Parse the Time column
    if "Time" in df.columns:
        df["Time"] = parse_datetime(df["Time"])

    return df


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
    if "Time" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["Time"]):
        df["Time"] = pd.to_datetime(df["Time"])

    # Extract time-based features
    df["Year"] = df["Time"].dt.year
    df["Month"] = df["Time"].dt.month
    df["MonthName"] = df["Time"].dt.month_name()
    df["Quarter"] = (
        "Q" + df["Time"].dt.quarter.astype(str) + " " + df["Year"].astype(str)
    )
    df["Day"] = df["Time"].dt.day
    df["DayOfWeek"] = df["Time"].dt.day_name()
    df["WeekOfYear"] = df["Time"].dt.isocalendar().week

    return df


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

    monthly_data = (
        df.groupby(df["Time"].dt.to_period("M"))
        .agg({"Total": ["sum", "count", "mean"], "Time": lambda x: x.iloc[0]})
        .reset_index(drop=True)
    )

    # Flatten column names
    monthly_data.columns = ["Total_Sum", "Total_Count", "Total_Mean", "Time"]
    monthly_data = monthly_data.sort_values("Time")
    monthly_data["Date"] = monthly_data["Time"]

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
        return f"{value / 1_000_000_000:.{decimals}f}B"
    elif abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"{value / 1_000:.{decimals}f}K"
    else:
        return f"{value:.{decimals}f}"


def validate_dataframe(df: pd.DataFrame, required_columns: list[str]) -> tuple[bool, Optional[str]]:
    """
    Validate that a DataFrame has the required columns.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names

    Returns:
        Tuple of (is_valid, error_message)
    """
    if df.empty:
        return False, "No data available for analysis"

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"

    return True, None


def get_ytd_data(df: pd.DataFrame, current_year: Optional[int] = None) -> pd.DataFrame:
    """
    Get year-to-date data.

    Args:
        df: Preprocessed dividend DataFrame
        current_year: Year to filter for (defaults to current year)

    Returns:
        YTD filtered DataFrame
    """
    if current_year is None:
        current_year = datetime.now().year

    return df[df["Year"] == current_year].copy()


def get_previous_year_data(df: pd.DataFrame, current_year: Optional[int] = None) -> pd.DataFrame:
    """
    Get previous year data.

    Args:
        df: Preprocessed dividend DataFrame
        current_year: Current year reference (defaults to current year)

    Returns:
        Previous year filtered DataFrame
    """
    if current_year is None:
        current_year = datetime.now().year

    return df[df["Year"] == (current_year - 1)].copy()


def aggregate_by_stock(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate dividend data by stock ticker.

    Args:
        df: Preprocessed dividend DataFrame

    Returns:
        DataFrame aggregated by ticker
    """
    if df.empty:
        return df

    stock_data = df.groupby("Ticker").agg({
        "Name": "first",
        "ISIN": "first",
        "Total": ["sum", "count", "mean", "min", "max"],
        "Time": ["min", "max"]
    }).reset_index()

    # Flatten column names
    stock_data.columns = [
        "Ticker", "Name", "ISIN",
        "Total_Sum", "Total_Count", "Total_Mean", "Total_Min", "Total_Max",
        "First_Date", "Last_Date"
    ]

    return stock_data


def get_recent_dividends(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """
    Get most recent dividend payments.

    Args:
        df: Preprocessed dividend DataFrame
        limit: Number of recent dividends to return

    Returns:
        DataFrame with recent dividends
    """
    if df.empty:
        return df

    return df.nlargest(limit, "Time")[["Ticker", "Name", "Total", "Time", "No. of shares"]]
