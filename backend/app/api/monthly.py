"""
Monthly Analysis API endpoints.

Provides monthly dividend analysis and year-over-year comparisons.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import pandas as pd

router = APIRouter()


def get_data():
    """Dependency to get data from main app cache."""
    from app.main import get_data as _get_data
    return _get_data()


@router.get("/summary")
async def get_monthly_summary(year: int = None, data: tuple = Depends(get_data)):
    """Get monthly summary for a specific year."""
    df, monthly_data = data

    if df.empty:
        raise HTTPException(status_code=404, detail="No dividend data available")

    from datetime import datetime
    if year is None:
        year = datetime.now().year

    year_df = df[df["Year"] == year]

    monthly_summary = year_df.groupby("Month").agg({
        "Total": ["sum", "count", "mean"]
    }).reset_index()

    # TODO: Implement full monthly analysis logic
    return {"message": "Monthly summary endpoint - to be implemented", "year": year}


@router.get("/comparison")
async def get_year_comparison(data: tuple = Depends(get_data)):
    """Get year-over-year monthly comparison."""
    # TODO: Implement comparison logic
    return {"message": "Monthly comparison endpoint - to be implemented"}
