"""
FastAPI Main Application for Dividend Portfolio Dashboard.

This is the entry point for the FastAPI backend that serves the
dividend portfolio data and analysis endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import pandas as pd
from typing import Optional

from app.config import get_settings
from app.services.data_processor import load_data, preprocess_data, get_monthly_data
from app.api import overview, monthly, stocks, screener, forecast, reports

# Global data cache
_data_cache: dict = {
    "df": None,
    "monthly_data": None,
    "last_loaded": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: Load data
    settings = get_settings()
    try:
        print(f"Loading data from: {settings.data_path}")
        df = load_data(settings.data_path)
        df = preprocess_data(df)
        monthly_data = get_monthly_data(df)

        _data_cache["df"] = df
        _data_cache["monthly_data"] = monthly_data

        print(f"✓ Data loaded successfully: {len(df)} records")
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        # Continue anyway - will return errors on API calls

    yield

    # Shutdown: Cleanup
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Dividend Portfolio Dashboard API",
    description="API for tracking, analyzing, and forecasting dividend income",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(overview.router, prefix="/api/overview", tags=["Overview"])
app.include_router(monthly.router, prefix="/api/monthly", tags=["Monthly Analysis"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stock Analysis"])
app.include_router(screener.router, prefix="/api/screener", tags=["Dividend Screener"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["Forecast"])
app.include_router(reports.router, prefix="/api/reports", tags=["PDF Reports"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Dividend Portfolio Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    data_loaded = _data_cache["df"] is not None
    record_count = len(_data_cache["df"]) if data_loaded else 0

    return {
        "status": "healthy" if data_loaded else "degraded",
        "data_loaded": data_loaded,
        "record_count": record_count,
        "settings": {
            "environment": settings.environment,
            "default_currency": settings.default_currency
        }
    }


def get_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get cached data.

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


@app.post("/api/reload-data", tags=["Admin"])
async def reload_data():
    """Reload data from source (admin endpoint)."""
    try:
        settings = get_settings()
        df = load_data(settings.data_path)
        df = preprocess_data(df)
        monthly_data = get_monthly_data(df)

        _data_cache["df"] = df
        _data_cache["monthly_data"] = monthly_data

        return {
            "status": "success",
            "message": f"Data reloaded successfully",
            "record_count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload data: {str(e)}")


# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
