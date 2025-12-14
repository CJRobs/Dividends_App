"""
Monthly Analysis API endpoints.

Provides monthly dividend analysis, heatmaps, and company breakdowns.
"""

from fastapi import APIRouter, Depends, Query
from datetime import datetime
from typing import List, Optional
import pandas as pd
import numpy as np

from app.models.monthly import (
    MonthlyByYearData,
    HeatmapData,
    HeatmapCell,
    MonthlyByCompanyResponse,
    CompanyMonthlyData,
    CoverageData,
    MonthlyAnalysisResponse,
)
from app.config import MONTH_NAMES, MONTH_ORDER
from app.dependencies import get_data
from app.utils import to_python_type, cached_response

router = APIRouter()


@router.get("/by-year", response_model=MonthlyByYearData)
@cached_response(ttl_minutes=5)
async def get_monthly_by_year(data: tuple = Depends(get_data)):
    """
    Get monthly dividend totals organized by year.

    Returns data suitable for multi-line chart comparing years.
    """
    df, monthly_data = data

    # Pivot table: months as rows, years as columns
    monthly_by_year = df.pivot_table(
        index="MonthName",
        columns="Year",
        values="Total",
        aggfunc="sum"
    ).reset_index()

    # Sort by proper month order
    monthly_by_year["MonthNum"] = monthly_by_year["MonthName"].apply(
        lambda x: MONTH_ORDER.index(x) if x in MONTH_ORDER else 12
    )
    monthly_by_year = monthly_by_year.sort_values("MonthNum")

    # Build response
    months = monthly_by_year["MonthName"].tolist()
    years_data = {}

    year_columns = [col for col in monthly_by_year.columns if isinstance(col, (int, np.integer))]
    for year in sorted(year_columns):
        values = monthly_by_year[year].tolist()
        years_data[str(year)] = [to_python_type(v) for v in values]

    return MonthlyByYearData(months=months, years=years_data)


@router.get("/heatmap", response_model=HeatmapData)
@cached_response(ttl_minutes=5)
async def get_monthly_heatmap(data: tuple = Depends(get_data)):
    """
    Get monthly dividend heatmap data.

    Returns year x month matrix with dividend amounts.
    """
    df, monthly_data = data

    # Pivot table: years as rows, months as columns
    monthly_pivot = df.pivot_table(
        index="Year",
        columns="MonthName",
        values="Total",
        aggfunc="sum"
    ).fillna(0)

    # Ensure all months are present
    for month in MONTH_ORDER:
        if month not in monthly_pivot.columns:
            monthly_pivot[month] = 0

    # Reorder columns by month order
    monthly_pivot = monthly_pivot[MONTH_ORDER]

    # Build response
    rows = [str(year) for year in sorted(monthly_pivot.index)]
    cols = MONTH_ORDER.copy()

    cells = []
    for year in monthly_pivot.index:
        for month in MONTH_ORDER:
            value = monthly_pivot.loc[year, month]
            cells.append(HeatmapCell(
                row=str(year),
                col=month,
                value=to_python_type(value)
            ))

    return HeatmapData(rows=rows, cols=cols, data=cells)


