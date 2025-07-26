"""PDF Reports Tab Module.

This module provides functionality for generating and downloading 
PDF reports for monthly, quarterly, and yearly dividend analysis.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def create_pdf_report(df: pd.DataFrame, monthly_data: pd.DataFrame, period_type: str, 
                     period_date: datetime, currency: str, format_currency) -> bytes:
    """Generate PDF report for specified period."""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#1a237e')
    )
    
    story = []
    
    # Title
    if period_type == "Monthly":
        title = f"Monthly Dividend Report - {period_date.strftime('%B %Y')}"
        start_date = period_date.replace(day=1)
        if period_date.month == 12:
            end_date = period_date.replace(year=period_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = period_date.replace(month=period_date.month + 1, day=1) - timedelta(days=1)
    elif period_type == "Quarterly":
        quarter = (period_date.month - 1) // 3 + 1
        title = f"Quarterly Dividend Report - Q{quarter} {period_date.year}"
        start_month = (quarter - 1) * 3 + 1
        start_date = period_date.replace(month=start_month, day=1)
        if quarter == 4:
            end_date = period_date.replace(year=period_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_month = quarter * 3 + 1
            end_date = period_date.replace(month=end_month, day=1) - timedelta(days=1)
    else:  # Yearly
        title = f"Annual Dividend Report - {period_date.year}"
        start_date = period_date.replace(month=1, day=1)
        end_date = period_date.replace(month=12, day=31)
    
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))
    
    # Filter data for the period
    period_df = df[(df['Time'] >= start_date) & (df['Time'] <= end_date)].copy()
    
    if period_df.empty:
        story.append(Paragraph("No dividend data available for this period.", styles['Normal']))
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    
    total_dividends = period_df['Total'].sum()
    unique_stocks = period_df['Name'].nunique()
    total_transactions = len(period_df)
    avg_dividend = period_df['Total'].mean()
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Dividend Income', format_currency(total_dividends, currency)],
        ['Number of Stocks', str(unique_stocks)],
        ['Total Transactions', str(total_transactions)],
        ['Average Dividend per Transaction', format_currency(avg_dividend, currency)],
        ['Period', f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eaf6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc'))
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Top Performing Stocks
    story.append(Paragraph("Top Performing Stocks", heading_style))
    
    top_stocks = period_df.groupby('Name')['Total'].agg(['sum', 'count']).round(2)
    top_stocks.columns = ['Total Dividends', 'Transactions']
    top_stocks = top_stocks.sort_values('Total Dividends', ascending=False).head(10)
    
    top_stocks_data = [['Stock Name', 'Total Dividends', 'Transactions']]
    for stock, row in top_stocks.iterrows():
        top_stocks_data.append([
            stock[:30] + "..." if len(stock) > 30 else stock,
            format_currency(row['Total Dividends'], currency),
            str(int(row['Transactions']))
        ])
    
    top_stocks_table = Table(top_stocks_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
    top_stocks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eaf6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc'))
    ]))
    
    story.append(top_stocks_table)
    story.append(Spacer(1, 20))
    
    # Monthly Breakdown (if not monthly report)
    if period_type != "Monthly":
        story.append(Paragraph(f"{period_type} Breakdown", heading_style))
        
        if period_type == "Quarterly":
            period_df['Period'] = period_df['Time'].dt.strftime('%B %Y')
        else:  # Yearly
            period_df['Period'] = period_df['Time'].dt.strftime('%B')
        
        period_breakdown = period_df.groupby('Period')['Total'].agg(['sum', 'count']).round(2)
        period_breakdown.columns = ['Total Dividends', 'Transactions']
        
        breakdown_data = [['Period', 'Total Dividends', 'Transactions']]
        for period, row in period_breakdown.iterrows():
            breakdown_data.append([
                period,
                format_currency(row['Total Dividends'], currency),
                str(int(row['Transactions']))
            ])
        
        breakdown_table = Table(breakdown_data, colWidths=[2*inch, 1.5*inch, 1*inch])
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eaf6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc'))
        ]))
        
        story.append(breakdown_table)
        story.append(Spacer(1, 20))
    
    # Footer
    story.append(Spacer(1, 30))
    footer_text = f"Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    story.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def show_pdf_reports_tab(df: pd.DataFrame, monthly_data: pd.DataFrame, currency: str, 
                        current_date: datetime, format_currency, **kwargs):
    """Display the PDF Reports tab content."""
    
    st.title("📄 PDF Reports")
    st.markdown("Generate professional PDF reports for your dividend portfolio analysis.")
    
    # Report Type Selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        report_type = st.selectbox(
            "Report Type",
            ["Monthly", "Quarterly", "Yearly"],
            help="Select the type of report to generate"
        )
    
    with col2:
        if report_type == "Monthly":
            # Get available months from data
            available_months = df['Time'].dt.to_period('M').unique()
            available_months = sorted(available_months, reverse=True)
            
            if available_months:
                selected_period = st.selectbox(
                    "Select Month",
                    available_months,
                    format_func=lambda x: x.strftime('%B %Y'),
                    help="Select the month to generate report for"
                )
                period_date = selected_period.to_timestamp()
            else:
                st.error("No monthly data available")
                return
                
        elif report_type == "Quarterly":
            # Get available quarters
            df['Quarter'] = df['Time'].dt.to_period('Q')
            available_quarters = df['Quarter'].unique()
            available_quarters = sorted(available_quarters, reverse=True)
            
            if available_quarters:
                selected_period = st.selectbox(
                    "Select Quarter",
                    available_quarters,
                    format_func=lambda x: f"Q{x.quarter} {x.year}",
                    help="Select the quarter to generate report for"
                )
                period_date = selected_period.to_timestamp()
            else:
                st.error("No quarterly data available")
                return
                
        else:  # Yearly
            # Get available years
            available_years = sorted(df['Time'].dt.year.unique(), reverse=True)
            
            if available_years:
                selected_year = st.selectbox(
                    "Select Year",
                    available_years,
                    help="Select the year to generate report for"
                )
                period_date = datetime(selected_year, 1, 1)
            else:
                st.error("No yearly data available")
                return
    
    st.markdown("---")
    
    # Report Preview
    if st.button("📋 Preview Report Content", type="secondary"):
        with st.spinner("Generating preview..."):
            # Filter data based on selection
            if report_type == "Monthly":
                start_date = period_date.replace(day=1)
                if period_date.month == 12:
                    end_date = period_date.replace(year=period_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = period_date.replace(month=period_date.month + 1, day=1) - timedelta(days=1)
                preview_title = f"Monthly Report Preview - {period_date.strftime('%B %Y')}"
            elif report_type == "Quarterly":
                quarter = (period_date.month - 1) // 3 + 1
                start_month = (quarter - 1) * 3 + 1
                start_date = period_date.replace(month=start_month, day=1)
                if quarter == 4:
                    end_date = period_date.replace(year=period_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_month = quarter * 3 + 1
                    end_date = period_date.replace(month=end_month, day=1) - timedelta(days=1)
                preview_title = f"Quarterly Report Preview - Q{quarter} {period_date.year}"
            else:  # Yearly
                start_date = period_date.replace(month=1, day=1)
                end_date = period_date.replace(month=12, day=31)
                preview_title = f"Annual Report Preview - {period_date.year}"
            
            # Filter data
            period_df = df[(df['Time'] >= start_date) & (df['Time'] <= end_date)].copy()
            
            if period_df.empty:
                st.warning("No data available for the selected period.")
                return
            
            st.subheader(preview_title)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_dividends = period_df['Total'].sum()
                st.metric("Total Dividends", format_currency(total_dividends, currency))
            
            with col2:
                unique_stocks = period_df['Name'].nunique()
                st.metric("Unique Stocks", unique_stocks)
            
            with col3:
                total_transactions = len(period_df)
                st.metric("Transactions", total_transactions)
            
            with col4:
                avg_dividend = period_df['Total'].mean()
                st.metric("Avg per Transaction", format_currency(avg_dividend, currency))
            
            # Top performers
            st.subheader("Top Performing Stocks")
            top_stocks = period_df.groupby('Name')['Total'].agg(['sum', 'count']).round(2)
            top_stocks.columns = ['Total Dividends', 'Transactions']
            top_stocks = top_stocks.sort_values('Total Dividends', ascending=False).head(10)
            top_stocks['Total Dividends'] = top_stocks['Total Dividends'].apply(lambda x: format_currency(x, currency))
            st.dataframe(top_stocks, use_container_width=True)
    
    # Generate PDF button
    if st.button("📄 Generate PDF Report", type="primary"):
        try:
            with st.spinner("Generating PDF report..."):
                pdf_bytes = create_pdf_report(df, monthly_data, report_type, period_date, currency, format_currency)
            
            # Create download button
            filename = f"dividend_report_{report_type.lower()}_{period_date.strftime('%Y_%m')}.pdf"
            
            st.success("✅ PDF report generated successfully!")
            st.download_button(
                label="⬇️ Download PDF Report",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf"
            )
            
        except Exception as e:
            st.error(f"Error generating PDF report: {str(e)}")
            st.info("Make sure you have the required dependencies installed: `pip install reportlab`")