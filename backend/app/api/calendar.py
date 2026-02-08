"""
Calendar API Endpoints.

Provides dividend calendar views and iCalendar export functionality.
"""

from fastapi import APIRouter, Depends, Query, Response
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
from icalendar import Calendar, Event as iCalEvent
import logging

from app.models.calendar import CalendarMonth, DividendEvent, UpcomingDividend
from app.dependencies import get_data
from app.middleware.auth import require_auth
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[CalendarMonth])
async def get_calendar_view(
    year: int = Query(default=None, description="Year to view (default: current year)"),
    months: int = Query(default=12, ge=1, le=24, description="Number of months to display"),
    user: Dict = Depends(require_auth),
    data: tuple = Depends(get_data)
):
    """
    Get dividend calendar for specified period.

    Returns calendar data grouped by month with all dividend events.
    """
    # Unpack data tuple
    df, _ = data

    # Default to current year
    if year is None:
        year = datetime.now().year

    # Ensure Time column is datetime
    if 'Time' in df.columns:
        df['Time'] = pd.to_datetime(df['Time'])

    # Extract year and month
    df['Year'] = df['Time'].dt.year
    df['Month'] = df['Time'].dt.month

    # Filter data for the specified year
    year_data = df[df['Year'] == year].copy()

    # Group by month
    calendar_months = []
    for month in range(1, 13):
        month_data = year_data[year_data['Month'] == month]

        # Create events for this month
        events = [
            DividendEvent(
                date=row['Time'].date(),
                ticker=row['Ticker'],
                company_name=row['Name'],
                amount=float(row['Total']),
                expected=False
            )
            for _, row in month_data.iterrows()
        ]

        # Calculate total for the month
        total = float(month_data['Total'].sum()) if len(month_data) > 0 else 0.0

        calendar_months.append(CalendarMonth(
            year=year,
            month=month,
            events=events,
            total=total
        ))

    logger.info(f"Retrieved calendar for {year} with {sum(len(m.events) for m in calendar_months)} events")
    return calendar_months


@router.get("/export.ics")
@limiter.limit("10/minute")
async def export_calendar(
    request,
    year: int = Query(default=None, description="Year to export (default: current year)"),
    months: int = Query(default=12, ge=1, le=24, description="Number of months to export"),
    user: Dict = Depends(require_auth),
    data: tuple = Depends(get_data)
):
    """
    Export dividend calendar as iCalendar (.ics) file.

    The exported file can be imported into Google Calendar, Outlook, Apple Calendar, etc.
    """
    # Unpack data tuple
    df, _ = data

    # Default to current year
    if year is None:
        year = datetime.now().year

    # Ensure Time column is datetime
    if 'Time' in df.columns:
        df['Time'] = pd.to_datetime(df['Time'])

    # Filter data for the specified period
    start_date = datetime(year, 1, 1)
    end_date = start_date + timedelta(days=30 * months)

    filtered_df = df[(df['Time'] >= start_date) & (df['Time'] < end_date)].copy()

    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//Dividend Portfolio Dashboard//EN')
    cal.add('version', '2.0')
    cal.add('calname', 'Dividend Payments')
    cal.add('x-wr-calname', 'Dividend Payments')
    cal.add('x-wr-caldesc', 'Dividend payment schedule from portfolio tracking')

    # Add events for each dividend
    for _, row in filtered_df.iterrows():
        event = iCalEvent()

        # Event summary
        event.add('summary', f'{row["Ticker"]} Dividend - £{row["Total"]:.2f}')

        # All-day event
        event_date = row['Time'].date()
        event.add('dtstart', event_date)
        event.add('dtend', event_date + timedelta(days=1))

        # Description with details
        description = (
            f'Dividend payment from {row["Name"]} ({row["Ticker"]})\n'
            f'Amount: £{row["Total"]:.2f}\n'
            f'Payment Date: {event_date.isoformat()}'
        )
        event.add('description', description)

        # Unique ID for the event
        event.add('uid', f'{row["Ticker"]}-{row["Time"].isoformat()}@dividends-app')

        # Add creation timestamp
        event.add('dtstamp', datetime.now())

        cal.add_component(event)

    logger.info(f"Exported {len(filtered_df)} dividend events to iCalendar format")

    # Return as downloadable file
    return Response(
        content=cal.to_ical(),
        media_type='text/calendar',
        headers={
            'Content-Disposition': f'attachment; filename="dividends_{year}.ics"'
        }
    )


@router.get("/upcoming", response_model=List[UpcomingDividend])
async def get_upcoming_dividends(
    days: int = Query(default=30, ge=1, le=90, description="Number of days to look ahead"),
    user: Dict = Depends(require_auth),
    data: tuple = Depends(get_data)
):
    """
    Get dividends expected in the next N days.

    Uses historical payment patterns to predict upcoming dividends.
    """
    # Unpack data tuple
    df, _ = data

    # Ensure Time column is datetime
    if 'Time' in df.columns:
        df['Time'] = pd.to_datetime(df['Time'])

    # Current date
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    # Find stocks that have paid dividends in this month historically
    df['Month'] = df['Time'].dt.month
    df['Year'] = df['Time'].dt.year

    # Get historical payments for current month
    month_stocks = df[df['Month'] == current_month].copy()

    upcoming = []

    # Group by ticker to find patterns
    for ticker in month_stocks['Ticker'].unique():
        ticker_data = month_stocks[month_stocks['Ticker'] == ticker]

        # Check if they've already paid this year
        paid_this_year = df[(df['Ticker'] == ticker) & (df['Year'] == current_year)]
        paid_this_month = df[
            (df['Ticker'] == ticker) &
            (df['Year'] == current_year) &
            (df['Month'] == current_month)
        ]

        # Skip if already paid this month
        if len(paid_this_month) > 0:
            continue

        # Calculate average amount
        avg_amount = ticker_data['Total'].mean()

        # Estimate payment date (use median day of month from historical data)
        historical_days = ticker_data['Time'].dt.day
        median_day = int(historical_days.median()) if len(historical_days) > 0 else 15

        # Create expected date
        try:
            expected_date = datetime(current_year, current_month, median_day)
        except ValueError:
            # Handle invalid dates (e.g., Feb 30)
            expected_date = datetime(current_year, current_month, min(median_day, 28))

        # Only include if within the days window
        days_until = (expected_date - current_date).days
        if 0 <= days_until <= days:
            # Determine confidence based on historical consistency
            payment_count = len(ticker_data)
            if payment_count >= 3:
                confidence = "high"
            elif payment_count >= 2:
                confidence = "medium"
            else:
                confidence = "low"

            upcoming.append(UpcomingDividend(
                ticker=ticker,
                company_name=ticker_data['Name'].iloc[0],
                expected_date=expected_date.date().isoformat(),
                estimated_amount=float(avg_amount),
                confidence=confidence
            ))

    # Sort by expected date
    upcoming.sort(key=lambda x: x.expected_date)

    logger.info(f"Found {len(upcoming)} upcoming dividends in next {days} days")
    return upcoming
