"""
Shared dependencies for FastAPI routes.

This module centralizes data access and avoids circular imports
between routers and main.py.
"""

from typing import Tuple, Optional
import pandas as pd
from fastapi import HTTPException
from datetime import datetime


# Global data cache - set by main.py during startup
_data_cache: dict = {
    "df": None,
    "monthly_data": None,
    "last_loaded": None
}


def set_data(df: pd.DataFrame, monthly_data: pd.DataFrame) -> None:
    """
    Set cached data. Called by main.py during startup and reload.

    Args:
        df: Main dividend DataFrame
        monthly_data: Pre-aggregated monthly data
    """
    _data_cache["df"] = df
    _data_cache["monthly_data"] = monthly_data
    _data_cache["last_loaded"] = datetime.now()


def get_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get cached data for use in route handlers.

    Returns:
        Tuple of (main_df, monthly_data)

    Raises:
        HTTPException: If data is not loaded
    """
    if _data_cache["df"] is None:
        raise HTTPException(
            status_code=503,
            detail="Data not loaded. Check server logs for details."
        )

    return _data_cache["df"], _data_cache["monthly_data"]


def get_data_status() -> dict:
    """
    Get information about the cached data.

    Returns:
        Dictionary with data status information
    """
    df = _data_cache["df"]
    return {
        "loaded": df is not None,
        "record_count": len(df) if df is not None else 0,
        "last_loaded": _data_cache["last_loaded"].isoformat() if _data_cache["last_loaded"] else None
    }
