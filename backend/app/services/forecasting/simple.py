"""
Simple Average Forecast Model.

Provides a basic moving average forecast as a fallback option.
"""

import numpy as np
import pandas as pd
from typing import Tuple
from .base import ForecastModel


class SimpleAverageModel(ForecastModel):
    """Simple moving average forecast model."""

    name = "Simple Average"

    def fit_predict(
        self,
        series: pd.Series,
        periods: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate forecast using simple moving average.

        Args:
            series: Historical time series data
            periods: Number of periods to forecast

        Returns:
            Tuple of (predictions, lower_bounds, upper_bounds)
        """
        # Use last 6 months average
        lookback = min(6, len(series))
        recent_avg = series.tail(lookback).mean()

        # All predictions are the same (average)
        predictions = np.full(periods, recent_avg)

        # Confidence bands based on historical standard deviation
        std = series.tail(12).std() if len(series) >= 12 else series.std()
        lower = predictions - std
        upper = predictions + std

        return predictions, lower, upper
