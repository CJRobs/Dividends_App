"""
Stock Analysis API endpoints.

Provides stock-level analysis, period breakdowns, and concentration metrics.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Literal
from datetime import datetime
import pandas as pd
import numpy as np

from app.models.stocks import (
    PeriodAnalysisResponse,
    PeriodData,
    GrowthAnalysisResponse,
    GrowthData,
    ConcentrationData,
    StockDistribution,
    StockListItem,
    StockDetail,
    StockAnalysisResponse,
    PaymentHistory,
    YearlyTotal,
    MonthlyGrowth,
    StockOverviewResponse,
)
from app.dependencies import get_data
from app.utils import to_python_type, cached_response
from app.utils.validators import validate_ticker, validate_year

router = APIRouter()


def get_concentration_risk(pct: float, thresholds: tuple) -> str:
    """Determine concentration risk level."""
    if pct > thresholds[0]:
        return "High"
    elif pct > thresholds[1]:
        return "Medium"
    else:
        return "Low"


def determine_payment_cadence(payments_per_year: float) -> str:
    """Determine payment cadence based on average payments per year."""
    if payments_per_year >= 10:
        return "Monthly"
    elif payments_per_year >= 3.5:
        return "Quarterly"
    elif payments_per_year >= 1.5:
        return "Semi-annual"
    elif payments_per_year >= 0.8:
        return "Annual"
    return "Irregular"


@router.get("/list", response_model=List[StockListItem])
@cached_response(ttl_minutes=5)
async def list_stocks(
    limit: int = Query(50, description="Maximum number of stocks to return"),
    data: tuple = Depends(get_data)
):
    """Get list of all stocks in portfolio sorted by total dividends."""
    df, monthly_data = data

    if df.empty:
        return []

    # Aggregate by stock
    stock_agg = df.groupby(["Ticker", "Name"]).agg({
        "Total": ["sum", "count", "mean"],
        "Time": "max"
    }).reset_index()

    stock_agg.columns = ["Ticker", "Name", "Total_Sum", "Total_Count", "Total_Mean", "Last_Date"]

    # Calculate percentage of portfolio
    total_dividends = df["Total"].sum()
    stock_agg["Percentage"] = (stock_agg["Total_Sum"] / total_dividends * 100)

    # Get last dividend amount
    last_amounts = df.sort_values("Time").groupby("Ticker").last()["Total"]
    stock_agg["Last_Amount"] = stock_agg["Ticker"].map(last_amounts)

    # Sort by total and limit
    stock_agg = stock_agg.nlargest(limit, "Total_Sum")

    result = []
    for _, row in stock_agg.iterrows():
        result.append(StockListItem(
            ticker=to_python_type(row["Ticker"]),
            name=to_python_type(row["Name"]),
            total_dividends=to_python_type(row["Total_Sum"]),
            dividend_count=to_python_type(row["Total_Count"]),
            average_dividend=to_python_type(row["Total_Mean"]),
            percentage_of_portfolio=to_python_type(row["Percentage"]),
            last_dividend_date=to_python_type(row["Last_Date"]),
            last_dividend_amount=to_python_type(row["Last_Amount"])
        ))

    return result


@router.get("/by-period", response_model=PeriodAnalysisResponse)
async def get_stocks_by_period(
    period_type: Literal["Monthly", "Quarterly", "Yearly"] = Query("Monthly"),
    data: tuple = Depends(get_data)
):
    """
    Get dividend totals by stock for each time period.

    Returns data suitable for stacked bar charts.
    """
    df, monthly_data = data

    if df.empty:
        return PeriodAnalysisResponse(periods=[], stocks=[], data=[], period_type=period_type)

    time_data = df.copy()

    if period_type == "Monthly":
        time_data["Period"] = pd.to_datetime(
            time_data["Year"].astype(str) + "-" + time_data["Month"].astype(str) + "-01"
        )
        time_data["PeriodName"] = time_data["Period"].dt.strftime("%b %Y")
        time_data["PeriodKey"] = time_data["Period"].dt.strftime("%Y-%m")

    elif period_type == "Quarterly":
        time_data["QuarterNum"] = time_data["Quarter"].str.split(" ").str[0].str[1].astype(int)
        time_data["QuarterYear"] = time_data["Quarter"].str.split(" ").str[1].astype(int)
        time_data["Period"] = pd.to_datetime(
            time_data["QuarterYear"].astype(str) + "-" +
            ((time_data["QuarterNum"] * 3) - 2).astype(str) + "-01"
        )
        time_data["PeriodName"] = time_data["Quarter"]
        time_data["PeriodKey"] = (
            time_data["QuarterYear"].astype(str) + "-Q" + time_data["QuarterNum"].astype(str)
        )

    else:  # Yearly
        time_data["Period"] = pd.to_datetime(time_data["Year"].astype(str) + "-01-01")
        time_data["PeriodName"] = time_data["Year"].astype(str)
        time_data["PeriodKey"] = time_data["Year"].astype(str)

    # Group by period and stock
    period_totals = (
        time_data.groupby(["Period", "PeriodName", "PeriodKey", "Name"])["Total"]
        .sum()
        .reset_index()
    )
    period_totals = period_totals.sort_values("Period")

    # Get unique periods and stocks
    periods = period_totals.sort_values("Period")["PeriodName"].unique().tolist()
    stocks = sorted(period_totals["Name"].unique().tolist())

    # Build period data
    result_data = []
    for period_name in periods:
        period_df = period_totals[period_totals["PeriodName"] == period_name]
        period_key = period_df["PeriodKey"].iloc[0] if not period_df.empty else period_name

        stock_amounts = {}
        for _, row in period_df.iterrows():
            stock_amounts[row["Name"]] = to_python_type(row["Total"])

        total = sum(stock_amounts.values())

        result_data.append(PeriodData(
            period=period_name,
            period_key=period_key,
            stocks=stock_amounts,
            total=total
        ))

    return PeriodAnalysisResponse(
        periods=periods,
        stocks=stocks,
        data=result_data,
        period_type=period_type
    )


@router.get("/growth", response_model=GrowthAnalysisResponse)
async def get_growth_analysis(
    period_type: Literal["Monthly", "Quarterly", "Yearly"] = Query("Monthly"),
    data: tuple = Depends(get_data)
):
    """Get period-over-period growth rates."""
    df, monthly_data = data

    if df.empty:
        return GrowthAnalysisResponse(data=[], average_growth=None)

    time_data = df.copy()

    if period_type == "Monthly":
        time_data["Period"] = pd.to_datetime(
            time_data["Year"].astype(str) + "-" + time_data["Month"].astype(str) + "-01"
        )
        time_data["PeriodName"] = time_data["Period"].dt.strftime("%b %Y")

    elif period_type == "Quarterly":
        time_data["QuarterNum"] = time_data["Quarter"].str.split(" ").str[0].str[1].astype(int)
        time_data["QuarterYear"] = time_data["Quarter"].str.split(" ").str[1].astype(int)
        time_data["Period"] = pd.to_datetime(
            time_data["QuarterYear"].astype(str) + "-" +
            ((time_data["QuarterNum"] * 3) - 2).astype(str) + "-01"
        )
        time_data["PeriodName"] = time_data["Quarter"]

    else:  # Yearly
        time_data["Period"] = pd.to_datetime(time_data["Year"].astype(str) + "-01-01")
        time_data["PeriodName"] = time_data["Year"].astype(str)

    # Aggregate by period
    period_totals = time_data.groupby(["Period", "PeriodName"])["Total"].sum().reset_index()
    period_totals = period_totals.sort_values("Period")

    # Calculate growth
    period_totals["Previous"] = period_totals["Total"].shift(1)
    period_totals["Growth"] = (
        (period_totals["Total"] - period_totals["Previous"]) / period_totals["Previous"] * 100
    )
    period_totals["Growth"] = period_totals["Growth"].fillna(0)

    result_data = []
    for _, row in period_totals.iterrows():
        result_data.append(GrowthData(
            period=row["PeriodName"],
            total=to_python_type(row["Total"]),
            growth_percent=to_python_type(row["Growth"]) if not pd.isna(row["Previous"]) else None
        ))

    avg_growth = period_totals["Growth"].iloc[1:].mean() if len(period_totals) > 1 else None

    return GrowthAnalysisResponse(
        data=result_data,
        average_growth=to_python_type(avg_growth)
    )


@router.get("/distribution", response_model=List[StockDistribution])
@cached_response(ttl_minutes=5)
async def get_stock_distribution(data: tuple = Depends(get_data)):
    """Get portfolio distribution by stock for pie chart."""
    df, monthly_data = data

    if df.empty:
        return []

    stock_totals = df.groupby("Name")["Total"].sum().reset_index()
    stock_totals = stock_totals.sort_values("Total", ascending=False)

    total = stock_totals["Total"].sum()
    stock_totals["Percentage"] = (stock_totals["Total"] / total * 100)

    result = []
    for _, row in stock_totals.iterrows():
        result.append(StockDistribution(
            name=row["Name"],
            total=to_python_type(row["Total"]),
            percentage=to_python_type(row["Percentage"])
        ))

    return result


@router.get("/concentration", response_model=ConcentrationData)
@cached_response(ttl_minutes=5)
async def get_concentration_analysis(data: tuple = Depends(get_data)):
    """Get concentration risk analysis."""
    df, monthly_data = data

    if df.empty:
        return ConcentrationData(
            top_1_percent=0, top_3_percent=0, top_5_percent=0, top_10_percent=0,
            top_1_risk="Low", top_3_risk="Low", top_5_risk="Low", top_10_risk="Low"
        )

    stock_totals = df.groupby("Name")["Total"].sum().reset_index()
    stock_totals = stock_totals.sort_values("Total", ascending=False)

    total = stock_totals["Total"].sum()
    stock_totals["Percentage"] = (stock_totals["Total"] / total * 100)

    top_1 = stock_totals.head(1)["Percentage"].sum()
    top_3 = stock_totals.head(3)["Percentage"].sum()
    top_5 = stock_totals.head(5)["Percentage"].sum()
    top_10 = stock_totals.head(10)["Percentage"].sum()

    return ConcentrationData(
        top_1_percent=to_python_type(top_1),
        top_3_percent=to_python_type(top_3),
        top_5_percent=to_python_type(top_5),
        top_10_percent=to_python_type(top_10),
        top_1_risk=get_concentration_risk(top_1, (15, 10)),
        top_3_risk=get_concentration_risk(top_3, (40, 25)),
        top_5_risk=get_concentration_risk(top_5, (60, 40)),
        top_10_risk=get_concentration_risk(top_10, (80, 60))
    )


@router.get("/", response_model=StockOverviewResponse)
async def get_stocks_overview(data: tuple = Depends(get_data)):
    """Get complete stocks overview in a single request."""
    stocks = await list_stocks(limit=50, data=data)
    distribution = await get_stock_distribution(data)
    concentration = await get_concentration_analysis(data)

    df, _ = data
    total_dividends = float(df["Total"].sum()) if not df.empty else 0

    return StockOverviewResponse(
        stocks=stocks,
        distribution=distribution,
        concentration=concentration,
        total_stocks=len(stocks),
        total_dividends=total_dividends
    )


@router.get("/{ticker}", response_model=StockAnalysisResponse)
async def get_stock_details(ticker: str, data: tuple = Depends(get_data)):
    """Get detailed analysis for a specific stock."""
    # Validate ticker format
    ticker = validate_ticker(ticker)

    df, monthly_data = data

    # Filter by ticker OR name (case-insensitive)
    company_data = df[
        (df["Ticker"].str.upper() == ticker.upper()) |
        (df["Name"].str.upper() == ticker.upper())
    ].copy()

    if company_data.empty:
        raise HTTPException(status_code=404, detail=f"Stock '{ticker}' not found")

    # Basic info
    ticker_val = company_data["Ticker"].iloc[0]
    name = company_data["Name"].iloc[0]
    isin = company_data["ISIN"].iloc[0] if "ISIN" in company_data.columns else ""

    # Metrics
    total_dividends = company_data["Total"].sum()
    dividend_count = len(company_data)
    average_dividend = company_data["Total"].mean()
    min_dividend = company_data["Total"].min()
    max_dividend = company_data["Total"].max()

    # Dates
    first_date = company_data["Time"].min()
    last_date = company_data["Time"].max()
    last_amount = company_data.sort_values("Time").iloc[-1]["Total"]

    # Payment frequency
    unique_years = company_data["Year"].nunique()
    payments_per_year = dividend_count / unique_years if unique_years > 0 else 0
    cadence = determine_payment_cadence(payments_per_year)

    detail = StockDetail(
        ticker=to_python_type(ticker_val),
        name=to_python_type(name),
        isin=to_python_type(isin),
        total_dividends=to_python_type(total_dividends),
        dividend_count=to_python_type(dividend_count),
        average_dividend=to_python_type(average_dividend),
        min_dividend=to_python_type(min_dividend),
        max_dividend=to_python_type(max_dividend),
        first_dividend_date=to_python_type(first_date),
        last_dividend_date=to_python_type(last_date),
        last_dividend_amount=to_python_type(last_amount),
        payment_cadence=cadence,
        payments_per_year=to_python_type(payments_per_year)
    )

    # Yearly totals
    yearly = company_data.groupby("Year")["Total"].sum().reset_index()
    yearly_totals = [
        YearlyTotal(year=int(row["Year"]), total=to_python_type(row["Total"]))
        for _, row in yearly.iterrows()
    ]

    # Payment history - group by date (some stocks have multiple payments on the same day)
    company_data["Date"] = company_data["Time"].dt.date
    daily_payments = company_data.groupby("Date").agg({
        "Total": "sum",
        "No. of shares": "sum"
    }).reset_index()
    daily_payments = daily_payments.sort_values("Date", ascending=False)

    payment_history = [
        PaymentHistory(
            date=to_python_type(row["Date"]),
            amount=to_python_type(row["Total"]),
            shares=to_python_type(row["No. of shares"])
        )
        for _, row in daily_payments.iterrows()
    ]

    # Monthly growth
    company_data["YearMonth"] = company_data["Time"].dt.strftime("%Y-%m")
    company_data["MonthYear"] = company_data["Time"].dt.strftime("%b %Y")
    monthly_totals = company_data.groupby(["YearMonth", "MonthYear"])["Total"].sum().reset_index()
    monthly_totals = monthly_totals.sort_values("YearMonth")

    monthly_totals["Previous"] = monthly_totals["Total"].shift(1)
    monthly_totals["PercentChange"] = (
        (monthly_totals["Total"] - monthly_totals["Previous"]) / monthly_totals["Previous"] * 100
    ).fillna(0)

    monthly_growth = [
        MonthlyGrowth(
            month=row["MonthYear"],
            total=to_python_type(row["Total"]),
            percent_change=to_python_type(row["PercentChange"]) if not pd.isna(row["Previous"]) else None
        )
        for _, row in monthly_totals.iterrows()
    ]

    return StockAnalysisResponse(
        detail=detail,
        yearly_totals=yearly_totals,
        payment_history=payment_history,
        monthly_growth=monthly_growth
    )
