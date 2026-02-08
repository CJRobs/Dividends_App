"""
Tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.auth
@pytest.mark.api
def test_login_success(test_client: TestClient):
    """Test successful login with default credentials."""
    response = test_client.post(
        "/api/auth/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.auth
@pytest.mark.api
def test_login_invalid_credentials(test_client: TestClient):
    """Test login with invalid credentials."""
    response = test_client.post(
        "/api/auth/login",
        data={
            "username": "admin",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.auth
@pytest.mark.api
def test_login_missing_credentials(test_client: TestClient):
    """Test login with missing credentials."""
    response = test_client.post("/api/auth/login", data={})

    assert response.status_code == 422  # Validation error


@pytest.mark.auth
@pytest.mark.api
def test_get_current_user_with_valid_token(test_client: TestClient, auth_headers):
    """Test getting current user info with valid token."""
    response = test_client.get("/api/auth/me", headers=auth_headers)

    assert response.status_code in [200, 404]  # 404 if user doesn't exist in test DB


@pytest.mark.auth
@pytest.mark.api
def test_get_current_user_without_token(test_client: TestClient):
    """Test accessing protected endpoint without token."""
    response = test_client.get("/api/auth/me")

    assert response.status_code == 403  # Forbidden (no auth header)


@pytest.mark.auth
@pytest.mark.api
def test_get_current_user_with_invalid_token(test_client: TestClient, invalid_token):
    """Test accessing protected endpoint with invalid token."""
    headers = {"Authorization": f"Bearer {invalid_token}"}
    response = test_client.get("/api/auth/me", headers=headers)

    assert response.status_code == 401  # Unauthorized


@pytest.mark.auth
@pytest.mark.api
def test_logout(test_client: TestClient, auth_headers):
    """Test logout endpoint."""
    response = test_client.post("/api/auth/logout", headers=auth_headers)

    # Should succeed or return 404 if user doesn't exist in test DB
    assert response.status_code in [200, 404]


@pytest.mark.auth
@pytest.mark.api
def test_protected_endpoint_without_auth(test_client: TestClient):
    """Test that protected endpoints require authentication."""
    # Try to access overview endpoint without authentication
    response = test_client.get("/api/overview/summary")

    assert response.status_code == 403  # Should be forbidden without auth
