"""
Pytest configuration and fixtures for backend tests.

Provides reusable test fixtures for API testing, authentication, and data mocking.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from typing import Dict, Generator
import json
from pathlib import Path

# Import the main app
from app.main import app
from app.dependencies import set_data_state
from app.config import get_settings
from app.middleware.auth import create_access_token
from app.utils.password import hash_password


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
        DataFrame with sample dividend records
    """
    # Create 24 months of sample data
    dates = pd.date_range('2024-01-01', periods=24, freq='M')

    data = {
        'Time': dates.tolist() * 2,  # 2 stocks
        'Ticker': ['AAPL'] * 24 + ['MSFT'] * 24,
        'Name': ['Apple Inc.'] * 24 + ['Microsoft Corp.'] * 24,
        'Total': [100.0 + i * 2 for i in range(24)] + [150.0 + i * 3 for i in range(24)],
        'ISIN': ['US0378331005'] * 24 + ['US5949181045'] * 24,
        'Account Type': ['ISA'] * 24 + ['GIA'] * 24,
    }

    df = pd.DataFrame(data)
    df['Time'] = pd.to_datetime(df['Time'])

    return df


@pytest.fixture(scope="function", autouse=True)
def setup_test_data(mock_dividend_data):
    """
    Automatically set up test data before each test.

    Args:
        mock_dividend_data: Mock dividend data fixture
    """
    # Preprocess the data like the real app does
    df = mock_dividend_data.copy()
    df['Year'] = df['Time'].dt.year
    df['Month'] = df['Time'].dt.month
    df['MonthName'] = df['Time'].dt.strftime('%B')
    df['Quarter'] = df['Time'].dt.quarter
    df['Day'] = df['Time'].dt.day
    df['DayOfWeek'] = df['Time'].dt.dayofweek
    df['WeekOfYear'] = df['Time'].dt.isocalendar().week

    # Create monthly aggregated data
    monthly_data = df.groupby(['Year', 'Month', 'MonthName']).agg({
        'Total': 'sum'
    }).reset_index()

    # Set the data in the app
    set_data_state({
        "data": df,
        "monthly_data": monthly_data,
        "record_count": len(df),
        "last_loaded": datetime.now().isoformat(),
        "loaded": True
    })

    yield

    # Cleanup after test
    set_data_state(None)


@pytest.fixture(scope="function")
def auth_token(test_settings) -> str:
    """
    Create a valid JWT token for testing authenticated endpoints.

    Returns:
        JWT access token string
    """
    token = create_access_token(
        data={"sub": "testuser"},
        expires_delta=timedelta(minutes=30)
    )
    return token


@pytest.fixture(scope="function")
def auth_headers(auth_token) -> Dict[str, str]:
    """
    Create authorization headers with JWT token.

    Args:
        auth_token: JWT token from auth_token fixture

    Returns:
        Dictionary with Authorization header
    """
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="session")
def test_user_data():
    """
    Create test user data.

    Returns:
        Dictionary with test user information
    """
    return {
        "username": "testuser",
        "password": "testpass123",
        "hashed_password": hash_password("testpass123")
    }


@pytest.fixture(scope="function")
def mock_users_file(tmp_path, test_user_data):
    """
    Create a temporary users file for authentication tests.

    Args:
        tmp_path: Pytest temporary path fixture
        test_user_data: Test user data fixture

    Returns:
        Path to the temporary users file
    """
    users_data = {
        test_user_data["username"]: {
            "username": test_user_data["username"],
            "hashed_password": test_user_data["hashed_password"],
            "disabled": False
        }
    }

    users_file = tmp_path / "users.json"
    with open(users_file, 'w') as f:
        json.dump(users_data, f)

    return users_file


@pytest.fixture(scope="function")
def expired_token(test_settings) -> str:
    """
    Create an expired JWT token for testing token expiration.

    Returns:
        Expired JWT token string
    """
    token = create_access_token(
        data={"sub": "testuser"},
        expires_delta=timedelta(seconds=-1)  # Already expired
    )
    return token


@pytest.fixture(scope="function")
def invalid_token() -> str:
    """
    Create an invalid JWT token for testing token validation.

    Returns:
        Invalid token string
    """
    return "invalid.jwt.token"


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "api: API endpoint tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add 'unit' marker to all tests in tests/unit/
        if "tests/unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add 'integration' marker to all tests in tests/integration/
        if "tests/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add 'api' marker to all tests in tests/api/
        if "tests/api/" in str(item.fspath):
            item.add_marker(pytest.mark.api)
