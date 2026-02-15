"""
FastAPI Main Application for Dividend Portfolio Dashboard.

This is the entry point for the FastAPI backend that serves the
dividend portfolio data and analysis endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from contextlib import asynccontextmanager
import httpx
import pandas as pd
import time
import os
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.services.data_processor import load_data, preprocess_data, get_monthly_data, validate_dataframe
from app.api import overview, monthly, stocks, screener, forecast, reports, auth, calendar
from app.dependencies import set_data, get_data_status
from app.utils.cache import clear_cache
from app.utils.logging_config import setup_logging
from app.middleware.rate_limit import limiter
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.error_logging import ErrorLoggingMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Initialize logging at module level
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: Load data
    settings = get_settings()
    try:
        logger.info(f"Loading data from: {settings.data_path}")

        # Validate data path exists before loading
        data_file = Path(settings.data_path)

        if not data_file.exists():
            logger.error(f"Data file not found: {settings.data_path}")
            logger.warning("Application starting in degraded mode - API endpoints will return 503")
            yield
            return

        if not data_file.is_file():
            logger.error(f"Data path is not a file: {settings.data_path}")
            logger.warning("Application starting in degraded mode")
            yield
            return

        # Check file permissions
        if not os.access(data_file, os.R_OK):
            logger.error(f"Data file not readable (permission denied): {settings.data_path}")
            logger.warning("Application starting in degraded mode")
            yield
            return

        # Load and validate data
        df = load_data(settings.data_path)
        df = preprocess_data(df)

        # Validate schema
        required_columns = ["Time", "Ticker", "Name", "Total"]
        is_valid, error_msg = validate_dataframe(df, required_columns)
        if not is_valid:
            logger.error(f"Data validation failed: {error_msg}")
            logger.warning("Application starting in degraded mode")
            yield
            return

        monthly_data = get_monthly_data(df)
        set_data(df, monthly_data)

        logger.info(
            f"Data loaded successfully: {len(df)} records, "
            f"{len(df['Ticker'].unique())} unique tickers"
        )

        # Initialize Alpha Vantage disk cache (if enabled)
        if hasattr(settings, 'cache_enabled') and settings.cache_enabled:
            try:
                from app.services.alpha_vantage_cache import init_cache
                import app.services.alpha_vantage_cache as cache_module

                init_cache(settings)
                logger.info("Alpha Vantage disk cache initialized")

                # Warm cache from disk (if enabled)
                if hasattr(settings, 'cache_warm_on_startup') and settings.cache_warm_on_startup:
                    if cache_module.av_cache:
                        loaded = cache_module.av_cache.warm_cache_from_disk()
                        logger.info(f"Cache warmed: {loaded} entries loaded from disk")

            except Exception as e:
                logger.error(f"Failed to initialize Alpha Vantage cache: {e}", exc_info=True)
                logger.warning("Continuing without disk cache")

        # Initialize multi-provider orchestrator
        try:
            from app.services.providers import get_provider_chain
            from app.services.data_orchestrator import DataOrchestrator
            import app.services.data_orchestrator as orch_module

            provider_chain = get_provider_chain(settings)
            orch_module.orchestrator = DataOrchestrator(provider_chain)
            app.state.orchestrator = orch_module.orchestrator

            provider_names = [p.name for p in provider_chain]
            logger.info(f"Data orchestrator initialized with providers: {provider_names}")
        except Exception as e:
            logger.error(f"Failed to initialize data orchestrator: {e}", exc_info=True)
            logger.warning("Continuing without multi-provider fallback")

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.warning("Application starting in degraded mode - check DATA_PATH in .env")
    except PermissionError as e:
        logger.error(f"Permission denied reading data file: {e}")
        logger.warning("Application starting in degraded mode - check file permissions")
    except pd.errors.EmptyDataError as e:
        logger.error(f"Data file is empty: {e}")
        logger.warning("Application starting in degraded mode")
    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}", exc_info=True)
        logger.warning("Application starting in degraded mode")

    # Create shared httpx client for Alpha Vantage API calls (connection pooling)
    app.state.http_client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        headers={"Accept": "application/json"},
    )
    logger.info("Shared httpx client created")

    yield

    # Shutdown: Cleanup
    logger.info("Application shutting down")

    # Close shared httpx client
    await app.state.http_client.aclose()
    logger.info("Shared httpx client closed")

    # Save cache metadata (if enabled)
    if hasattr(settings, 'cache_enabled') and settings.cache_enabled:
        try:
            from app.services.alpha_vantage_cache import av_cache

            if av_cache:
                av_cache.save_metadata()
                logger.info("Cache metadata saved")
        except Exception as e:
            logger.warning(f"Error saving cache metadata: {e}")


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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods only
    allow_headers=["Authorization", "Content-Type", "Accept"],  # Explicit headers only
)

# Configure rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Add security headers
app.add_middleware(SecurityHeadersMiddleware)

# Add error logging (captures all unhandled exceptions)
app.add_middleware(ErrorLoggingMiddleware)


# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        logger.info(f"Request: {request.method} {request.url.path}")

        response = await call_next(request)

        duration = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"Status={response.status_code} Duration={duration:.3f}s"
        )

        return response


app.add_middleware(RequestLoggingMiddleware)


# Include routers
# Auth router (no prefix - already has /api/auth in router definition)
app.include_router(auth.router)
app.include_router(overview.router, prefix="/api/overview", tags=["Overview"])
app.include_router(monthly.router, prefix="/api/monthly", tags=["Monthly Analysis"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stock Analysis"])
app.include_router(screener.router, prefix="/api/screener", tags=["Dividend Screener"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["Forecast"])
app.include_router(reports.router, prefix="/api/reports", tags=["PDF Reports"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])


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
        logger.info("Manual data reload requested")

        # Validate file exists
        data_file = Path(settings.data_path)
        if not data_file.exists():
            logger.error(f"Data file not found during reload: {settings.data_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Data file not found: {settings.data_path}"
            )

        # Load and validate
        df = load_data(settings.data_path)
        df = preprocess_data(df)

        # Validate schema
        required_columns = ["Time", "Ticker", "Name", "Total"]
        is_valid, error_msg = validate_dataframe(df, required_columns)
        if not is_valid:
            logger.error(f"Data validation failed during reload: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        monthly_data = get_monthly_data(df)
        set_data(df, monthly_data)
        cache_cleared = clear_cache()

        logger.info(f"Data reloaded successfully: {len(df)} records")

        return {
            "status": "success",
            "message": "Data reloaded successfully",
            "record_count": len(df),
            "unique_tickers": len(df['Ticker'].unique()),
            "date_range": {
                "start": df['Time'].min().isoformat(),
                "end": df['Time'].max().isoformat()
            },
            "cache_entries_cleared": cache_cleared
        }
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"File not found during reload: {e}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except pd.errors.EmptyDataError:
        logger.error("Empty data file during reload")
        raise HTTPException(status_code=400, detail="Data file is empty")
    except Exception as e:
        logger.error(f"Failed to reload data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reload data: {str(e)}")


# Custom exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded. Please try again later.",
            "status_code": 429,
            "detail": "Too many requests"
        }
    )


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
