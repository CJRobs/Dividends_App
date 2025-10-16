"""
Forecast API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()


def get_data():
    from app.main import get_data as _get_data
    return _get_data()


@router.get("/predict")
async def get_forecast(months: int = 12, data: tuple = Depends(get_data)):
    """Generate dividend forecast."""
    return {"message": f"Forecast for {months} months - to be implemented"}