@router.get("/by-company", response_model=MonthlyByCompanyResponse)
async def get_monthly_by_company(
    companies: Optional[List[str]] = Query(None, description="Filter by company names"),
    month: Optional[str] = Query(None, description="Filter by specific month name"),
    data: tuple = Depends(get_data)
):
    """
    Get monthly dividends broken down by company.

    Returns stacked bar chart data.
    If month is provided, shows that month across all years.
    Otherwise shows all months.
    """
    df, monthly_data = data

    filtered_df = df.copy()

    # Apply company filter
    if companies:
        filtered_df = filtered_df[filtered_df["Name"].isin(companies)]

    # Apply month filter
    if month and month != "All Months":
        filtered_df = filtered_df[filtered_df["MonthName"] == month]

    result_data = []
    unique_companies = set()
    unique_periods = set()

    if month and month != "All Months":
        # Group by year and company for specific month
        grouped = filtered_df.groupby(["Year", "Name"])["Total"].sum().reset_index()
        grouped = grouped.sort_values("Year")

        for _, row in grouped.iterrows():
            period = str(int(row["Year"]))
            company = row["Name"]
            amount = to_python_type(row["Total"])

            result_data.append(CompanyMonthlyData(
                period=period,
                company=company,
                amount=amount
            ))
            unique_companies.add(company)
            unique_periods.add(period)
    else:
        # Group by month and company
        grouped = filtered_df.groupby(["MonthName", "Month", "Name"])["Total"].sum().reset_index()

        # Sort by month order
        grouped["MonthNum"] = grouped["MonthName"].apply(
            lambda x: MONTH_ORDER.index(x) if x in MONTH_ORDER else 12
        )
        grouped = grouped.sort_values("MonthNum")

        for _, row in grouped.iterrows():
            period = row["MonthName"]
            company = row["Name"]
            amount = to_python_type(row["Total"])

            result_data.append(CompanyMonthlyData(
                period=period,
                company=company,
                amount=amount
            ))
            unique_companies.add(company)
            unique_periods.add(period)

    # Sort periods (either by month order or year)
    if month and month != "All Months":
        sorted_periods = sorted(unique_periods)
    else:
        sorted_periods = sorted(
            unique_periods,
            key=lambda x: MONTH_ORDER.index(x) if x in MONTH_ORDER else 12
        )

    return MonthlyByCompanyResponse(
        data=result_data,
        companies=sorted(list(unique_companies)),
        periods=list(sorted_periods)
    )


@router.get("/coverage", response_model=CoverageData)
async def get_coverage_analysis(
    monthly_expenses: float = Query(2000.0, description="Monthly expenses amount"),
    data: tuple = Depends(get_data)
):
    """
    Calculate monthly expense coverage analysis.

    Returns coverage percentage and gap analysis based on most recent month.
    """
    df, monthly_data = data

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Get most recent complete month data
    recent_months = monthly_data[
        (monthly_data["Time"].dt.year < current_year) |
        (
            (monthly_data["Time"].dt.year == current_year) &
            (monthly_data["Time"].dt.month < current_month)
        )
    ]

    if not recent_months.empty:
        most_recent = recent_months.iloc[-1]
        amount_received = to_python_type(most_recent["Total_Sum"])
        month_name = most_recent["Time"].strftime("%B %Y")
    else:
        amount_received = 0.0
        month_name = "No data"

    # Calculate coverage
    coverage_percent = (amount_received / monthly_expenses * 100) if monthly_expenses > 0 else 0
    coverage_percent = min(coverage_percent, 100)  # Cap at 100%

    # Gap to full coverage
    gap_amount = max(0, monthly_expenses - amount_received)

    # Calculate monthly average
    monthly_average = to_python_type(monthly_data["Total_Sum"].mean()) if not monthly_data.empty else 0.0

    return CoverageData(
        month_name=month_name,
        amount_received=amount_received,
        coverage_percent=coverage_percent,
        gap_amount=gap_amount,
        monthly_average=monthly_average
    )


@router.get("/", response_model=MonthlyAnalysisResponse)
async def get_monthly_analysis(data: tuple = Depends(get_data)):
    """
    Get complete monthly analysis data in a single request.

    Combines by-year data, heatmap, and metadata.
    """
    df, monthly_data = data

    # Get by-year data
    by_year_response = await get_monthly_by_year(data)

    # Get heatmap data
    heatmap_response = await get_monthly_heatmap(data)

    # Get unique companies and months
    companies = sorted(df["Name"].unique().tolist())
    months = MONTH_ORDER.copy()
    # Filter out NaN values before converting to int
    years = sorted([int(y) for y in df["Year"].dropna().unique().tolist()])

    return MonthlyAnalysisResponse(
        by_year=by_year_response,
        heatmap=heatmap_response,
        companies=companies,
        months=months,
        years=years
    )
