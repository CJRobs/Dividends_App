"""
Tests for main application endpoints and core functionality.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_root_endpoint(test_client: TestClient):
    """Test the root endpoint returns API information."""
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert data["docs"] == "/docs"


@pytest.mark.unit
def test_health_check_with_data(test_client: TestClient):
    """Test health check endpoint with loaded data."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["data_loaded"] is True
    assert data["record_count"] > 0
    assert "settings" in data


@pytest.mark.unit
def test_cors_headers(test_client: TestClient):
    """Test that CORS headers are properly configured."""
    response = test_client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )

    # Check that CORS headers are present
    assert "access-control-allow-origin" in response.headers.keys() or \
           "Access-Control-Allow-Origin" in response.headers.keys()


@pytest.mark.unit
def test_security_headers(test_client: TestClient):
    """Test that security headers are added to responses."""
    response = test_client.get("/")

    headers = {k.lower(): v for k, v in response.headers.items()}

    # Check for security headers
    assert "x-content-type-options" in headers
    assert headers["x-content-type-options"] == "nosniff"

    assert "x-frame-options" in headers
    assert headers["x-frame-options"] == "DENY"

    assert "x-xss-protection" in headers


@pytest.mark.unit
def test_invalid_endpoint_returns_404(test_client: TestClient):
    """Test that invalid endpoints return 404."""
    response = test_client.get("/invalid/endpoint/that/does/not/exist")

    assert response.status_code == 404
