"""
Type conversion utilities for numpy/pandas to native Python types.
"""

import numpy as np
import pandas as pd
from typing import Any


def to_python_type(value: Any) -> Any:
    """
    Convert numpy/pandas types to native Python types for JSON serialization.

    Args:
        value: Any value that might be a numpy/pandas type

    Returns:
        Native Python type equivalent
    """
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    if isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.str_, str)):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value
