"""
Stock Analysis API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()


def get_data():
    from app.main import get_data as _get_data
    return _get_data()


@router.get("/list")
async def list_stocks(data: tuple = Depends(get_data)):
    """Get list of all stocks in portfolio."""
    return {"message": "Stocks list endpoint - to be implemented"}


@router.get("/{symbol}")
async def get_stock_details(symbol: str, data: tuple = Depends(get_data)):
    """Get details for a specific stock."""
    return {"message": f"Stock details for {symbol} - to be implemented"}
