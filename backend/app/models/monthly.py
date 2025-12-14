"""
Pydantic models for monthly analysis data.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class MonthlyByYearData(BaseModel):
    """Monthly data organized by year for line chart."""

    months: List[str] = Field(..., description="List of month names")
    years: Dict[str, List[Optional[float]]] = Field(
        ...,
        description="Year keys with list of monthly values"
    )


class HeatmapCell(BaseModel):
    """Single cell in heatmap."""

    row: str = Field(..., description="Row label (year)")
    col: str = Field(..., description="Column label (month)")
    value: float = Field(..., description="Dividend amount")


class HeatmapData(BaseModel):
    """Heatmap matrix data."""

    rows: List[str] = Field(..., description="Row labels (years)")
    cols: List[str] = Field(..., description="Column labels (months)")
    data: List[HeatmapCell] = Field(..., description="Cell data")


class CompanyMonthlyData(BaseModel):
    """Company data for stacked bar chart."""

    period: str = Field(..., description="Period label (month or year)")
    company: str = Field(..., description="Company name")
    amount: float = Field(..., description="Dividend amount")


class MonthlyByCompanyResponse(BaseModel):
    """Response for company breakdown chart."""

    data: List[CompanyMonthlyData]
    companies: List[str] = Field(..., description="List of unique companies")
    periods: List[str] = Field(..., description="List of unique periods")


class CoverageData(BaseModel):
    """Expense coverage analysis data."""

    month_name: str = Field(..., description="Most recent month name")
    amount_received: float = Field(..., description="Dividend amount received")
    coverage_percent: float = Field(..., description="Percentage of expenses covered")
    gap_amount: float = Field(..., description="Gap to 100% coverage")
    monthly_average: float = Field(..., description="Average monthly dividend")


class MonthlyAnalysisResponse(BaseModel):
    """Complete monthly analysis response."""

    by_year: MonthlyByYearData
    heatmap: HeatmapData
    companies: List[str]
    months: List[str]
    years: List[int]
