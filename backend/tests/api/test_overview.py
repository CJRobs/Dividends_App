"""
Tests for overview API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.unit
def test_get_overview_summary(test_client: TestClient, auth_headers):
    """Test getting portfolio summary."""
    response = test_client.get("/api/overview/summary", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Check that expected fields are present
    assert "ytd_total" in data
    assert "total_invested" in data
    assert isinstance(data["ytd_total"], (int, float))


@pytest.mark.api
@pytest.mark.unit
def test_get_ytd_chart(test_client: TestClient, auth_headers):
    """Test getting YTD chart data."""
    response = test_client.get("/api/overview/ytd-chart", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should return chart data
    assert isinstance(data, (list, dict))


@pytest.mark.api
@pytest.mark.unit
def test_get_top_stocks(test_client: TestClient, auth_headers):
    """Test getting top dividend-paying stocks."""
    response = test_client.get("/api/overview/top-stocks", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # With our mock data, should have at least 2 stocks
    assert len(data) >= 2

    if len(data) > 0:
        # Check structure of first stock
        stock = data[0]
        assert "ticker" in stock
        assert "name" in stock
        assert "total" in stock


@pytest.mark.api
@pytest.mark.unit
def test_get_recent_dividends(test_client: TestClient, auth_headers):
    """Test getting recent dividend payments."""
    response = test_client.get("/api/overview/recent-dividends", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)

    if len(data) > 0:
        dividend = data[0]
        assert "date" in dividend or "time" in dividend.lower()
        assert "ticker" in dividend
        assert "total" in dividend or "amount" in dividend


@pytest.mark.api
@pytest.mark.unit
def test_get_annual_stats(test_client: TestClient, auth_headers):
    """Test getting annual statistics."""
    response = test_client.get("/api/overview/annual-stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)

    if len(data) > 0:
        year_stat = data[0]
        assert "year" in year_stat
        assert "total" in year_stat


@pytest.mark.api
@pytest.mark.unit
def test_overview_with_invalid_year(test_client: TestClient, auth_headers):
    """Test overview endpoints with invalid year parameter."""
    response = test_client.get(
        "/api/overview/summary?year=1999",
        headers=auth_headers
    )

    # Should either return 400 (if validated) or handle gracefully
    assert response.status_code in [200, 400]
