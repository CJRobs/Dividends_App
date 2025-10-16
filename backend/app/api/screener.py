"""
Dividend Screener API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()


def get_data():
    from app.main import get_data as _get_data
    return _get_data()


@router.post("/search")
async def search_dividends(data: tuple = Depends(get_data)):
    """Search dividends with criteria."""
    return {"message": "Screener search endpoint - to be implemented"}
