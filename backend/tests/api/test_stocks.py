"""
Tests for stocks API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_list_stocks(test_client: TestClient):
    """Test getting list of all stocks."""
    response = test_client.get("/api/stocks/list")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 2

    stock = data[0]
    assert "ticker" in stock
    assert "name" in stock
    assert "total_dividends" in stock
    assert "dividend_count" in stock
    assert "percentage_of_portfolio" in stock


@pytest.mark.api
def test_get_stock_details_valid_ticker(test_client: TestClient):
    """Test getting details for a valid stock ticker."""
    # First get a valid ticker from the stock list
    list_response = test_client.get("/api/stocks/list?limit=1")
    assert list_response.status_code == 200
    stocks = list_response.json()
    assert len(stocks) > 0
    ticker = stocks[0]["ticker"]

    response = test_client.get(f"/api/stocks/{ticker}")

    assert response.status_code == 200
    data = response.json()

    assert "detail" in data
    assert "yearly_totals" in data
    assert "payment_history" in data
    assert data["detail"]["ticker"] == ticker


@pytest.mark.api
@pytest.mark.security
def test_get_stock_invalid_ticker_format(test_client: TestClient):
    """Test that invalid ticker format is rejected."""
    invalid_tickers = [
        "'; DROP TABLE--",
        "ABC DEF",
        "A" * 10,  # Too long
    ]

    for ticker in invalid_tickers:
        response = test_client.get(f"/api/stocks/{ticker}")
        assert response.status_code == 400, f"Ticker '{ticker}' should be rejected"


@pytest.mark.api
def test_get_stock_not_found(test_client: TestClient):
    """Test getting details for a stock that doesn't exist."""
    response = test_client.get("/api/stocks/ZZZZ")

    assert response.status_code == 404


@pytest.mark.api
def test_get_stocks_overview(test_client: TestClient):
    """Test getting stocks overview."""
    response = test_client.get("/api/stocks/")

    assert response.status_code == 200
    data = response.json()

    assert "stocks" in data
    assert "distribution" in data
    assert "concentration" in data
    assert "total_stocks" in data
    assert "total_dividends" in data


@pytest.mark.api
def test_get_stock_distribution(test_client: TestClient):
    """Test getting stock distribution data."""
    response = test_client.get("/api/stocks/distribution")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 2

    item = data[0]
    assert "name" in item
    assert "total" in item
    assert "percentage" in item


@pytest.mark.api
def test_get_stocks_by_period(test_client: TestClient):
    """Test getting stocks by period."""
    response = test_client.get("/api/stocks/by-period?period_type=Monthly")

    assert response.status_code == 200
    data = response.json()

    assert "periods" in data
    assert "stocks" in data
    assert "data" in data
    assert "period_type" in data


@pytest.mark.api
def test_get_growth_analysis(test_client: TestClient):
    """Test getting growth analysis."""
    response = test_client.get("/api/stocks/growth")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.api
def test_get_concentration_analysis(test_client: TestClient):
    """Test getting concentration risk analysis."""
    response = test_client.get("/api/stocks/concentration")

    assert response.status_code == 200
    data = response.json()

    assert "top_1_percent" in data
    assert "top_3_percent" in data
    assert "top_5_percent" in data
