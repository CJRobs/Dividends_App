"""
Overview API endpoints.

Provides portfolio summary statistics, YTD charts, and recent dividends.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List
import pandas as pd

from app.models.portfolio import (
    PortfolioSummary,
    StockSummary,
    RecentDividend,
    TimeSeriesData,
    ChartData,
    OverviewResponse,
    AnnualStats,
    DividendStreakInfo
)
from app.config import get_settings, format_currency
from app.services.data_processor import (
    get_ytd_data,
    get_previous_year_data,
    aggregate_by_stock,
    get_recent_dividends,
    safe_divide
)
from app.dependencies import get_data
from app.utils import to_python_type, cached_response

router = APIRouter()


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


@router.get("/yoy-comparison")
async def get_yoy_comparison(data: tuple = Depends(get_data)):
    """
    Get year-over-year comparison data for charts.

    Returns monthly totals for each year to enable YoY comparison.
    """
    df, _ = data

    if df.empty:
        raise HTTPException(status_code=404, detail="No dividend data available")

    # Get all years in the data
    years = sorted(df["Year"].unique())

    # Create monthly totals for each year
    from app.config import MONTH_NAMES

    result = {
        "years": [],
        "months": list(MONTH_NAMES.values()),
        "data": {}
    }

    for year in years:
        year_df = df[df["Year"] == year]
        monthly = year_df.groupby("Month")["Total"].sum()

        # Fill in all 12 months
        monthly_values = [float(monthly.get(m, 0)) for m in range(1, 13)]
        result["data"][str(int(year))] = monthly_values
        result["years"].append(int(year))

    return result


@router.get("/annual-stats", response_model=List[AnnualStats])
@cached_response(ttl_minutes=5)
async def get_annual_stats(data: tuple = Depends(get_data)):
    """
    Get annual statistics for each year.

    Returns total, count, average, and growth for each year.
    """
    df, _ = data

    if df.empty:
        raise HTTPException(status_code=404, detail="No dividend data available")

    # Aggregate by year
    yearly = df.groupby("Year").agg({
        "Total": ["sum", "count", "mean"],
        "Ticker": "nunique"
    }).reset_index()

    yearly.columns = ["year", "total", "count", "average", "unique_stocks"]
    yearly = yearly.sort_values("year")

    # Calculate year-over-year growth
    yearly["growth"] = yearly["total"].pct_change() * 100

    result = []
    for _, row in yearly.iterrows():
        result.append(AnnualStats(
            year=int(row["year"]),
            total=float(row["total"]),
            count=int(row["count"]),
            average=float(row["average"]),
            unique_stocks=int(row["unique_stocks"]),
            growth=float(row["growth"]) if pd.notna(row["growth"]) else None
        ))

    return result


@router.get("/dividend-streak", response_model=DividendStreakInfo)
@cached_response(ttl_minutes=5)
async def get_dividend_streak(data: tuple = Depends(get_data)):
    """
    Get dividend streak information - consecutive months with dividends.
    """
    df, _ = data

    if df.empty:
        return DividendStreakInfo(
            current_streak=0,
            longest_streak=0,
            months_with_dividends=0,
            total_months_span=0
        )

    # Get unique months with dividends - work on a copy to avoid modifying cached data
    df_copy = df.copy()
    df_copy["YearMonth"] = df_copy["Time"].dt.to_period("M")
    months_with_divs = df_copy["YearMonth"].unique()

    # Sort months
    months_sorted = sorted(months_with_divs)

    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    temp_streak = 1

    for i in range(1, len(months_sorted)):
        # Check if consecutive
        if (months_sorted[i] - months_sorted[i-1]).n == 1:
            temp_streak += 1
        else:
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 1

    longest_streak = max(longest_streak, temp_streak)

    # Calculate current streak (from most recent month backwards)
    if len(months_sorted) > 0:
        current_month = pd.Period(datetime.now(), freq="M")
        if months_sorted[-1] == current_month or months_sorted[-1] == current_month - 1:
            current_streak = 1
            for i in range(len(months_sorted) - 2, -1, -1):
                if (months_sorted[i+1] - months_sorted[i]).n == 1:
                    current_streak += 1
                else:
                    break

    return DividendStreakInfo(
        current_streak=current_streak,
        longest_streak=longest_streak,
        months_with_dividends=len(months_with_divs),
        total_months_span=(months_sorted[-1] - months_sorted[0]).n + 1 if len(months_sorted) > 1 else 1
    )


@router.get("/distribution")
async def get_distribution_analysis(data: tuple = Depends(get_data)):
    """
    Get dividend distribution and analysis data.

    Returns:
    - portfolio_allocation: Top 10 stocks + Others grouped
    - monthly_totals: Dividends by calendar month (Jan-Dec) across all years
    - top_stocks_horizontal: Top 10 for horizontal bar chart
    - recent_trend: Last 12 months of dividend data
    - summary_stats: Additional statistics
    - projected_annual: Projected annual income based on current pace
    - concentration_risk: Portfolio concentration warning info
    - dividend_streak: Streak information
    """
    df, monthly_data = data
    from app.config import MONTH_NAMES

    if df.empty:
        raise HTTPException(status_code=404, detail="No dividend data available")

    # Portfolio allocation (Top 10 + Others)
    stock_totals = df.groupby(["Ticker", "Name"])["Total"].sum().reset_index()
    stock_totals = stock_totals.sort_values("Total", ascending=False)

    top_10 = stock_totals.head(10)
    others_total = stock_totals.iloc[10:]["Total"].sum() if len(stock_totals) > 10 else 0

    allocation = []
    for _, row in top_10.iterrows():
        allocation.append({
            "name": row["Ticker"],
            "value": float(row["Total"]),
            "fullName": row["Name"]
        })

    if others_total > 0:
        allocation.append({
            "name": "Others",
            "value": float(others_total),
            "fullName": f"Other {len(stock_totals) - 10} stocks"
        })

    # Monthly totals across ALL years (Jan-Dec aggregated)
    monthly_all_years = df.groupby("Month")["Total"].sum().reset_index()
    monthly_totals = []
    for month_num in range(1, 13):
        month_data = monthly_all_years[monthly_all_years["Month"] == month_num]
        total = float(month_data["Total"].iloc[0]) if not month_data.empty else 0.0
        monthly_totals.append({
            "month": MONTH_NAMES[month_num][:3],
            "monthFull": MONTH_NAMES[month_num],
            "value": total
        })

    # Top 10 stocks for horizontal bar (sorted for display)
    top_stocks_h = []
    for _, row in top_10.iterrows():
        top_stocks_h.append({
            "ticker": row["Ticker"],
            "name": row["Name"],
            "total": float(row["Total"])
        })

    # Recent 12 months trend
    df_sorted = df.sort_values("Time")
    df_sorted["YearMonth"] = df_sorted["Time"].dt.to_period("M")
    monthly_recent = df_sorted.groupby("YearMonth")["Total"].sum()

    # Get last 12 months
    recent_periods = sorted(monthly_recent.index)[-12:]
    recent_trend = []
    for period in recent_periods:
        recent_trend.append({
            "date": str(period),
            "label": period.strftime("%b %Y"),
            "value": float(monthly_recent[period])
        })

    # Summary statistics
    total_dividends = float(df["Total"].sum())
    monthly_avg = float(monthly_recent.mean()) if len(monthly_recent) > 0 else 0
    best_month = monthly_recent.idxmax() if len(monthly_recent) > 0 else None
    best_month_value = float(monthly_recent.max()) if len(monthly_recent) > 0 else 0

    # YoY growth calculation
    current_year = datetime.now().year
    prev_year = current_year - 1
    cy_total = float(df[df["Year"] == current_year]["Total"].sum())
    py_total = float(df[df["Year"] == prev_year]["Total"].sum())
    yoy_growth = ((cy_total - py_total) / py_total * 100) if py_total > 0 else None

    summary_stats = {
        "total_lifetime": total_dividends,
        "monthly_average": monthly_avg,
        "best_month": str(best_month) if best_month else None,
        "best_month_value": best_month_value,
        "yoy_growth": yoy_growth
    }

    # Projected annual income based on current year's pace
    current_year = datetime.now().year
    current_month = datetime.now().month
    ytd_total = float(df[df["Year"] == current_year]["Total"].sum())

    # Project based on YTD average (annualized)
    if current_month > 0:
        projected_annual = (ytd_total / current_month) * 12
    else:
        projected_annual = monthly_avg * 12

    # Calculate projected vs last year
    last_year_total = float(df[df["Year"] == current_year - 1]["Total"].sum()) if current_year > 1 else 0
    projected_vs_last_year = ((projected_annual - last_year_total) / last_year_total * 100) if last_year_total > 0 else None

    projected_income = {
        "ytd_total": ytd_total,
        "projected_annual": projected_annual,
        "last_year_total": last_year_total,
        "projected_vs_last_year": projected_vs_last_year,
        "months_elapsed": current_month
    }

    # Portfolio concentration risk analysis
    total_portfolio = float(stock_totals["Total"].sum())
    top_3_total = float(stock_totals.head(3)["Total"].sum()) if len(stock_totals) >= 3 else total_portfolio
    top_3_percentage = (top_3_total / total_portfolio * 100) if total_portfolio > 0 else 0

    # Herfindahl-Hirschman Index for concentration
    stock_shares = stock_totals["Total"] / total_portfolio * 100
    hhi = float((stock_shares ** 2).sum())

    # Determine concentration level
    if top_3_percentage > 60:
        concentration_level = "High"
        concentration_warning = f"Top 3 stocks represent {top_3_percentage:.1f}% of dividends. Consider diversifying."
    elif top_3_percentage > 40:
        concentration_level = "Medium"
        concentration_warning = f"Top 3 stocks represent {top_3_percentage:.1f}% of dividends."
    else:
        concentration_level = "Low"
        concentration_warning = None

    concentration_risk = {
        "top_3_percentage": top_3_percentage,
        "top_3_stocks": [row["Ticker"] for _, row in stock_totals.head(3).iterrows()],
        "hhi_index": hhi,
        "concentration_level": concentration_level,
        "warning": concentration_warning,
        "unique_stocks": len(stock_totals)
    }

    # Dividend streak info (simplified calculation inline)
    df_copy = df.copy()
    df_copy["YearMonth"] = df_copy["Time"].dt.to_period("M")
    months_with_divs = sorted(df_copy["YearMonth"].unique())

    current_streak = 0
    longest_streak = 1
    temp_streak = 1

    for i in range(1, len(months_with_divs)):
        if (months_with_divs[i] - months_with_divs[i-1]).n == 1:
            temp_streak += 1
        else:
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 1
    longest_streak = max(longest_streak, temp_streak)

    # Current streak
    if len(months_with_divs) > 0:
        current_period = pd.Period(datetime.now(), freq="M")
        if months_with_divs[-1] == current_period or months_with_divs[-1] == current_period - 1:
            current_streak = 1
            for i in range(len(months_with_divs) - 2, -1, -1):
                if (months_with_divs[i+1] - months_with_divs[i]).n == 1:
                    current_streak += 1
                else:
                    break

    dividend_streak = {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "months_with_dividends": len(months_with_divs),
        "consistency_rate": (len(months_with_divs) / ((months_with_divs[-1] - months_with_divs[0]).n + 1) * 100) if len(months_with_divs) > 1 else 100
    }

    return {
        "portfolio_allocation": allocation,
        "monthly_totals": monthly_totals,
        "top_stocks_horizontal": top_stocks_h,
        "recent_trend": recent_trend,
        "summary_stats": summary_stats,
        "projected_income": projected_income,
        "concentration_risk": concentration_risk,
        "dividend_streak": dividend_streak
    }


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
