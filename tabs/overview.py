import streamlit as st
import pandas as pd
import plotly.express as px
from utils.chart_themes import create_bar_chart, apply_chart_theme, create_line_chart

def show_overview_tab(df, monthly_data, currency, theme, current_date, current_year, current_month, format_currency, **kwargs):
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
    total_dividends = df['Total'].sum()
    unique_stocks = df['Name'].nunique()
    
    # For year-on-year comparison, exclude current year
    completed_year_df = df[df['Year'] < current_year]
    last_completed_year = current_year - 1
    second_last_completed_year = current_year - 2
    
    last_completed_year_total = completed_year_df[completed_year_df['Year'] == last_completed_year]['Total'].sum()
    second_last_completed_year_total = completed_year_df[completed_year_df['Year'] == second_last_completed_year]['Total'].sum()
    
    yoy_change = 0
    if second_last_completed_year_total > 0:
        yoy_change = ((last_completed_year_total - second_last_completed_year_total) / second_last_completed_year_total) * 100
    
    # Calculate average monthly dividend
    months_with_data = df['Time'].dt.to_period('M').nunique()
    monthly_avg = total_dividends / months_with_data if months_with_data > 0 else 0
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Dividends",
            format_currency(total_dividends, currency),
            delta=None
        )
        
    with col2:
        st.metric(
            f"{last_completed_year} Total",
            format_currency(last_completed_year_total, currency),
            delta=f"{yoy_change:.1f}%" if yoy_change != 0 else None
        )
        
    with col3:
        st.metric(
            "Monthly Average",
            format_currency(monthly_avg, currency),
            delta=None
        )
        
    with col4:
        st.metric(
            "Unique Stocks",
            f"{unique_stocks}",
            delta=None
        )
    
    st.markdown("---")
    
    # Yearly summary chart - Excluding current year as incomplete
    yearly_totals = df.groupby('Year')['Total'].sum().reset_index()
    
    fig_yearly = create_bar_chart(
        yearly_totals,
        x_col='Year',
        y_col='Total',
        title="📈 Yearly Dividend Totals",
        theme=theme,
        labels={"Total": f"Dividend Amount ({currency})", "Year": "Year"}
    )
    
    fig_yearly.update_layout(
        height=400,
        xaxis=dict(type='category'),
        yaxis=dict(title=f"Dividend Amount ({currency})")
    )
    
    st.plotly_chart(fig_yearly, use_container_width=True)
    
    # Split the next section into two columns
    col1, col2 = st.columns(2)
    
    with col1:
        # Top dividend stocks
        top_stocks = df.groupby('Name')['Total'].sum().sort_values(ascending=False).head(10).reset_index()
        
        fig_top_stocks = create_bar_chart(
            top_stocks,
            y_col='Name',
            x_col='Total',
            title="🏆 Top 10 Dividend Stocks",
            theme=theme,
            orientation='h',
            labels={"Total": f"Dividend Amount ({currency})", "Name": "Stock"}
        )
        
        fig_top_stocks.update_layout(
            height=500,
            yaxis=dict(categoryorder='total ascending')
        )
        
        st.plotly_chart(fig_top_stocks, use_container_width=True)
    
    with col2:
        # Recent monthly trend - excluding current month
        recent_data = monthly_data[
            (monthly_data['Time'].dt.year < current_year) | 
            ((monthly_data['Time'].dt.year == current_year) & 
             (monthly_data['Time'].dt.month < current_month))
        ]
        recent_data = recent_data.sort_values('Time').tail(12)  # Last 12 months
        
        fig_recent = create_line_chart(
            recent_data,
            x_col='Time',
            y_col='Total_Sum',
            title="📊 Recent Dividend Trend (Last 12 Months)",
            theme=theme,
            labels={"Total_Sum": f"Dividend Amount ({currency})", "Time": "Month"}
        )
        
        fig_recent.update_layout(
            height=500,
            xaxis=dict(
                title="Month",
                tickangle=-45,
                tickformat="%b %Y"
            ),
            yaxis=dict(title=f"Dividend Amount ({currency})")
        )
        
        st.plotly_chart(fig_recent, use_container_width=True)