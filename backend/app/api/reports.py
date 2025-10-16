"""
PDF Reports API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends

router = APIRouter()


def get_data():
    from app.main import get_data as _get_data
    return _get_data()


@router.post("/generate")
async def generate_report(data: tuple = Depends(get_data)):
    """Generate PDF report."""
    return {"message": "PDF report generation - to be implemented"}
