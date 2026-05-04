"""
Tests for overview API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_get_overview_summary(test_client: TestClient):
    """Test getting portfolio summary."""
    response = test_client.get("/api/overview/summary")

    assert response.status_code == 200
    data = response.json()

    assert "total_dividends" in data
    assert "total_dividends_ytd" in data
    assert "total_count" in data
    assert "unique_stocks" in data
    assert "average_dividend" in data
    assert isinstance(data["total_dividends"], (int, float))
    assert data["total_dividends"] > 0
    assert data["unique_stocks"] > 0


@pytest.mark.api
def test_get_ytd_chart(test_client: TestClient):
    """Test getting YTD chart data."""
    response = test_client.get("/api/overview/ytd-chart")

    assert response.status_code == 200
    data = response.json()

    assert "dates" in data
    assert "values" in data
    assert "label" in data
    assert isinstance(data["dates"], list)
    assert isinstance(data["values"], list)


@pytest.mark.api
def test_get_top_stocks(test_client: TestClient):
    """Test getting top dividend-paying stocks."""
    response = test_client.get("/api/overview/top-stocks")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 2

    stock = data[0]
    assert "ticker" in stock
    assert "name" in stock
    assert "total_dividends" in stock
    assert "percentage_of_portfolio" in stock


@pytest.mark.api
def test_get_recent_dividends(test_client: TestClient):
    """Test getting recent dividend payments."""
    response = test_client.get("/api/overview/recent-dividends")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    dividend = data[0]
    assert "ticker" in dividend
    assert "amount" in dividend
    assert "date" in dividend


@pytest.mark.api
def test_get_annual_stats(test_client: TestClient):
    """Test getting annual statistics."""
    response = test_client.get("/api/overview/annual-stats")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    year_stat = data[0]
    assert "year" in year_stat
    assert "total" in year_stat
    assert "count" in year_stat
    assert "average" in year_stat


@pytest.mark.api
def test_get_yoy_comparison(test_client: TestClient):
    """Test getting year-over-year comparison."""
    response = test_client.get("/api/overview/yoy-comparison")

    assert response.status_code == 200
    data = response.json()

    assert "years" in data
    assert "months" in data
    assert "data" in data
    assert isinstance(data["years"], list)


@pytest.mark.api
def test_get_dividend_streak(test_client: TestClient):
    """Test getting dividend streak info."""
    response = test_client.get("/api/overview/dividend-streak")

    assert response.status_code == 200
    data = response.json()

    assert "current_streak" in data
    assert "longest_streak" in data
    assert "months_with_dividends" in data
    assert isinstance(data["current_streak"], int)


@pytest.mark.api
def test_get_distribution(test_client: TestClient):
    """Test getting distribution analysis."""
    response = test_client.get("/api/overview/distribution")

    assert response.status_code == 200
    data = response.json()

    assert "portfolio_allocation" in data
    assert "summary_stats" in data
    assert "concentration_risk" in data


@pytest.mark.api
def test_get_complete_overview(test_client: TestClient):
    """Test getting complete overview in single request."""
    response = test_client.get("/api/overview/")

    assert response.status_code == 200
    data = response.json()

    assert "summary" in data
    assert "ytd_chart" in data
    assert "top_stocks" in data
    assert "recent_dividends" in data


@pytest.mark.api
def test_top_stocks_with_custom_limit(test_client: TestClient):
    """Test top stocks endpoint with custom limit parameter."""
    response = test_client.get("/api/overview/top-stocks?limit=1")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
