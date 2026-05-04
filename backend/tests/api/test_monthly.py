"""
Tests for monthly analysis API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_get_monthly_by_year(test_client: TestClient):
    """Test getting monthly totals organized by year."""
    response = test_client.get("/api/monthly/by-year")

    assert response.status_code == 200
    data = response.json()

    assert "months" in data
    assert "years" in data
    assert isinstance(data["months"], list)
    assert isinstance(data["years"], dict)
    assert len(data["months"]) == 12


@pytest.mark.api
def test_get_monthly_heatmap(test_client: TestClient):
    """Test getting heatmap data."""
    response = test_client.get("/api/monthly/heatmap")

    assert response.status_code == 200
    data = response.json()

    assert "rows" in data
    assert "cols" in data
    assert "data" in data
    assert isinstance(data["data"], list)

    if len(data["data"]) > 0:
        cell = data["data"][0]
        assert "row" in cell
        assert "col" in cell
        assert "value" in cell


@pytest.mark.api
def test_get_monthly_by_company(test_client: TestClient):
    """Test getting monthly dividends by company."""
    response = test_client.get("/api/monthly/by-company")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "companies" in data
    assert "periods" in data
    assert isinstance(data["companies"], list)
    assert len(data["companies"]) >= 2


@pytest.mark.api
def test_get_coverage_analysis(test_client: TestClient):
    """Test expense coverage analysis."""
    response = test_client.get("/api/monthly/coverage?monthly_expenses=1000")

    assert response.status_code == 200
    data = response.json()

    assert "month_name" in data
    assert "amount_received" in data
    assert "coverage_percent" in data
    assert "gap_amount" in data
    assert isinstance(data["coverage_percent"], (int, float))


@pytest.mark.api
def test_get_complete_monthly_analysis(test_client: TestClient):
    """Test getting complete monthly analysis."""
    response = test_client.get("/api/monthly/")

    assert response.status_code == 200
    data = response.json()

    assert "by_year" in data
    assert "heatmap" in data
    assert "companies" in data
    assert "years" in data
