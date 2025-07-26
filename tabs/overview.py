import streamlit as st
import pandas as pd
import numpy as np
from utils.chart_themes import (
    create_bar_chart, 
    create_line_chart, 
    create_pie_chart, 
    create_area_chart,
    create_scatter_chart,
    COLORS
)
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show_overview_tab(
    df,
    monthly_data,
    currency,
    theme,
    current_date,
    current_year,
    current_month,
    format_currency,
    **kwargs,
):
    """
    Display the Overview tab content

    Parameters:
    -----------
    df : pandas.DataFrame
        The main dataframe with all dividend data
    monthly_data : pandas.DataFrame
        Preprocessed monthly dividend data
    currency : str
        Currency code for display (GBP, USD, EUR)
    theme : str
        UI theme (Light or Dark)
    current_date : datetime
        Current date for filtering
    current_year : int
        Current year
    current_month : int
        Current month
    format_currency : function
        Function to format currency values
    """
    # Calculate summary metrics
    total_dividends = df["Total"].sum()
    unique_stocks = df["Name"].nunique()
    current_year_dividends = df[df["Year"] == current_year]["Total"].sum()
    
    # For year-on-year comparison, exclude current year
    completed_year_df = df[df["Year"] < current_year]
    last_completed_year = current_year - 1
    second_last_completed_year = current_year - 2

    last_completed_year_total = completed_year_df[
        completed_year_df["Year"] == last_completed_year
    ]["Total"].sum()
    second_last_completed_year_total = completed_year_df[
        completed_year_df["Year"] == second_last_completed_year
    ]["Total"].sum()

    yoy_change = 0
    if second_last_completed_year_total > 0:
        yoy_change = (
            (last_completed_year_total - second_last_completed_year_total)
            / second_last_completed_year_total
        ) * 100

    # Calculate average monthly dividend
    months_with_data = df["Time"].dt.to_period("M").nunique()
    monthly_avg = total_dividends / months_with_data if months_with_data > 0 else 0
    
    # Calculate dividend yield metrics
    quarterly_payments = df[df["Time"].dt.month.isin([3, 6, 9, 12])]["Total"].sum()
    monthly_payments = df[~df["Time"].dt.month.isin([3, 6, 9, 12])]["Total"].sum()
    
    # Calculate concentration risk (top 5 stocks percentage)
    top_5_total = df.groupby("Name")["Total"].sum().nlargest(5).sum()
    concentration_risk = (top_5_total / total_dividends * 100) if total_dividends > 0 else 0

    # Key metrics in columns - Enhanced with more useful metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric(
            "Total Dividends", format_currency(total_dividends, currency), delta=None
        )

    with col2:
        st.metric(
            f"{current_year} YTD",
            format_currency(current_year_dividends, currency),
            delta=None
        )

    with col3:
        st.metric(
            f"{last_completed_year} Total",
            format_currency(last_completed_year_total, currency),
            delta=f"{yoy_change:.1f}%" if yoy_change != 0 else None,
        )

    with col4:
        st.metric("Monthly Average", format_currency(monthly_avg, currency), delta=None)

    with col5:
        st.metric("Unique Stocks", f"{unique_stocks}", delta=None)
        
    with col6:
        st.metric("Top 5 Concentration", f"{concentration_risk:.1f}%", 
                 delta="⚠️ High" if concentration_risk > 60 else "✅ Diversified")

    st.markdown("---")

    # Yearly summary chart - Excluding current year as incomplete
    yearly_totals = df.groupby("Year")["Total"].sum().reset_index()

    fig_yearly = create_bar_chart(
        yearly_totals,
        x_col="Year",
        y_col="Total",
        title="📈 Yearly Dividend Totals",
        theme=theme,
        labels={"Total": f"Dividend Amount ({currency})", "Year": "Year"},
    )

    fig_yearly.update_layout(
        height=400,
        xaxis=dict(type="category"),
        yaxis=dict(title=f"Dividend Amount ({currency})"),
    )

    st.plotly_chart(fig_yearly, use_container_width=True)
    
    # Dividend Distribution Analysis
    st.markdown("### 📊 Dividend Distribution & Analysis")
    
    # Create dividend distribution pie chart and payment frequency analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Portfolio allocation pie chart
        top_10_stocks = (
            df.groupby("Name")["Total"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        
        # Group smaller stocks into "Others"
        others_total = df.groupby("Name")["Total"].sum().sort_values(ascending=False).iloc[10:].sum()
        if others_total > 0:
            others_row = pd.DataFrame({"Name": ["Others"], "Total": [others_total]})
            pie_data = pd.concat([top_10_stocks, others_row], ignore_index=True)
        else:
            pie_data = top_10_stocks
            
        fig_pie = create_pie_chart(
            pie_data,
            values_col="Total",
            names_col="Name",
            title="💼 Portfolio Allocation (Top 10 + Others)",
            theme=theme
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Payment frequency analysis
        payment_freq = df.groupby(df["Time"].dt.month)["Total"].sum().reset_index()
        payment_freq["Month_Name"] = payment_freq["Time"].apply(
            lambda x: pd.to_datetime(f"2023-{x:02d}-01").strftime("%b")
        )
        
        fig_freq = create_bar_chart(
            payment_freq,
            x_col="Month_Name",
            y_col="Total",
            title="📅 Dividend Payments by Month",
            theme=theme,
            labels={"Total": f"Dividend Amount ({currency})", "Month_Name": "Month"},
        )
        fig_freq.update_layout(height=400)
        st.plotly_chart(fig_freq, use_container_width=True)
    
    # Dividend Growth Analysis
    st.markdown("### 📈 Growth & Performance Analysis")
    
    # Split the next section into two columns
    col1, col2 = st.columns(2)

    with col1:
        # Top dividend stocks
        top_stocks = (
            df.groupby("Name")["Total"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        fig_top_stocks = create_bar_chart(
            top_stocks,
            y_col="Name",
            x_col="Total",
            title="🏆 Top 10 Dividend Stocks",
            theme=theme,
            orientation="h",
            labels={"Total": f"Dividend Amount ({currency})", "Name": "Stock"},
        )

        fig_top_stocks.update_layout(
            height=500, yaxis=dict(categoryorder="total ascending")
        )

        st.plotly_chart(fig_top_stocks, use_container_width=True)

    with col2:
        # Recent monthly trend - excluding current month
        recent_data = monthly_data[
            (monthly_data["Time"].dt.year < current_year)
            | (
                (monthly_data["Time"].dt.year == current_year)
                & (monthly_data["Time"].dt.month < current_month)
            )
        ]
        recent_data = recent_data.sort_values("Time").tail(12)  # Last 12 months

        fig_recent = create_line_chart(
            recent_data,
            x_col="Time",
            y_col="Total_Sum",
            title="📊 Recent Dividend Trend (Last 12 Months)",
            theme=theme,
            labels={"Total_Sum": f"Dividend Amount ({currency})", "Time": "Month"},
        )

        fig_recent.update_layout(
            height=500,
            xaxis=dict(title="Month", tickangle=-45, tickformat="%b %Y"),
            yaxis=dict(title=f"Dividend Amount ({currency})"),
        )

        st.plotly_chart(fig_recent, use_container_width=True)
    
    # TTM Dividend Yield Calculator
    st.markdown("### 💰 Trailing Twelve Months (TTM) Dividend Yield Calculator")
    
    # Calculate TTM dividends
    twelve_months_ago = current_date - pd.DateOffset(months=12)
    ttm_dividends = df[df["Time"] >= twelve_months_ago]["Total"].sum()
    
    # Create two columns for the calculator
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📊 TTM Dividend Calculation")
        st.metric("Trailing 12-Month Dividends", format_currency(ttm_dividends, currency))
        
        # Show the calculation formula
        st.markdown("**Formula:**")
        st.latex(r"\text{Dividend Yield} = \frac{\text{TTM Dividends}}{\text{Portfolio Value}} \times 100")
        
        # TTM breakdown by quarter
        quarters_data = []
        for i in range(4):
            quarter_start = current_date - pd.DateOffset(months=(i+1)*3)
            quarter_end = current_date - pd.DateOffset(months=i*3)
            quarter_dividends = df[
                (df["Time"] >= quarter_start) & (df["Time"] < quarter_end)
            ]["Total"].sum()
            quarters_data.append({
                "Quarter": f"Q{4-i} ({quarter_start.strftime('%Y')})",
                "Dividends": quarter_dividends
            })
        
        ttm_breakdown = pd.DataFrame(quarters_data)
        
        fig_ttm = create_bar_chart(
            ttm_breakdown,
            x_col="Quarter",
            y_col="Dividends",
            title="📅 TTM Quarterly Breakdown",
            theme=theme,
            labels={"Dividends": f"Dividend Amount ({currency})", "Quarter": "Quarter"},
        )
        fig_ttm.update_layout(height=300)
        st.plotly_chart(fig_ttm, use_container_width=True)
    
    with col2:
        st.markdown("#### 💼 Portfolio Yield Calculator")
        
        # User input for portfolio value
        portfolio_value = st.number_input(
            f"Enter your current portfolio value ({currency}):",
            min_value=0.0,
            value=100000.0,
            step=1000.0,
            format="%.2f",
            help="Enter the total current market value of your dividend-paying portfolio"
        )
        
        # Calculate dividend yield
        if portfolio_value > 0:
            dividend_yield = (ttm_dividends / portfolio_value) * 100
            
            # Display results
            st.metric(
                "Current Dividend Yield",
                f"{dividend_yield:.2f}%",
                delta=f"vs avg 4% yield" if dividend_yield != 4.0 else None
            )
            
            # Yield comparison and insights
            if dividend_yield < 2.0:
                st.info("🔵 **Low Yield**: Consider growth-focused strategy or seek higher-yielding opportunities.")
            elif dividend_yield < 4.0:
                st.success("🟢 **Moderate Yield**: Well-balanced dividend portfolio.")
            elif dividend_yield < 6.0:
                st.warning("🟡 **High Yield**: Strong income generation, monitor sustainability.")
            else:
                st.error("🔴 **Very High Yield**: Exceptional income but verify dividend safety.")
            
            # Additional calculations
            st.markdown("#### 📈 Projections")
            
            projected_annual = ttm_dividends
            projected_monthly = ttm_dividends / 12
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Projected Annual Income", format_currency(projected_annual, currency))
            with col_b:
                st.metric("Projected Monthly Income", format_currency(projected_monthly, currency))
                
            # Show yield on cost if we assume current yield continues
            st.markdown("**Key Insights:**")
            st.write(f"• Your portfolio generates {format_currency(projected_monthly, currency)} per month")
            st.write(f"• At current yield of {dividend_yield:.2f}%, your dividends could buy {format_currency(ttm_dividends / dividend_yield * 100, currency)} worth of new investments annually")
            st.write(f"• To reach {format_currency(projected_monthly * 1.1, currency)}/month (+10%), you need {format_currency(portfolio_value * 0.1, currency)} more capital at current yield")
        else:
            st.info("Enter your portfolio value above to calculate dividend yield and projections.")
    
    # Summary Statistics Table
    st.markdown("### 📋 Portfolio Summary Statistics")
    
    # Calculate additional statistics
    stats_data = {
        "Metric": [
            "Total Portfolio Value (Dividends)",
            "Average Dividend per Stock",
            "Median Dividend per Stock",
            "Standard Deviation",
            "Coefficient of Variation",
            "Total Payments Received",
            "Average Payment Size",
            "Largest Single Payment",
            "Most Productive Month",
            "Least Productive Month"
        ],
        "Value": [
            format_currency(total_dividends, currency),
            format_currency(df.groupby("Name")["Total"].sum().mean(), currency),
            format_currency(df.groupby("Name")["Total"].sum().median(), currency),
            format_currency(df.groupby("Name")["Total"].sum().std(), currency),
            f"{(df.groupby('Name')['Total'].sum().std() / df.groupby('Name')['Total'].sum().mean()):.2f}",
            f"{len(df):,}",
            format_currency(df["Total"].mean(), currency),
            format_currency(df["Total"].max(), currency),
            monthly_data.loc[monthly_data["Total_Sum"].idxmax(), "Time"].strftime("%B %Y") if len(monthly_data) > 0 else "N/A",
            monthly_data.loc[monthly_data["Total_Sum"].idxmin(), "Time"].strftime("%B %Y") if len(monthly_data) > 0 else "N/A"
        ]
    }
    
    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True, hide_index=True)
