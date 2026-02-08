"""
Calendar Models for Dividend Calendar Feature.

Provides Pydantic models for dividend events and calendar views.
"""

from pydantic import BaseModel, Field
from datetime import date as DateType
from typing import List, Optional


class DividendEvent(BaseModel):
    """Individual dividend event for calendar display."""

    date: DateType = Field(..., description="Date of dividend payment")
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Full company name")
    amount: float = Field(..., description="Dividend amount in GBP")
    expected: bool = Field(default=False, description="True if forecasted, False if actual payment")


class CalendarMonth(BaseModel):
    """Calendar data for a single month."""

    year: int = Field(..., description="Year of the month")
    month: int = Field(..., ge=1, le=12, description="Month number (1-12)")
    events: List[DividendEvent] = Field(default_factory=list, description="Dividend events in this month")
    total: float = Field(default=0.0, description="Total dividends for the month")


class UpcomingDividend(BaseModel):
    """Predicted upcoming dividend payment."""

    ticker: str
    company_name: str
    expected_date: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    estimated_amount: float
    confidence: str = Field(..., description="Confidence level: low, medium, high")


class CalendarExportRequest(BaseModel):
    """Request parameters for calendar export."""

    year: Optional[int] = Field(default=None, description="Year to export (default: current year)")
    months: int = Field(default=12, ge=1, le=24, description="Number of months to export")
    include_forecast: bool = Field(default=False, description="Include forecasted dividends")
