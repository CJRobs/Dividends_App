"""
Overview API endpoints.

Provides portfolio summary statistics, YTD charts, and recent dividends.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List
import pandas as pd
import numpy as np

from app.models.portfolio import (
    PortfolioSummary,
    StockSummary,
    RecentDividend,
    TimeSeriesData,
    ChartData,
    OverviewResponse
)
from app.config import get_settings, format_currency
from app.services.data_processor import (
    get_ytd_data,
    get_previous_year_data,
    aggregate_by_stock,
    get_recent_dividends,
    safe_divide
)

router = APIRouter()


def to_python_type(value):
    """Convert numpy/pandas types to native Python types."""
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    if isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.str_, str)):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return value


def get_data():
    """Dependency to get data from main app cache."""
    from app.main import get_data as _get_data
    return _get_data()


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(data: tuple = Depends(get_data)):
    """
    Get overall portfolio summary statistics.

    Returns summary including total dividends, YTD performance,
    stock count, and comparison with previous year.
    """
    df, monthly_data = data
    settings = get_settings()

    if df.empty:
        raise HTTPException(status_code=404, detail="No dividend data available")

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Calculate summary metrics
    total_dividends = float(df["Total"].sum())
    total_count = len(df)
    unique_stocks = df["Ticker"].nunique()
    average_dividend = float(df["Total"].mean())
    highest_dividend = float(df["Total"].max())
    lowest_dividend = float(df["Total"].min())

    # YTD calculations
    ytd_df = get_ytd_data(df, current_year)
    total_dividends_ytd = float(ytd_df["Total"].sum()) if not ytd_df.empty else 0.0

    # Previous year comparison
    prev_year_df = get_previous_year_data(df, current_year)
    # Get same months from previous year for fair comparison
    prev_year_ytd = prev_year_df[prev_year_df["Month"] <= current_month]
    prev_year_ytd_total = float(prev_year_ytd["Total"].sum()) if not prev_year_ytd.empty else 0.0

    ytd_change = total_dividends_ytd - prev_year_ytd_total
    ytd_change_percent = safe_divide(ytd_change, prev_year_ytd_total) * 100 if prev_year_ytd_total > 0 else None

    # Dates
    first_dividend_date = df["Time"].min()
    last_dividend_date = df["Time"].max()

    return PortfolioSummary(
        total_dividends=total_dividends,
        total_dividends_ytd=total_dividends_ytd,
        total_count=total_count,
        unique_stocks=unique_stocks,
        average_dividend=average_dividend,
        highest_dividend=highest_dividend,
        lowest_dividend=lowest_dividend,
        first_dividend_date=first_dividend_date,
        last_dividend_date=last_dividend_date,
        ytd_vs_last_year_change=ytd_change if prev_year_ytd_total > 0 else None,
        ytd_vs_last_year_percent=ytd_change_percent
    )


@router.get("/ytd-chart", response_model=TimeSeriesData)
async def get_ytd_chart(data: tuple = Depends(get_data)):
    """
    Get year-to-date cumulative dividend chart data.

    Returns time series data showing cumulative dividends over the current year.
    """
    df, monthly_data = data

    if df.empty:
        raise HTTPException(status_code=404, detail="No dividend data available")

    current_year = datetime.now().year
    ytd_df = get_ytd_data(df, current_year)

    if ytd_df.empty:
        return TimeSeriesData(dates=[], values=[], label="YTD Dividends")

    # Sort by time and calculate cumulative sum
    ytd_df = ytd_df.sort_values("Time")
    ytd_df["Cumulative"] = ytd_df["Total"].cumsum()

    # Format dates
    dates = ytd_df["Time"].dt.strftime("%Y-%m-%d").tolist()
    values = ytd_df["Cumulative"].tolist()

    return TimeSeriesData(
        dates=dates,
        values=values,
        label=f"YTD Dividends {current_year}"
    )


@router.get("/monthly-chart", response_model=ChartData)
async def get_monthly_chart(year: int = None, data: tuple = Depends(get_data)):
    """
    Get monthly dividend bar chart data.

    Args:
        year: Optional year filter (defaults to current year)

    Returns chart data with monthly totals.
    """
    df, monthly_data = data

    if df.empty:
        raise HTTPException(status_code=404, detail="No dividend data available")

    if year is None:
        year = datetime.now().year

    year_df = df[df["Year"] == year]

    if year_df.empty:
        return ChartData(labels=[], values=[], colors=None)

    # Group by month
    monthly_totals = year_df.groupby("Month")["Total"].sum().reset_index()

    # Create full 12 months with zeros for missing months
    from app.config import MONTH_NAMES
    all_months = pd.DataFrame({"Month": range(1, 13)})
    monthly_totals = all_months.merge(monthly_totals, on="Month", how="left").fillna(0)

    labels = [MONTH_NAMES[int(month)] for month in monthly_totals["Month"]]
    values = [float(v) for v in monthly_totals["Total"].tolist()]

    return ChartData(
        labels=labels,
        values=values,
        colors=None
    )


@router.get("/top-stocks", response_model=List[StockSummary])
async def get_top_stocks(limit: int = 10, data: tuple = Depends(get_data)):
    """
    Get top dividend-paying stocks.

    Args:
        limit: Number of top stocks to return (default 10)

    Returns list of top stocks by total dividends.
    """
    df, monthly_data = data

    if df.empty:
        raise HTTPException(status_code=404, detail="No dividend data available")

    # Aggregate by stock
    stock_agg = aggregate_by_stock(df)

    # Calculate percentage of portfolio
    total_dividends = df["Total"].sum()
    stock_agg["Percentage"] = (stock_agg["Total_Sum"] / total_dividends * 100)

    # Sort and limit
    stock_agg = stock_agg.nlargest(limit, "Total_Sum")

    # Convert to response model
    result = []
    for _, row in stock_agg.iterrows():
        # Ensure all numeric types are converted properly - pandas sometimes returns numpy types
        result.append(StockSummary(
            ticker=to_python_type(row["Ticker"]),
            name=to_python_type(row["Name"]),
            isin=to_python_type(row["ISIN"]),
            total_dividends=to_python_type(row["Total_Sum"]),
            dividend_count=to_python_type(row["Total_Count"]),
            average_dividend=to_python_type(row["Total_Mean"]),
            last_dividend_date=to_python_type(row["Last_Date"]),
            last_dividend_amount=to_python_type(row["Total_Max"]),
            percentage_of_portfolio=to_python_type(row["Percentage"])
        ))

    return result


@router.get("/recent-dividends", response_model=List[RecentDividend])
async def get_recent_dividends_endpoint(limit: int = 10, data: tuple = Depends(get_data)):
    """
    Get most recent dividend payments.

    Args:
        limit: Number of recent dividends to return (default 10)

    Returns list of recent dividend payments.
    """
    df, monthly_data = data

    if df.empty:
        raise HTTPException(status_code=404, detail="No dividend data available")

    recent = get_recent_dividends(df, limit)

    result = []
    for _, row in recent.iterrows():
        result.append(RecentDividend(
            ticker=to_python_type(row["Ticker"]),
            name=to_python_type(row["Name"]),
            amount=to_python_type(row["Total"]),
            date=to_python_type(row["Time"]),
            shares=to_python_type(row["No. of shares"])
        ))

    return result


@router.get("/", response_model=OverviewResponse)
async def get_complete_overview(data: tuple = Depends(get_data)):
    """
    Get complete overview data in a single request.

    Combines summary, YTD chart, monthly chart, top stocks, and recent dividends.
    """
    summary = await get_portfolio_summary(data)
    ytd_chart = await get_ytd_chart(data)
    monthly_chart = await get_monthly_chart(data=data)
    top_stocks = await get_top_stocks(data=data)
    recent_dividends = await get_recent_dividends_endpoint(data=data)

    return OverviewResponse(
        summary=summary,
        ytd_chart=ytd_chart,
        monthly_chart=monthly_chart,
        top_stocks=top_stocks,
        recent_dividends=recent_dividends
    )
