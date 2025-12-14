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
from app.dependencies import set_data, get_data_status
from app.utils.cache import clear_cache


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

        # Store in shared dependencies module
        set_data(df, monthly_data)

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
    data_status = get_data_status()

    return {
        "status": "healthy" if data_status["loaded"] else "degraded",
        "data_loaded": data_status["loaded"],
        "record_count": data_status["record_count"],
        "last_loaded": data_status["last_loaded"],
        "settings": {
            "environment": settings.environment,
            "default_currency": settings.default_currency
        }
    }


@app.post("/api/reload-data", tags=["Admin"])
async def reload_data():
    """Reload data from source and clear cache (admin endpoint)."""
    try:
        settings = get_settings()
        df = load_data(settings.data_path)
        df = preprocess_data(df)
        monthly_data = get_monthly_data(df)

        # Update shared data and clear response cache
        set_data(df, monthly_data)
        cache_cleared = clear_cache()

        return {
            "status": "success",
            "message": "Data reloaded successfully",
            "record_count": len(df),
            "cache_entries_cleared": cache_cleared
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
