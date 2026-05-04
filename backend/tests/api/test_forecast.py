"""
Tests for forecast API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_get_simple_forecast(test_client: TestClient):
    """Test simple moving average forecast (always available)."""
    response = test_client.get("/api/forecast/simple")

    assert response.status_code == 200
    data = response.json()

    assert "model_name" in data
    assert "forecast" in data
    assert "historical" in data
    assert "total_projected" in data
    assert "monthly_average" in data
    assert isinstance(data["forecast"], list)
    assert len(data["forecast"]) > 0

    point = data["forecast"][0]
    assert "date" in point
    assert "predicted" in point


@pytest.mark.api
def test_get_simple_forecast_custom_months(test_client: TestClient):
    """Test simple forecast with custom months parameter."""
    response = test_client.get("/api/forecast/simple?months=6")

    assert response.status_code == 200
    data = response.json()

    assert len(data["forecast"]) == 6


@pytest.mark.api
def test_get_all_forecasts(test_client: TestClient):
    """Test getting all available forecasts."""
    response = test_client.get("/api/forecast/")

    assert response.status_code == 200
    data = response.json()

    assert "available_models" in data
    assert "simple_average" in data
    assert isinstance(data["available_models"], list)
    assert len(data["available_models"]) > 0


@pytest.mark.api
def test_get_ensemble_forecast(test_client: TestClient):
    """Test getting ensemble forecast."""
    response = test_client.get("/api/forecast/ensemble")

    assert response.status_code == 200
    data = response.json()

    assert "model_name" in data
    assert "forecast" in data
    assert isinstance(data["forecast"], list)


@pytest.mark.api
def test_fi_calculator(test_client: TestClient):
    """Test financial independence calculator."""
    response = test_client.get("/api/forecast/fi-calculator?monthly_goal=5000")

    assert response.status_code == 200
    data = response.json()

    assert "monthly_goal" in data
    assert "current_monthly_avg" in data
    assert "goal_reached" in data
    assert data["monthly_goal"] == 5000.0
    assert isinstance(data["current_monthly_avg"], (int, float))
