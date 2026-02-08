"""
Forecasting services package.

Provides various time series forecasting models for dividend predictions.
"""

from typing import Dict
from .base import ForecastModel

# Import specific models (will be created)
try:
    from .simple import SimpleAverageModel
    SIMPLE_AVAILABLE = True
except ImportError:
    SIMPLE_AVAILABLE = False

# Registry of available models
AVAILABLE_MODELS: Dict[str, ForecastModel] = {}

if SIMPLE_AVAILABLE:
    AVAILABLE_MODELS["simple"] = SimpleAverageModel()

__all__ = [
    "ForecastModel",
    "AVAILABLE_MODELS",
]
