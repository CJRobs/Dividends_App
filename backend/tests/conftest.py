"""
Pytest configuration and fixtures for backend tests.

Provides reusable test fixtures for API testing and data mocking.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from fastapi.testclient import TestClient
from typing import Generator

# Import the main app
from app.main import app
from app.dependencies import set_data, clear_data
from app.services.data_processor import preprocess_data, get_monthly_data
from app.config import get_settings


@pytest.fixture(scope="session")
def test_settings():
    """Get test settings."""
    return get_settings()


@pytest.fixture(scope="function")
def test_client() -> Generator[TestClient, None, None]:
    """
    Create a test client for the FastAPI application.

    Yields:
        TestClient instance for making API requests
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def mock_dividend_data() -> pd.DataFrame:
    """
    Create mock dividend data for testing.

    Returns:
        DataFrame with sample dividend records matching the real CSV schema
    """
    records = []
    # Create 24 months of data for 2 stocks
    for month_offset in range(24):
        date = pd.Timestamp("2024-01-15") + pd.DateOffset(months=month_offset)
        records.append({
            "Action": "Dividend (Ordinary)",
            "Time": date,
            "ISIN": "US0378331005",
            "Ticker": "AAPL",
            "Name": "Apple Inc.",
            "No. of shares": 10.0,
            "Price/share": 0.0,
            "Currency (Price/share)": "USD",
            "Exchange rate": 1.0,
            "Total": 100.0 + month_offset * 2,
            "Currency (Total)": "GBP",
            "Withholding tax": 0.0,
            "Currency (Withholding tax)": "GBP",
        })
        records.append({
            "Action": "Dividend (Ordinary)",
            "Time": date + pd.DateOffset(days=5),
            "ISIN": "US5949181045",
            "Ticker": "MSFT",
            "Name": "Microsoft Corp.",
            "No. of shares": 5.0,
            "Price/share": 0.0,
            "Currency (Price/share)": "USD",
            "Exchange rate": 1.0,
            "Total": 150.0 + month_offset * 3,
            "Currency (Total)": "GBP",
            "Withholding tax": 0.0,
            "Currency (Withholding tax)": "GBP",
        })

    df = pd.DataFrame(records)
    df["Time"] = pd.to_datetime(df["Time"])
    return df


@pytest.fixture(scope="function", autouse=True)
def setup_test_data(mock_dividend_data):
    """
    Automatically set up test data before each test.

    Preprocesses mock data the same way the real app does at startup,
    then injects it via the dependency layer.
    """
    df = preprocess_data(mock_dividend_data.copy())
    monthly_data = get_monthly_data(df)

    set_data(df, monthly_data)

    yield

    clear_data()


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API endpoint tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        if "tests/unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        if "tests/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "tests/api/" in str(item.fspath):
            item.add_marker(pytest.mark.api)
