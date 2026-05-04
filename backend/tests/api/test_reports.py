"""
Tests for reports API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_get_available_periods(test_client: TestClient):
    """Test getting available report periods."""
    response = test_client.get("/api/reports/periods")

    assert response.status_code == 200
    data = response.json()

    assert "monthly" in data
    assert "quarterly" in data
    assert "yearly" in data
    assert isinstance(data["monthly"], list)
    assert isinstance(data["yearly"], list)


@pytest.mark.api
def test_preview_yearly_report(test_client: TestClient):
    """Test previewing a yearly report."""
    response = test_client.post(
        "/api/reports/preview",
        json={"period_type": "Yearly", "year": 2024}
    )

    assert response.status_code == 200
    data = response.json()

    assert "period_type" in data
    assert "total_dividends" in data
    assert "dividend_count" in data
    assert "top_stocks" in data
    assert data["total_dividends"] > 0


@pytest.mark.api
def test_preview_monthly_report(test_client: TestClient):
    """Test previewing a monthly report."""
    response = test_client.post(
        "/api/reports/preview",
        json={"period_type": "Monthly", "year": 2024, "month": 6}
    )

    assert response.status_code == 200
    data = response.json()

    assert "period_type" in data
    assert "total_dividends" in data
