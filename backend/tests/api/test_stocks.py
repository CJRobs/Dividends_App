"""
Tests for stocks API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.unit
def test_list_stocks(test_client: TestClient, auth_headers):
    """Test getting list of all stocks."""
    response = test_client.get("/api/stocks/list", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 2  # Our mock data has AAPL and MSFT

    if len(data) > 0:
        stock = data[0]
        assert "ticker" in stock
        assert "name" in stock
        assert "total" in stock


@pytest.mark.api
@pytest.mark.unit
def test_get_stock_details_valid_ticker(test_client: TestClient, auth_headers):
    """Test getting details for a valid stock ticker."""
    response = test_client.get("/api/stocks/AAPL", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "ticker" in data or "symbol" in data
    assert "name" in data


@pytest.mark.api
@pytest.mark.unit
@pytest.mark.security
def test_get_stock_invalid_ticker_format(test_client: TestClient, auth_headers):
    """Test that invalid ticker format is rejected (SQL injection prevention)."""
    invalid_tickers = [
        "'; DROP TABLE--",
        "INVALID123",
        "ABC DEF",
        "123ABC",
        "A" * 10,  # Too long
    ]

    for ticker in invalid_tickers:
        response = test_client.get(f"/api/stocks/{ticker}", headers=auth_headers)

        # Should return 400 Bad Request due to validation
        assert response.status_code == 400, f"Ticker '{ticker}' should be rejected"


@pytest.mark.api
@pytest.mark.unit
def test_get_stock_not_found(test_client: TestClient, auth_headers):
    """Test getting details for a stock that doesn't exist."""
    response = test_client.get("/api/stocks/ZZZZ", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.api
@pytest.mark.unit
def test_get_stocks_overview(test_client: TestClient, auth_headers):
    """Test getting stocks overview."""
    response = test_client.get("/api/stocks/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should return some overview data
    assert isinstance(data, (dict, list))


@pytest.mark.api
@pytest.mark.unit
def test_get_stock_distribution(test_client: TestClient, auth_headers):
    """Test getting stock distribution data."""
    response = test_client.get("/api/stocks/distribution", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, (list, dict))


@pytest.mark.api
@pytest.mark.unit
def test_stocks_endpoint_without_auth(test_client: TestClient):
    """Test that stocks endpoints require authentication."""
    response = test_client.get("/api/stocks/list")

    assert response.status_code == 403  # Forbidden
