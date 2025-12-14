"""
PDF Reports API endpoints.

Provides PDF report generation for dividend analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import io

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from app.config import get_settings, format_currency

router = APIRouter()


class ReportRequest(BaseModel):
    """Request model for report generation."""
    period_type: str  # "Monthly", "Quarterly", "Yearly"
    year: int
    month: Optional[int] = None  # For monthly reports
    quarter: Optional[int] = None  # For quarterly reports


class PeriodInfo(BaseModel):
    """Available period information."""
    label: str
    year: int
    month: Optional[int] = None
    quarter: Optional[int] = None


class AvailablePeriodsResponse(BaseModel):
    """Response with available periods for reports."""
    monthly: List[PeriodInfo]
    quarterly: List[PeriodInfo]
    yearly: List[PeriodInfo]


class ReportPreview(BaseModel):
    """Preview data for a report."""
    period_type: str
    period_label: str
    total_dividends: float
    dividend_count: int
    unique_stocks: int
    top_stocks: List[dict]
    monthly_breakdown: Optional[List[dict]] = None


def get_data():
    from app.dependencies import get_data as _get_data
    return _get_data()


def get_period_dates(period_type: str, year: int, month: int = None, quarter: int = None):
    """Get start and end dates for a period."""
    if period_type == "Monthly":
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    elif period_type == "Quarterly":
        start_month = (quarter - 1) * 3 + 1
        start_date = datetime(year, start_month, 1)
        if quarter == 4:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_month = quarter * 3 + 1
            end_date = datetime(year, end_month, 1) - timedelta(days=1)
    else:  # Yearly
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)

    return start_date, end_date


def create_pdf_report(
    df: pd.DataFrame,
    period_type: str,
    start_date: datetime,
    end_date: datetime,
    currency: str = "GBP"
) -> bytes:
    """Generate PDF report for specified period."""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor("#1a237e"),
    )
    normal_style = styles["Normal"]

    story = []

    # Title
    if period_type == "Monthly":
        title = f"Monthly Dividend Report - {start_date.strftime('%B %Y')}"
    elif period_type == "Quarterly":
        quarter = (start_date.month - 1) // 3 + 1
        title = f"Quarterly Dividend Report - Q{quarter} {start_date.year}"
    else:
        title = f"Annual Dividend Report - {start_date.year}"

    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))

    # Filter data for the period
    period_df = df[(df["Time"] >= start_date) & (df["Time"] <= end_date)].copy()

    if period_df.empty:
        story.append(
            Paragraph("No dividend data available for this period.", normal_style)
        )
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    # Summary Section
    story.append(Paragraph("Summary", heading_style))

    total_dividends = period_df["Total"].sum()
    dividend_count = len(period_df)
    unique_stocks = period_df["Ticker"].nunique()
    avg_dividend = period_df["Total"].mean()

    summary_data = [
        ["Metric", "Value"],
        ["Total Dividends", format_currency(total_dividends, currency)],
        ["Number of Payments", str(dividend_count)],
        ["Unique Stocks", str(unique_stocks)],
        ["Average Dividend", format_currency(avg_dividend, currency)],
    ]

    summary_table = Table(summary_data, colWidths=[2.5 * inch, 2.5 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f5f5")),
        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e0e0e0")),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("TOPPADDING", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Top Stocks Section
    story.append(Paragraph("Top Performing Stocks", heading_style))

    stock_totals = period_df.groupby(["Ticker", "Name"])["Total"].agg(["sum", "count"]).reset_index()
    stock_totals.columns = ["Ticker", "Name", "Total", "Count"]
    stock_totals = stock_totals.sort_values("Total", ascending=False).head(10)

    stock_data = [["Ticker", "Company", "Total", "Payments"]]
    for _, row in stock_totals.iterrows():
        stock_data.append([
            row["Ticker"],
            row["Name"][:30] + "..." if len(str(row["Name"])) > 30 else row["Name"],
            format_currency(row["Total"], currency),
            str(int(row["Count"]))
        ])

    stock_table = Table(stock_data, colWidths=[1 * inch, 2.5 * inch, 1.2 * inch, 0.8 * inch])
    stock_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (2, 0), (3, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
    ]))

    story.append(stock_table)
    story.append(Spacer(1, 20))

    # Monthly breakdown for quarterly/yearly reports
    if period_type in ["Quarterly", "Yearly"]:
        story.append(Paragraph("Monthly Breakdown", heading_style))

        period_df["YearMonth"] = period_df["Time"].dt.to_period("M")
        monthly_totals = period_df.groupby("YearMonth")["Total"].sum().reset_index()
        monthly_totals["YearMonth"] = monthly_totals["YearMonth"].astype(str)

        monthly_data = [["Month", "Total"]]
        for _, row in monthly_totals.iterrows():
            monthly_data.append([
                row["YearMonth"],
                format_currency(row["Total"], currency)
            ])

        monthly_table = Table(monthly_data, colWidths=[2 * inch, 2 * inch])
        monthly_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
        ]))

        story.append(monthly_table)
        story.append(Spacer(1, 20))

    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        "Footer",
        parent=normal_style,
        fontSize=8,
        textColor=colors.gray,
        alignment=TA_CENTER
    )
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Dividend Portfolio Dashboard",
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


@router.get("/periods", response_model=AvailablePeriodsResponse)
async def get_available_periods(data: tuple = Depends(get_data)):
    """
    Get available periods for report generation.
    """
    df, _ = data

    if df.empty:
        return AvailablePeriodsResponse(monthly=[], quarterly=[], yearly=[])

    # Get unique year-months
    df["YearMonth"] = df["Time"].dt.to_period("M")
    periods = df["YearMonth"].unique()

    monthly = []
    quarterly_set = set()
    yearly_set = set()

    for period in sorted(periods, reverse=True):
        year = period.year
        month = period.month

        # Monthly
        monthly.append(PeriodInfo(
            label=period.strftime("%B %Y"),
            year=year,
            month=month
        ))

        # Quarterly
        quarter = (month - 1) // 3 + 1
        quarter_key = (year, quarter)
        if quarter_key not in quarterly_set:
            quarterly_set.add(quarter_key)

        # Yearly
        yearly_set.add(year)

    quarterly = [
        PeriodInfo(
            label=f"Q{q} {y}",
            year=y,
            quarter=q
        )
        for y, q in sorted(quarterly_set, reverse=True)
    ]

    yearly = [
        PeriodInfo(
            label=str(y),
            year=y
        )
        for y in sorted(yearly_set, reverse=True)
    ]

    return AvailablePeriodsResponse(
        monthly=monthly[:24],  # Last 2 years
        quarterly=quarterly[:8],  # Last 2 years
        yearly=yearly
    )


@router.post("/preview", response_model=ReportPreview)
async def preview_report(request: ReportRequest, data: tuple = Depends(get_data)):
    """
    Get preview data for a report.
    """
    df, _ = data
    settings = get_settings()

    # Get period dates
    start_date, end_date = get_period_dates(
        request.period_type,
        request.year,
        request.month,
        request.quarter
    )

    # Filter data
    period_df = df[(df["Time"] >= start_date) & (df["Time"] <= end_date)]

    if period_df.empty:
        raise HTTPException(status_code=404, detail="No data for this period")

    # Calculate metrics
    total_dividends = float(period_df["Total"].sum())
    dividend_count = len(period_df)
    unique_stocks = period_df["Ticker"].nunique()

    # Top stocks
    stock_totals = period_df.groupby(["Ticker", "Name"])["Total"].sum().reset_index()
    stock_totals = stock_totals.sort_values("Total", ascending=False).head(5)
    top_stocks = [
        {
            "ticker": row["Ticker"],
            "name": row["Name"],
            "total": float(row["Total"])
        }
        for _, row in stock_totals.iterrows()
    ]

    # Monthly breakdown for quarterly/yearly
    monthly_breakdown = None
    if request.period_type in ["Quarterly", "Yearly"]:
        period_df_copy = period_df.copy()
        period_df_copy["YearMonth"] = period_df_copy["Time"].dt.to_period("M")
        monthly_totals = period_df_copy.groupby("YearMonth")["Total"].sum()
        monthly_breakdown = [
            {"month": str(m), "total": float(t)}
            for m, t in monthly_totals.items()
        ]

    # Period label
    if request.period_type == "Monthly":
        period_label = start_date.strftime("%B %Y")
    elif request.period_type == "Quarterly":
        period_label = f"Q{request.quarter} {request.year}"
    else:
        period_label = str(request.year)

    return ReportPreview(
        period_type=request.period_type,
        period_label=period_label,
        total_dividends=total_dividends,
        dividend_count=dividend_count,
        unique_stocks=unique_stocks,
        top_stocks=top_stocks,
        monthly_breakdown=monthly_breakdown
    )


@router.post("/generate")
async def generate_report(request: ReportRequest, data: tuple = Depends(get_data)):
    """
    Generate and download PDF report.
    """
    df, _ = data
    settings = get_settings()

    # Get period dates
    start_date, end_date = get_period_dates(
        request.period_type,
        request.year,
        request.month,
        request.quarter
    )

    # Generate PDF
    pdf_bytes = create_pdf_report(
        df,
        request.period_type,
        start_date,
        end_date,
        settings.default_currency
    )

    # Create filename
    if request.period_type == "Monthly":
        filename = f"dividend_report_{start_date.strftime('%Y_%m')}.pdf"
    elif request.period_type == "Quarterly":
        filename = f"dividend_report_Q{request.quarter}_{request.year}.pdf"
    else:
        filename = f"dividend_report_{request.year}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
