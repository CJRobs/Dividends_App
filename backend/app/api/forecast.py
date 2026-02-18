"""
Forecast API endpoints.

Provides dividend forecasting using multiple models:
- SARIMAX
- Holt-Winters (Exponential Smoothing)
- Simple Moving Average (as fallback)
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.dependencies import get_data
from app.models.portfolio import FICalculatorResponse
from app.utils import cached_response
from app.utils.logging_config import get_logger

logger = get_logger()
warnings.filterwarnings('ignore')

router = APIRouter()

# Thread pool for parallel forecast execution
_forecast_executor = ThreadPoolExecutor(max_workers=4)

# Try to import forecasting libraries
STATSMODELS_AVAILABLE = False
PROPHET_AVAILABLE = False
SKTIME_AVAILABLE = False

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    STATSMODELS_AVAILABLE = True
except ImportError:
    pass

try:
    from prophet import Prophet
    import logging
    logging.getLogger("prophet").setLevel(logging.WARNING)
    logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
    PROPHET_AVAILABLE = True
except ImportError:
    pass

try:
    from sktime.forecasting.theta import ThetaForecaster
    SKTIME_AVAILABLE = True
except ImportError:
    pass


class ForecastPoint(BaseModel):
    """Single forecast data point."""
    date: str
    predicted: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class ForecastResult(BaseModel):
    """Forecast result from a model."""
    model_name: str
    forecast: List[ForecastPoint]
    historical: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    total_projected: float
    monthly_average: float
    annual_projections: List[Dict[str, Any]]


class ForecastResponse(BaseModel):
    """Complete forecast response."""
    sarimax: Optional[ForecastResult] = None
    holt_winters: Optional[ForecastResult] = None
    prophet: Optional[ForecastResult] = None
    theta: Optional[ForecastResult] = None
    simple_average: Optional[ForecastResult] = None
    ensemble: Optional[ForecastResult] = None
    available_models: List[str]
    current_month_tracking: Optional[Dict[str, Any]] = None  # Current incomplete month for tracking




def prepare_monthly_series(df: pd.DataFrame, exclude_current_month: bool = True) -> tuple[pd.Series, dict]:
    """
    Prepare monthly time series from dividend data.

    Args:
        df: DataFrame with dividend data
        exclude_current_month: If True, excludes the current incomplete month from training

    Returns:
        Tuple of (training_series, current_month_data)
        current_month_data contains the current month's partial data for tracking
    """
    df_copy = df.copy()
    df_copy['YearMonth'] = df_copy['Time'].dt.to_period('M')
    monthly = df_copy.groupby('YearMonth')['Total'].sum()

    # Create complete date range
    if len(monthly) > 0:
        date_range = pd.period_range(
            start=monthly.index.min(),
            end=monthly.index.max(),
            freq='M'
        )
        monthly = monthly.reindex(date_range, fill_value=0)

    # Get current month info
    current_period = pd.Period(datetime.now(), freq='M')
    current_month_data = None

    if exclude_current_month and len(monthly) > 0:
        # Check if the last month in data is the current month
        if monthly.index[-1] == current_period:
            # Extract current month data for tracking display
            current_month_data = {
                "date": str(current_period),
                "value": float(monthly.iloc[-1]),
                "is_partial": True
            }
            # Remove current month from training data
            monthly = monthly.iloc[:-1]

    return monthly, current_month_data


def forecast_sarimax(series: pd.Series, months: int) -> Optional[ForecastResult]:
    """Generate SARIMAX forecast."""
    if not STATSMODELS_AVAILABLE or len(series) < 12:
        return None

    try:
        # SARIMAX with differencing to match original Streamlit implementation
        model = SARIMAX(
            series.values,
            order=(1, 1, 0),  # Fixed: was (1,0,1), original uses (1,1,0)
            seasonal_order=(1, 1, 0, 12),  # Fixed: was (1,0,1,12), original uses (1,1,0,12)
            enforce_stationarity=True,
            enforce_invertibility=True
        )
        results = model.fit(disp=False, maxiter=100)

        # Generate forecast
        forecast = results.get_forecast(steps=months)
        pred = forecast.predicted_mean
        conf = forecast.conf_int(alpha=0.05)

        # Build forecast points
        last_date = series.index[-1]
        forecast_points = []
        for i in range(months):
            future_date = last_date + i + 1
            forecast_points.append(ForecastPoint(
                date=str(future_date),
                predicted=max(0, float(pred[i])),
                lower_bound=max(0, float(conf[i, 0])),
                upper_bound=float(conf[i, 1])
            ))

        # Historical data
        historical = [
            {"date": str(date), "value": float(val)}
            for date, val in series.items()
        ]

        # Calculate metrics
        total_projected = sum(max(0, p) for p in pred)
        monthly_avg = total_projected / months

        # Annual projections
        annual_projections = []
        for year in range(1, (months // 12) + 2):
            start_idx = (year - 1) * 12
            end_idx = min(year * 12, months)
            if start_idx < months:
                year_total = sum(max(0, pred[i]) for i in range(start_idx, end_idx))
                annual_projections.append({
                    "year": f"Year {year}",
                    "projected": year_total
                })

        return ForecastResult(
            model_name="SARIMAX",
            forecast=forecast_points,
            historical=historical,
            metrics={"aic": float(results.aic) if hasattr(results, 'aic') else None},
            total_projected=total_projected,
            monthly_average=monthly_avg,
            annual_projections=annual_projections
        )
    except Exception as e:
        logger.warning(f"SARIMAX forecast failed: {e}")
        return None


def forecast_holt_winters(series: pd.Series, months: int) -> Optional[ForecastResult]:
    """Generate Holt-Winters forecast."""
    if not STATSMODELS_AVAILABLE or len(series) < 24:
        return None

    try:
        # Ensure positive values for multiplicative model
        series_adj = series + 0.01

        model = ExponentialSmoothing(
            series_adj.values,
            seasonal_periods=12,
            trend='add',
            seasonal='mul',  # Fixed: was 'add', original uses 'mul' (multiplicative)
            damped_trend=False  # Fixed: was True, original uses False
        )
        results = model.fit(optimized=True)

        # Generate forecast
        pred = results.forecast(months)

        # Build forecast points (no confidence interval for HW)
        last_date = series.index[-1]
        forecast_points = []
        for i in range(months):
            future_date = last_date + i + 1
            forecast_points.append(ForecastPoint(
                date=str(future_date),
                predicted=max(0, float(pred[i])),
            ))

        # Historical data
        historical = [
            {"date": str(date), "value": float(val)}
            for date, val in series.items()
        ]

        # Calculate metrics
        total_projected = sum(max(0, p) for p in pred)
        monthly_avg = total_projected / months

        # Annual projections
        annual_projections = []
        for year in range(1, (months // 12) + 2):
            start_idx = (year - 1) * 12
            end_idx = min(year * 12, months)
            if start_idx < months:
                year_total = sum(max(0, pred[i]) for i in range(start_idx, end_idx))
                annual_projections.append({
                    "year": f"Year {year}",
                    "projected": year_total
                })

        return ForecastResult(
            model_name="Holt-Winters",
            forecast=forecast_points,
            historical=historical,
            metrics={},
            total_projected=total_projected,
            monthly_average=monthly_avg,
            annual_projections=annual_projections
        )
    except Exception as e:
        logger.warning(f"Holt-Winters forecast failed: {e}")
        return None


def forecast_simple_average(series: pd.Series, months: int) -> ForecastResult:
    """Generate simple moving average forecast."""
    # Use last 12 months average
    lookback = min(12, len(series))
    avg = series.tail(lookback).mean()

    # Apply simple growth trend
    growth_rate = 0.02  # 2% monthly growth assumption
    last_date = series.index[-1]

    forecast_points = []
    for i in range(months):
        future_date = last_date + i + 1
        predicted = avg * ((1 + growth_rate) ** (i + 1))
        forecast_points.append(ForecastPoint(
            date=str(future_date),
            predicted=max(0, float(predicted)),
        ))

    # Historical data
    historical = [
        {"date": str(date), "value": float(val)}
        for date, val in series.items()
    ]

    # Calculate metrics
    total_projected = sum(fp.predicted for fp in forecast_points)
    monthly_avg = total_projected / months

    # Annual projections
    annual_projections = []
    for year in range(1, (months // 12) + 2):
        start_idx = (year - 1) * 12
        end_idx = min(year * 12, months)
        if start_idx < months:
            year_total = sum(forecast_points[i].predicted for i in range(start_idx, end_idx))
            annual_projections.append({
                "year": f"Year {year}",
                "projected": year_total
            })

    return ForecastResult(
        model_name="Simple Average",
        forecast=forecast_points,
        historical=historical,
        metrics={"lookback_months": lookback, "growth_rate": growth_rate},
        total_projected=total_projected,
        monthly_average=monthly_avg,
        annual_projections=annual_projections
    )


def forecast_prophet(series: pd.Series, months: int) -> Optional[ForecastResult]:
    """Generate Prophet forecast."""
    if not PROPHET_AVAILABLE or len(series) < 12:
        return None

    try:
        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        prophet_data = pd.DataFrame({
            'ds': series.index.to_timestamp(),
            'y': series.values
        })

        # Initialize Prophet with yearly seasonality only
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode='additive'
        )
        model.fit(prophet_data)

        # Create future dataframe
        future = model.make_future_dataframe(periods=months, freq='ME')
        forecast = model.predict(future)

        # Extract forecast portion (last 'months' rows)
        forecast_portion = forecast.tail(months)

        # Build forecast points
        last_date = series.index[-1]
        forecast_points = []
        for i, (_, row) in enumerate(forecast_portion.iterrows()):
            future_date = last_date + i + 1
            forecast_points.append(ForecastPoint(
                date=str(future_date),
                predicted=max(0, float(row['yhat'])),
                lower_bound=max(0, float(row['yhat_lower'])),
                upper_bound=float(row['yhat_upper'])
            ))

        # Historical data
        historical = [
            {"date": str(date), "value": float(val)}
            for date, val in series.items()
        ]

        # Calculate metrics
        total_projected = sum(fp.predicted for fp in forecast_points)
        monthly_avg = total_projected / months

        # Annual projections
        annual_projections = []
        for year in range(1, (months // 12) + 2):
            start_idx = (year - 1) * 12
            end_idx = min(year * 12, months)
            if start_idx < months:
                year_total = sum(forecast_points[i].predicted for i in range(start_idx, end_idx))
                annual_projections.append({
                    "year": f"Year {year}",
                    "projected": year_total
                })

        return ForecastResult(
            model_name="Prophet",
            forecast=forecast_points,
            historical=historical,
            metrics={"seasonality_mode": "additive"},
            total_projected=total_projected,
            monthly_average=monthly_avg,
            annual_projections=annual_projections
        )
    except Exception as e:
        logger.warning(f"Prophet forecast failed: {e}")
        return None


def forecast_theta(series: pd.Series, months: int) -> Optional[ForecastResult]:
    """Generate Theta Forecaster prediction using sktime."""
    if not SKTIME_AVAILABLE or len(series) < 6:
        return None

    try:
        # Prepare data for sktime (needs numeric index)
        ts_data = pd.Series(series.values, index=range(len(series)))

        # Initialize Theta forecaster with seasonal period
        forecaster = ThetaForecaster(sp=12)
        forecaster.fit(ts_data)

        # Generate forecast
        fh = list(range(1, months + 1))
        forecast_values = forecaster.predict(fh)

        # Try to get prediction intervals
        try:
            pred_ints = forecaster.predict_interval(fh, coverage=0.95)
            if len(pred_ints.columns) >= 2:
                lower_ci = pred_ints.iloc[:, 0].values
                upper_ci = pred_ints.iloc[:, 1].values
            else:
                raise ValueError("Insufficient interval columns")
        except Exception:
            # Fallback: use historical volatility for confidence bounds
            historical_std = series.std()
            lower_ci = forecast_values.values - 1.96 * historical_std
            upper_ci = forecast_values.values + 1.96 * historical_std

        # Build forecast points
        last_date = series.index[-1]
        forecast_points = []
        for i in range(months):
            future_date = last_date + i + 1
            forecast_points.append(ForecastPoint(
                date=str(future_date),
                predicted=max(0, float(forecast_values.iloc[i])),
                lower_bound=max(0, float(lower_ci[i])),
                upper_bound=float(upper_ci[i])
            ))

        # Historical data
        historical = [
            {"date": str(date), "value": float(val)}
            for date, val in series.items()
        ]

        # Calculate metrics
        total_projected = sum(fp.predicted for fp in forecast_points)
        monthly_avg = total_projected / months

        # Annual projections
        annual_projections = []
        for year in range(1, (months // 12) + 2):
            start_idx = (year - 1) * 12
            end_idx = min(year * 12, months)
            if start_idx < months:
                year_total = sum(forecast_points[i].predicted for i in range(start_idx, end_idx))
                annual_projections.append({
                    "year": f"Year {year}",
                    "projected": year_total
                })

        return ForecastResult(
            model_name="Theta",
            forecast=forecast_points,
            historical=historical,
            metrics={"seasonal_period": 12},
            total_projected=total_projected,
            monthly_average=monthly_avg,
            annual_projections=annual_projections
        )
    except Exception as e:
        logger.warning(f"Theta forecast failed: {e}")
        return None


def create_ensemble(forecasts: List[ForecastResult], series: pd.Series, months: int) -> ForecastResult:
    """Create ensemble forecast by averaging available models."""
    if not forecasts:
        return forecast_simple_average(series, months)

    # Average predictions
    ensemble_points = []
    last_date = series.index[-1]

    for i in range(months):
        predictions = [f.forecast[i].predicted for f in forecasts if i < len(f.forecast)]
        avg_pred = np.mean(predictions) if predictions else 0

        # Average bounds if available
        lower_bounds = [f.forecast[i].lower_bound for f in forecasts
                       if i < len(f.forecast) and f.forecast[i].lower_bound is not None]
        upper_bounds = [f.forecast[i].upper_bound for f in forecasts
                       if i < len(f.forecast) and f.forecast[i].upper_bound is not None]

        future_date = last_date + i + 1
        ensemble_points.append(ForecastPoint(
            date=str(future_date),
            predicted=max(0, float(avg_pred)),
            lower_bound=max(0, float(np.mean(lower_bounds))) if lower_bounds else None,
            upper_bound=float(np.mean(upper_bounds)) if upper_bounds else None
        ))

    # Historical data
    historical = [
        {"date": str(date), "value": float(val)}
        for date, val in series.items()
    ]

    # Calculate metrics
    total_projected = sum(fp.predicted for fp in ensemble_points)
    monthly_avg = total_projected / months

    # Annual projections
    annual_projections = []
    for year in range(1, (months // 12) + 2):
        start_idx = (year - 1) * 12
        end_idx = min(year * 12, months)
        if start_idx < months:
            year_total = sum(ensemble_points[i].predicted for i in range(start_idx, end_idx))
            annual_projections.append({
                "year": f"Year {year}",
                "projected": year_total
            })

    return ForecastResult(
        model_name="Ensemble",
        forecast=ensemble_points,
        historical=historical,
        metrics={"models_used": [f.model_name for f in forecasts]},
        total_projected=total_projected,
        monthly_average=monthly_avg,
        annual_projections=annual_projections
    )


@router.get("/", response_model=ForecastResponse)
@cached_response(ttl_minutes=10)
async def get_all_forecasts(
    request: Request,
    months: int = Query(default=12, ge=1, le=36, description="Forecast horizon in months"),
    lookback: int = Query(default=0, ge=0, le=120, description="Lookback months for training (0 = use all data)"),
    data: tuple = Depends(get_data)
):
    """
    Get forecasts from all available models (executed in parallel).

    Args:
        months: Forecast horizon in months (1-36)
        lookback: Training data lookback period in months (0 = use all available data, 6-120 = limit training window)

    Note: The current incomplete month is excluded from training but returned as
    'current_month_tracking' for display purposes.
    """
    df, _ = data

    if df.empty:
        raise HTTPException(status_code=404, detail="No dividend data available")

    # Prepare monthly time series (excludes current incomplete month)
    series, current_month_data = prepare_monthly_series(df, exclude_current_month=True)

    # Apply lookback period if specified
    if lookback > 0 and len(series) > lookback:
        series = series.tail(lookback)

    if len(series) < 6:
        raise HTTPException(status_code=400, detail="Not enough data for forecasting (need at least 6 months)")

    # Run forecast models in parallel using thread pool
    loop = asyncio.get_event_loop()

    # Submit all forecasting tasks to thread pool
    sarimax_future = loop.run_in_executor(_forecast_executor, forecast_sarimax, series, months)
    hw_future = loop.run_in_executor(_forecast_executor, forecast_holt_winters, series, months)
    prophet_future = loop.run_in_executor(_forecast_executor, forecast_prophet, series, months)
    theta_future = loop.run_in_executor(_forecast_executor, forecast_theta, series, months)

    # Wait for all forecasts to complete in parallel
    sarimax_result, hw_result, prophet_result, theta_result = await asyncio.gather(
        sarimax_future, hw_future, prophet_future, theta_future
    )

    # Simple average runs quickly, no need for thread pool
    simple_result = forecast_simple_average(series, months)

    # Build available models list and forecasts for ensemble
    available_models = ["Simple Average"]
    forecasts = [simple_result]

    if sarimax_result:
        available_models.append("SARIMAX")
        forecasts.append(sarimax_result)

    if hw_result:
        available_models.append("Holt-Winters")
        forecasts.append(hw_result)

    if prophet_result:
        available_models.append("Prophet")
        forecasts.append(prophet_result)

    if theta_result:
        available_models.append("Theta")
        forecasts.append(theta_result)

    # Ensemble (average of all available models)
    ensemble_result = create_ensemble(forecasts, series, months)
    available_models.append("Ensemble")

    return ForecastResponse(
        sarimax=sarimax_result,
        holt_winters=hw_result,
        prophet=prophet_result,
        theta=theta_result,
        simple_average=simple_result,
        ensemble=ensemble_result,
        available_models=available_models,
        current_month_tracking=current_month_data
    )


@router.get("/sarimax", response_model=Optional[ForecastResult])
async def get_sarimax_forecast(
    months: int = Query(default=12, ge=1, le=36),
    data: tuple = Depends(get_data)
):
    """Get SARIMAX forecast."""
    df, _ = data
    series, _ = prepare_monthly_series(df)
    result = forecast_sarimax(series, months)
    if not result:
        raise HTTPException(status_code=400, detail="SARIMAX model not available (need statsmodels and 12+ months of data)")
    return result


@router.get("/holt-winters", response_model=Optional[ForecastResult])
async def get_holt_winters_forecast(
    months: int = Query(default=12, ge=1, le=36),
    data: tuple = Depends(get_data)
):
    """Get Holt-Winters forecast."""
    df, _ = data
    series, _ = prepare_monthly_series(df)
    result = forecast_holt_winters(series, months)
    if not result:
        raise HTTPException(status_code=400, detail="Holt-Winters model not available (need statsmodels and 24+ months of data)")
    return result


@router.get("/simple", response_model=ForecastResult)
async def get_simple_forecast(
    months: int = Query(default=12, ge=1, le=36),
    data: tuple = Depends(get_data)
):
    """Get simple moving average forecast."""
    df, _ = data
    series, _ = prepare_monthly_series(df)
    return forecast_simple_average(series, months)


@router.get("/ensemble", response_model=ForecastResult)
async def get_ensemble_forecast(
    months: int = Query(default=12, ge=1, le=36),
    data: tuple = Depends(get_data)
):
    """Get ensemble forecast (average of all available models)."""
    df, _ = data
    series, _ = prepare_monthly_series(df)

    forecasts = []
    sarimax = forecast_sarimax(series, months)
    if sarimax:
        forecasts.append(sarimax)

    hw = forecast_holt_winters(series, months)
    if hw:
        forecasts.append(hw)

    forecasts.append(forecast_simple_average(series, months))

    return create_ensemble(forecasts, series, months)


@router.get("/predict")
async def get_forecast(
    months: int = Query(default=12, ge=1, le=36),
    data: tuple = Depends(get_data)
):
    """Legacy endpoint - redirects to ensemble forecast."""
    return await get_ensemble_forecast(months=months, data=data)


@router.get("/fi-calculator", response_model=FICalculatorResponse)
@cached_response(ttl_minutes=5)
async def calculate_fi_goal(
    monthly_goal: float = Query(..., description="Monthly dividend income goal"),
    data: tuple = Depends(get_data)
):
    """
    Calculate years to reach financial independence goal.
    """
    df, _ = data
    series, _ = prepare_monthly_series(df, exclude_current_month=False)  # Include current month for FI calc

    if len(series) < 6:
        raise HTTPException(status_code=400, detail="Not enough data")

    # Current monthly average (last 12 months)
    current_avg = series.tail(12).mean()

    # Calculate historical growth rate
    if len(series) >= 24:
        old_avg = series.iloc[:12].mean()
        new_avg = series.iloc[-12:].mean()
        if old_avg > 0:
            annual_growth = (new_avg / old_avg) ** (12 / len(series)) - 1
        else:
            annual_growth = 0.1  # Default 10% growth
    else:
        annual_growth = 0.1

    # Calculate years to goal
    if current_avg >= monthly_goal:
        years_to_goal = 0
    elif annual_growth <= 0:
        years_to_goal = float('inf')
    else:
        # Compound growth formula: goal = current * (1 + rate)^years
        years_to_goal = np.log(monthly_goal / current_avg) / np.log(1 + annual_growth)

    return FICalculatorResponse(
        monthly_goal=monthly_goal,
        current_monthly_avg=float(current_avg),
        annual_growth_rate=float(annual_growth) * 100,
        years_to_goal=float(years_to_goal) if years_to_goal != float('inf') else None,
        goal_reached=bool(current_avg >= monthly_goal)
    )
