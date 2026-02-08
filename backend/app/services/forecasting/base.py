"""
Base forecast model class.

Abstract base class that eliminates code duplication across forecast models
by providing common functionality for data preparation, metrics calculation,
and result formatting.
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime


class ForecastModel(ABC):
    """Abstract base class for all forecast models."""

    name: str = "Base Model"
    requires_library: str = None

    @abstractmethod
    def fit_predict(
        self,
        series: pd.Series,
        periods: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Fit model and generate predictions.

        Args:
            series: Historical time series data
            periods: Number of periods to forecast

        Returns:
            Tuple of (predictions, lower_bounds, upper_bounds)
        """
        pass

    def generate_forecast(
        self,
        series: pd.Series,
        months: int
    ) -> Dict[str, Any]:
        """
        Common forecast generation logic (eliminates duplication).

        Args:
            series: Historical time series data
            months: Number of months to forecast

        Returns:
            Dictionary with forecast results
        """
        # Fit and predict
        predictions, lower, upper = self.fit_predict(series, months)

        # Prepare historical data
        historical = self._prepare_historical(series)

        # Calculate metrics
        metrics = self._calculate_metrics(series, predictions[:len(series)])

        # Calculate annual projections
        annual_projections = self._calculate_annual_projections(predictions)

        # Format forecast output
        forecast_data = self._format_forecast(predictions, lower, upper)

        return {
            "model_name": self.name,
            "forecast": forecast_data,
            "historical": historical,
            "metrics": metrics,
            "total_projected": float(np.sum(predictions)),
            "monthly_average": float(np.mean(predictions)),
            "annual_projections": annual_projections
        }

    def _prepare_historical(self, series: pd.Series) -> List[Dict[str, Any]]:
        """Extract historical data for charting."""
        return [
            {
                "month": date.strftime("%Y-%m") if isinstance(date, (pd.Timestamp, datetime)) else str(date),
                "value": float(value)
            }
            for date, value in series.items()
        ]

    def _calculate_metrics(
        self,
        actual: pd.Series,
        predicted: np.ndarray
    ) -> Dict[str, float]:
        """Calculate forecast accuracy metrics."""
        # Handle case where predicted is shorter than actual
        n = min(len(actual), len(predicted))
        if n == 0:
            return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

        actual_values = actual.values[-n:]
        predicted_values = predicted[:n]

        mae = np.mean(np.abs(actual_values - predicted_values))
        rmse = np.sqrt(np.mean((actual_values - predicted_values) ** 2))

        # Avoid division by zero in MAPE
        mape = 0.0
        if np.any(actual_values != 0):
            mape = np.mean(
                np.abs((actual_values - predicted_values) / np.where(actual_values != 0, actual_values, 1))
            ) * 100

        return {
            "mae": float(mae),
            "rmse": float(rmse),
            "mape": float(mape)
        }

    def _calculate_annual_projections(
        self,
        predictions: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Group predictions by year."""
        current_year = datetime.now().year
        projections = []

        for i in range(0, len(predictions), 12):
            year_data = predictions[i:i+12]
            projections.append({
                "year": current_year + (i // 12),
                "total": float(np.sum(year_data)),
                "months": len(year_data)
            })

        return projections

    def _format_forecast(
        self,
        predictions: np.ndarray,
        lower: np.ndarray,
        upper: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Format predictions with confidence intervals."""
        start_date = pd.Timestamp.now().normalize()

        return [
            {
                "month": (start_date + pd.DateOffset(months=i)).strftime("%Y-%m"),
                "value": float(predictions[i]),
                "lower": float(lower[i]),
                "upper": float(upper[i])
            }
            for i in range(len(predictions))
        ]
