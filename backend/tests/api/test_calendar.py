"""
Tests for calendar API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_get_calendar_view(test_client: TestClient):
    """Test getting calendar view for a year."""
    response = test_client.get("/api/calendar/?year=2024")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    month = data[0]
    assert "year" in month
    assert "month" in month
    assert "events" in month
    assert "total" in month
    assert isinstance(month["events"], list)


@pytest.mark.api
def test_calendar_events_have_correct_fields(test_client: TestClient):
    """Test that calendar events contain expected fields."""
    response = test_client.get("/api/calendar/?year=2024")
    data = response.json()

    # Find a month with events
    months_with_events = [m for m in data if len(m["events"]) > 0]
    assert len(months_with_events) > 0

    event = months_with_events[0]["events"][0]
    assert "date" in event
    assert "ticker" in event
    assert "amount" in event


@pytest.mark.api
def test_export_ics(test_client: TestClient):
    """Test iCalendar export returns correct content type."""
    response = test_client.get("/api/calendar/export.ics")

    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "text/calendar" in content_type or "application/octet-stream" in content_type


@pytest.mark.api
def test_get_upcoming_dividends(test_client: TestClient):
    """Test getting upcoming dividends."""
    response = test_client.get("/api/calendar/upcoming?days=30")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
