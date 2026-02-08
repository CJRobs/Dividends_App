"""
Input validation utilities for API endpoints.

Provides validators for common input types to prevent injection attacks
and ensure data integrity.
"""

import re
from datetime import datetime
from fastapi import HTTPException, status
from typing import Optional


# Ticker symbol pattern: 1-5 uppercase letters
TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}$')

# Valid forecast models
VALID_FORECAST_MODELS = [
    "sarimax", "holt_winters", "prophet", "theta", "simple", "ensemble"
]


def validate_ticker(ticker: str) -> str:
    """
    Validate and sanitize stock ticker symbol.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Sanitized uppercase ticker

    Raises:
        HTTPException: If ticker format is invalid
    """
    if not ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker symbol is required"
        )

    # Convert to uppercase and strip whitespace
    ticker = ticker.upper().strip()

    # Validate format
    if not TICKER_PATTERN.match(ticker):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ticker format: '{ticker}'. Must be 1-5 uppercase letters."
        )

    return ticker


def validate_year(year: int) -> int:
    """
    Validate year is within reasonable range.

    Args:
        year: Year value

    Returns:
        Validated year

    Raises:
        HTTPException: If year is invalid
    """
    current_year = datetime.now().year
    min_year = 2000
    max_year = current_year + 1

    if not (min_year <= year <= max_year):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid year: {year}. Must be between {min_year} and {max_year}."
        )

    return year


def validate_month(month: int) -> int:
    """
    Validate month is between 1-12.

    Args:
        month: Month value

    Returns:
        Validated month

    Raises:
        HTTPException: If month is invalid
    """
    if not (1 <= month <= 12):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid month: {month}. Must be between 1 and 12."
        )

    return month


def validate_forecast_months(months: int, max_months: int = 36) -> int:
    """
    Validate forecast period length.

    Args:
        months: Number of months to forecast
        max_months: Maximum allowed months

    Returns:
        Validated months

    Raises:
        HTTPException: If months value is invalid
    """
    if not (1 <= months <= max_months):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid forecast period: {months}. Must be between 1 and {max_months} months."
        )

    return months


def validate_forecast_model(model: str) -> str:
    """
    Validate forecast model name.

    Args:
        model: Model name

    Returns:
        Validated lowercase model name

    Raises:
        HTTPException: If model is not supported
    """
    model_lower = model.lower().strip()

    if model_lower not in VALID_FORECAST_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid forecast model: '{model}'. Valid models: {', '.join(VALID_FORECAST_MODELS)}"
        )

    return model_lower


def validate_positive_number(value: float, field_name: str = "value") -> float:
    """
    Validate that a number is positive.

    Args:
        value: Number to validate
        field_name: Name of the field for error messages

    Returns:
        Validated value

    Raises:
        HTTPException: If value is not positive
    """
    if value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}: {value}. Must be a positive number."
        )

    return value


def validate_pagination(
    offset: int = 0,
    limit: int = 100,
    max_limit: int = 1000
) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Args:
        offset: Number of records to skip
        limit: Number of records to return
        max_limit: Maximum allowed limit

    Returns:
        Tuple of (validated_offset, validated_limit)

    Raises:
        HTTPException: If pagination parameters are invalid
    """
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid offset: {offset}. Must be non-negative."
        )

    if not (1 <= limit <= max_limit):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid limit: {limit}. Must be between 1 and {max_limit}."
        )

    return offset, limit


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize string input by removing dangerous characters.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        HTTPException: If string is too long
    """
    # Strip whitespace
    value = value.strip()

    # Check length
    if len(value) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Input too long: {len(value)} characters. Maximum is {max_length}."
        )

    # Remove potential SQL injection characters (basic protection)
    dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
    for char in dangerous_chars:
        if char in value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid characters detected in input"
            )

    return value
