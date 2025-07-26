"""Dividend Screener Tab Module.

This module provides functionality for screening dividend stocks
using Alpha Vantage API data with comprehensive analysis tools.
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json

from config import AppConfig, load_config
from utils import handle_api_error, create_loading_spinner, validate_dataframe

def rate_limit(delay: float = None) -> None:
    """Add delay between API calls to respect rate limits.
    
    Args:
        delay: Custom delay in seconds, uses config default if None
    """
    config = load_config()
    time.sleep(delay or config.api_rate_limit_delay)

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, handling None and string 'None'.
    
    Args:
        value: Value to convert to float
        default: Default value if conversion fails
        
    Returns:
        Float value or default if conversion fails
    """
    if value is None or value == 'None' or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

@st.cache_data(ttl=3600, show_spinner="Fetching company overview...")
def get_company_overview(symbol: str) -> Optional[Dict[str, Any]]:
    """Get company overview data from Alpha Vantage.
    
    Args:
        symbol: Stock symbol to fetch data for
        
    Returns:
        Dictionary containing company overview data or None if failed
    """
    config = load_config()
    
    try:
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol.upper(),
            'apikey': config.alpha_vantage_api_key
        }
        
        rate_limit()
        response = requests.get(config.api_base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'Symbol' in data and data.get('Symbol'):
            return data
        elif 'Error Message' in data:
            st.error(f"API Error: {data['Error Message']}")
            return None
        elif 'Note' in data:
            st.warning(f"API Notice: {data['Note']}")
            return None
        else:
            st.warning(f"No data found for symbol: {symbol}")
            return None
            
    except requests.exceptions.RequestException as e:
        handle_api_error(e, f"Company overview fetch for {symbol}")
        return None
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=3600, show_spinner="Fetching dividend data...")
def get_dividend_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Get dividend data from Alpha Vantage.
    
    Args:
        symbol: Stock symbol to fetch dividend data for
        
    Returns:
        Dictionary containing dividend time series data or None if failed
    """
    config = load_config()
    
    try:
        params = {
            'function': 'TIME_SERIES_MONTHLY_ADJUSTED',
            'symbol': symbol.upper(),
            'apikey': config.alpha_vantage_api_key
        }
        
        rate_limit()
        response = requests.get(config.api_base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'Monthly Adjusted Time Series' in data:
            return data['Monthly Adjusted Time Series']
        else:
            return None
            
    except Exception as e:
        st.error(f"Error fetching dividend data for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=3600, show_spinner="Fetching price data...")
def get_daily_price_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Get daily price data from Alpha Vantage.
    
    Args:
        symbol: Stock symbol to fetch price data for
        
    Returns:
        Dictionary containing daily price time series data or None if failed
    """
    config = load_config()
    
    try:
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol.upper(),
            'apikey': config.alpha_vantage_api_key,
            'outputsize': 'full'
        }
        
        rate_limit()
        response = requests.get(config.api_base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'Time Series (Daily)' in data:
            return data['Time Series (Daily)']
        else:
            return None
            
    except Exception as e:
        st.error(f"Error fetching daily price data for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_income_statement(symbol):
    """Get income statement data from Alpha Vantage"""
    try:
        config = load_config()
        params = {
            'function': 'INCOME_STATEMENT',
            'symbol': symbol,
            'apikey': config.alpha_vantage_api_key
        }
        
        rate_limit()
        response = requests.get(config.api_base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'annualReports' in data:
            return data['annualReports']
        else:
            return None
            
    except Exception as e:
        st.error(f"Error fetching income statement for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_balance_sheet(symbol):
    """Get balance sheet data from Alpha Vantage"""
    try:
        config = load_config()
        params = {
            'function': 'BALANCE_SHEET',
            'symbol': symbol,
            'apikey': config.alpha_vantage_api_key
        }
        
        rate_limit()
        response = requests.get(config.api_base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'annualReports' in data:
            return data['annualReports']
        else:
            return None
            
    except Exception as e:
        st.error(f"Error fetching balance sheet for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_cash_flow(symbol):
    """Get cash flow statement data from Alpha Vantage"""
    try:
        config = load_config()
        params = {
            'function': 'CASH_FLOW',
            'symbol': symbol,
            'apikey': config.alpha_vantage_api_key
        }
        
        rate_limit()
        response = requests.get(config.api_base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'annualReports' in data:
            return data['annualReports']
        else:
            return None
            
    except Exception as e:
        st.error(f"Error fetching cash flow for {symbol}: {str(e)}")
        return None

def process_dividend_history(dividend_data, daily_price_data, overview_data):
    """Process dividend data into useful formats for analysis with proper yield calculation"""
    if not dividend_data:
        return None, None, None, None
    
    dividend_records = []
    for date, data in dividend_data.items():
        dividend_amount = safe_float(data.get('7. dividend amount', 0))
        if dividend_amount > 0:
            dividend_records.append({
                'date': pd.to_datetime(date),
                'dividend': dividend_amount,
                'year': pd.to_datetime(date).year,
                'quarter': pd.to_datetime(date).quarter
            })
    
    if not dividend_records:
        return None, None, None, None
    
    df = pd.DataFrame(dividend_records).sort_values('date')
    
    # Calculate annual dividends
    annual_dividends = df.groupby('year')['dividend'].sum().reset_index()
    annual_dividends['date'] = pd.to_datetime(annual_dividends['year'], format='%Y')
    
    # Calculate quarterly dividends
    df['year_quarter'] = df['year'].astype(str) + ' Q' + df['quarter'].astype(str)
    quarterly_dividends = df.groupby(['year', 'quarter', 'year_quarter'])['dividend'].sum().reset_index()
    quarterly_dividends['date'] = pd.to_datetime(quarterly_dividends['year'].astype(str) + '-' + 
                                                (quarterly_dividends['quarter'] * 3).astype(str) + '-01')
    
    # Calculate dividend yield over time using daily prices and trailing 12-month dividends
    yield_data = []
    if daily_price_data:
        # Sort dividend data by date
        df_sorted = df.sort_values('date')
        
        for date_str, price_info in daily_price_data.items():
            price_date = pd.to_datetime(date_str)
            closing_price = safe_float(price_info.get('4. close', 0))
            
            if closing_price > 0:
                # Calculate trailing 12-month dividends from this date
                twelve_months_ago = price_date - pd.DateOffset(months=12)
                trailing_dividends = df_sorted[
                    (df_sorted['date'] > twelve_months_ago) & 
                    (df_sorted['date'] <= price_date)
                ]['dividend'].sum()
                
                if trailing_dividends > 0:
                    dividend_yield = (trailing_dividends / closing_price) * 100
                    yield_data.append({
                        'date': price_date,
                        'price': closing_price,
                        'trailing_12m_dividends': trailing_dividends,
                        'dividend_yield': dividend_yield
                    })
    
    # Create yield dataframe
    yield_df = pd.DataFrame(yield_data).sort_values('date') if yield_data else None
    
    # Add estimated yield to original df (fallback calculation)
    current_price = safe_float(overview_data.get('Price', 0))
    if current_price > 0:
        df['estimated_yield'] = (df['dividend'] * 4 / current_price) * 100  # Rough quarterly estimate
        annual_dividends['estimated_yield'] = (annual_dividends['dividend'] / current_price) * 100
    else:
        df['estimated_yield'] = 0
        annual_dividends['estimated_yield'] = 0
    
    return df, annual_dividends, quarterly_dividends, yield_df

def calculate_financial_metrics(overview_data, income_data, balance_data, cash_flow_data):
    """Calculate comprehensive financial metrics"""
    metrics = {}
    
    try:
        # Basic company info
        metrics['symbol'] = overview_data.get('Symbol', 'N/A')
        metrics['name'] = overview_data.get('Name', 'N/A')
        metrics['sector'] = overview_data.get('Sector', 'N/A')
        metrics['industry'] = overview_data.get('Industry', 'N/A')
        metrics['description'] = overview_data.get('Description', 'N/A')
        metrics['exchange'] = overview_data.get('Exchange', 'N/A')
        metrics['currency'] = overview_data.get('Currency', 'USD')
        
        # Market data
        metrics['market_cap'] = safe_float(overview_data.get('MarketCapitalization', 0))
        metrics['shares_outstanding'] = safe_float(overview_data.get('SharesOutstanding', 0))
        metrics['current_price'] = safe_float(overview_data.get('Price', 0))
        metrics['52_week_high'] = safe_float(overview_data.get('52WeekHigh', 0))
        metrics['52_week_low'] = safe_float(overview_data.get('52WeekLow', 0))
        
        # Dividend metrics
        metrics['dividend_yield'] = safe_float(overview_data.get('DividendYield', 0)) * 100
        metrics['dividend_per_share'] = safe_float(overview_data.get('DividendPerShare', 0))
        metrics['ex_dividend_date'] = overview_data.get('ExDividendDate', 'N/A')
        metrics['dividend_date'] = overview_data.get('DividendDate', 'N/A')
        
        # Financial ratios
        metrics['pe_ratio'] = safe_float(overview_data.get('PERatio', 0))
        metrics['peg_ratio'] = safe_float(overview_data.get('PEGRatio', 0))
        metrics['pb_ratio'] = safe_float(overview_data.get('PriceToBookRatio', 0))
        metrics['price_to_sales'] = safe_float(overview_data.get('PriceToSalesRatioTTM', 0))
        metrics['ev_revenue'] = safe_float(overview_data.get('EVToRevenue', 0))
        metrics['ev_ebitda'] = safe_float(overview_data.get('EVToEBITDA', 0))
        
        # Profitability metrics
        metrics['profit_margin'] = safe_float(overview_data.get('ProfitMargin', 0)) * 100
        metrics['operating_margin'] = safe_float(overview_data.get('OperatingMarginTTM', 0)) * 100
        metrics['roe'] = safe_float(overview_data.get('ReturnOnEquityTTM', 0)) * 100
        metrics['roa'] = safe_float(overview_data.get('ReturnOnAssetsTTM', 0)) * 100
        
        # Growth metrics
        metrics['revenue_growth_yoy'] = safe_float(overview_data.get('QuarterlyRevenueGrowthYOY', 0)) * 100
        metrics['earnings_growth_yoy'] = safe_float(overview_data.get('QuarterlyEarningsGrowthYOY', 0)) * 100
        
        # Financial strength
        metrics['current_ratio'] = safe_float(overview_data.get('CurrentRatio', 0))
        metrics['quick_ratio'] = safe_float(overview_data.get('QuickRatio', 0))
        metrics['debt_to_equity'] = safe_float(overview_data.get('DebtToEquityRatio', 0))
        metrics['book_value'] = safe_float(overview_data.get('BookValue', 0))
        
        # TTM financials
        metrics['revenue_ttm'] = safe_float(overview_data.get('RevenueTTM', 0))
        metrics['gross_profit_ttm'] = safe_float(overview_data.get('GrossProfitTTM', 0))
        metrics['ebitda'] = safe_float(overview_data.get('EBITDA', 0))
        
        # Payout ratio calculation
        eps = safe_float(overview_data.get('EPS', 0))
        if eps > 0 and metrics['dividend_per_share'] > 0:
            metrics['payout_ratio'] = (metrics['dividend_per_share'] / eps) * 100
        else:
            metrics['payout_ratio'] = 0
        
        # Additional metrics from financial statements
        if income_data and len(income_data) > 0:
            latest_income = income_data[0]  # Most recent year
            metrics['total_revenue'] = safe_float(latest_income.get('totalRevenue', 0))
            metrics['net_income'] = safe_float(latest_income.get('netIncome', 0))
            metrics['operating_income'] = safe_float(latest_income.get('operatingIncome', 0))
            metrics['interest_expense'] = safe_float(latest_income.get('interestExpense', 0))
        
        if cash_flow_data and len(cash_flow_data) > 0:
            latest_cf = cash_flow_data[0]  # Most recent year
            metrics['operating_cash_flow'] = safe_float(latest_cf.get('operatingCashflow', 0))
            metrics['free_cash_flow'] = safe_float(latest_cf.get('operatingCashflow', 0)) - safe_float(latest_cf.get('capitalExpenditures', 0))
            metrics['capital_expenditures'] = safe_float(latest_cf.get('capitalExpenditures', 0))
            metrics['dividends_paid'] = abs(safe_float(latest_cf.get('dividendPayout', 0)))
        
    except Exception as e:
        st.error(f"Error calculating metrics: {str(e)}")
    
    return metrics

def show_dividend_screener_tab(df, monthly_data, currency, theme, current_date, current_year, current_month, format_currency, **kwargs):
    """
    Display the Dividend Analyzer tab content
    """
    st.subheader("📊 Dividend Stock Analyzer")
    st.markdown("Comprehensive dividend analysis using Alpha Vantage data with detailed financial metrics and visualizations")
    
    # Stock input section
    col1, col2 = st.columns([3, 1])
    
    with col1:
        symbol = st.text_input(
            "Enter stock symbol for analysis", 
            value="AAPL",
            help="Enter any US stock symbol (e.g., AAPL, MSFT, JNJ, KO)"
        ).upper()
    
    with col2:
        time_period = st.selectbox(
            "Analysis Period",
            ["5 Years", "3 Years", "All Available"],
            index=0
        )
    
    if st.button("🔍 Analyze Stock", type="primary"):
        if symbol:
            with st.spinner(f"Fetching comprehensive data for {symbol}..."):
                # Fetch all data
                overview = get_company_overview(symbol)
                dividend_data = get_dividend_data(symbol)
                daily_price_data = get_daily_price_data(symbol)
                income_data = get_income_statement(symbol)
                balance_data = get_balance_sheet(symbol)
                cash_flow_data = get_cash_flow(symbol)
                
                if overview:
                    # Calculate metrics
                    metrics = calculate_financial_metrics(overview, income_data, balance_data, cash_flow_data)
                    
                    # Process dividend history with proper yield calculation
                    div_history, annual_divs, quarterly_divs, yield_df = process_dividend_history(dividend_data, daily_price_data, overview)
                    
                    # Filter data based on time period
                    current_year = datetime.now().year
                    if time_period == "5 Years":
                        cutoff_year = current_year - 5
                    elif time_period == "3 Years":
                        cutoff_year = current_year - 3
                    else:
                        cutoff_year = 1900  # All available
                    
                    # Company Profile Section
                    st.markdown("---")
                    st.subheader(f"📋 Company Profile: {metrics['name']} ({metrics['symbol']})")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Market Cap", f"${metrics['market_cap']/1e9:.2f}B" if metrics['market_cap'] > 0 else "N/A")
                        st.metric("Current Price", f"${metrics['current_price']:.2f}" if metrics['current_price'] > 0 else "N/A")
                    
                    with col2:
                        st.metric("Dividend Yield", f"{metrics['dividend_yield']:.2f}%" if metrics['dividend_yield'] > 0 else "N/A")
                        st.metric("P/E Ratio", f"{metrics['pe_ratio']:.2f}" if metrics['pe_ratio'] > 0 else "N/A")
                    
                    with col3:
                        st.metric("Payout Ratio", f"{metrics['payout_ratio']:.1f}%" if metrics['payout_ratio'] > 0 else "N/A")
                        st.metric("ROE", f"{metrics['roe']:.2f}%" if metrics['roe'] > 0 else "N/A")
                    
                    with col4:
                        st.metric("Debt/Equity", f"{metrics['debt_to_equity']:.2f}" if metrics['debt_to_equity'] > 0 else "N/A")
                        st.metric("Current Ratio", f"{metrics['current_ratio']:.2f}" if metrics['current_ratio'] > 0 else "N/A")
                    
                    # Company details
                    with st.expander("📊 Detailed Company Information"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Sector:** {metrics['sector']}")
                            st.write(f"**Industry:** {metrics['industry']}")
                            st.write(f"**Exchange:** {metrics['exchange']}")
                            st.write(f"**Currency:** {metrics['currency']}")
                            st.write(f"**Shares Outstanding:** {metrics['shares_outstanding']:,.0f}" if metrics['shares_outstanding'] > 0 else "**Shares Outstanding:** N/A")
                        
                        with col2:
                            st.write(f"**52 Week High:** ${metrics['52_week_high']:.2f}" if metrics['52_week_high'] > 0 else "**52 Week High:** N/A")
                            st.write(f"**52 Week Low:** ${metrics['52_week_low']:.2f}" if metrics['52_week_low'] > 0 else "**52 Week Low:** N/A")
                            st.write(f"**Ex-Dividend Date:** {metrics['ex_dividend_date']}")
                            st.write(f"**Dividend Date:** {metrics['dividend_date']}")
                            st.write(f"**Book Value:** ${metrics['book_value']:.2f}" if metrics['book_value'] > 0 else "**Book Value:** N/A")
                        
                        if metrics['description'] != 'N/A':
                            st.write("**Company Description:**")
                            st.write(metrics['description'][:500] + "..." if len(metrics['description']) > 500 else metrics['description'])
                    
                    # Create tabs for detailed analysis
                    analysis_tabs = st.tabs(["📊 Income Statement", "⚖️ Balance Sheet", "💰 Cash Flow", "💎 Dividend Info"])
                    
                    # Tab 1: Income Statement
                    with analysis_tabs[0]:
                        st.subheader("📊 Income Statement Analysis")
                        
                        if income_data and len(income_data) > 0:
                            # Process income statement data for charts
                            income_chart_data = []
                            for report in income_data:
                                fiscal_year = report.get('fiscalDateEnding', '')[:4]
                                if fiscal_year and int(fiscal_year) >= cutoff_year:
                                    income_chart_data.append({
                                        'year': int(fiscal_year),
                                        'total_revenue': safe_float(report.get('totalRevenue', 0)) / 1e9,
                                        'gross_profit': safe_float(report.get('grossProfit', 0)) / 1e9,
                                        'operating_income': safe_float(report.get('operatingIncome', 0)) / 1e9,
                                        'net_income': safe_float(report.get('netIncome', 0)) / 1e9,
                                        'ebitda': safe_float(report.get('ebitda', 0)) / 1e9
                                    })
                            
                            if income_chart_data:
                                income_df = pd.DataFrame(income_chart_data).sort_values('year')
                                
                                # Revenue and Profitability Chart
                                fig_income = go.Figure()
                                
                                fig_income.add_trace(go.Bar(
                                    x=income_df['year'],
                                    y=income_df['total_revenue'],
                                    name='Total Revenue',
                                    marker_color='#4e8df5'
                                ))
                                
                                fig_income.add_trace(go.Scatter(
                                    x=income_df['year'],
                                    y=income_df['gross_profit'],
                                    mode='lines+markers',
                                    name='Gross Profit',
                                    line=dict(color='#22c55e', width=3),
                                    yaxis='y2'
                                ))
                                
                                fig_income.add_trace(go.Scatter(
                                    x=income_df['year'],
                                    y=income_df['net_income'],
                                    mode='lines+markers',
                                    name='Net Income',
                                    line=dict(color='#f59e0b', width=3),
                                    yaxis='y2'
                                ))
                                
                                fig_income.update_layout(
                                    title=f"Revenue and Profitability - {symbol}",
                                    xaxis_title="Year",
                                    yaxis=dict(title="Revenue ($ Billions)", side="left"),
                                    yaxis2=dict(title="Profit ($ Billions)", side="right", overlaying="y"),
                                    template="plotly_white" if theme == "Light" else "plotly_dark",
                                    height=500,
                                    hovermode='x unified'
                                )
                                
                                st.plotly_chart(fig_income, use_container_width=True)
                                
                                # Margin Analysis
                                margin_data = []
                                for _, row in income_df.iterrows():
                                    if row['total_revenue'] > 0:
                                        margin_data.append({
                                            'year': row['year'],
                                            'gross_margin': (row['gross_profit'] / row['total_revenue']) * 100,
                                            'operating_margin': (row['operating_income'] / row['total_revenue']) * 100,
                                            'net_margin': (row['net_income'] / row['total_revenue']) * 100
                                        })
                                
                                if margin_data:
                                    margin_df = pd.DataFrame(margin_data)
                                    
                                    fig_margins = go.Figure()
                                    
                                    fig_margins.add_trace(go.Scatter(
                                        x=margin_df['year'],
                                        y=margin_df['gross_margin'],
                                        mode='lines+markers',
                                        name='Gross Margin',
                                        line=dict(color='#4e8df5', width=3)
                                    ))
                                    
                                    fig_margins.add_trace(go.Scatter(
                                        x=margin_df['year'],
                                        y=margin_df['operating_margin'],
                                        mode='lines+markers',
                                        name='Operating Margin',
                                        line=dict(color='#22c55e', width=3)
                                    ))
                                    
                                    fig_margins.add_trace(go.Scatter(
                                        x=margin_df['year'],
                                        y=margin_df['net_margin'],
                                        mode='lines+markers',
                                        name='Net Margin',
                                        line=dict(color='#f59e0b', width=3)
                                    ))
                                    
                                    fig_margins.update_layout(
                                        title=f"Profit Margins Over Time - {symbol}",
                                        xaxis_title="Year",
                                        yaxis_title="Margin (%)",
                                        template="plotly_white" if theme == "Light" else "plotly_dark",
                                        height=400,
                                        hovermode='x unified'
                                    )
                                    
                                    st.plotly_chart(fig_margins, use_container_width=True)
                                
                                # Income Statement Table
                                st.subheader("Income Statement Summary")
                                display_income_df = income_df.copy()
                                display_income_df = display_income_df.round(2)
                                display_income_df = display_income_df.rename(columns={
                                    'year': 'Year',
                                    'total_revenue': 'Revenue ($B)',
                                    'gross_profit': 'Gross Profit ($B)',
                                    'operating_income': 'Operating Income ($B)',
                                    'net_income': 'Net Income ($B)',
                                    'ebitda': 'EBITDA ($B)'
                                })
                                st.dataframe(display_income_df, use_container_width=True)
                        else:
                            st.warning("No income statement data available")
                    
                    # Tab 2: Balance Sheet
                    with analysis_tabs[1]:
                        st.subheader("⚖️ Balance Sheet Analysis")
                        
                        if balance_data and len(balance_data) > 0:
                            # Process balance sheet data
                            balance_chart_data = []
                            for report in balance_data:
                                fiscal_year = report.get('fiscalDateEnding', '')[:4]
                                if fiscal_year and int(fiscal_year) >= cutoff_year:
                                    balance_chart_data.append({
                                        'year': int(fiscal_year),
                                        'total_assets': safe_float(report.get('totalAssets', 0)) / 1e9,
                                        'total_liabilities': safe_float(report.get('totalLiabilities', 0)) / 1e9,
                                        'shareholders_equity': safe_float(report.get('totalShareholderEquity', 0)) / 1e9,
                                        'current_assets': safe_float(report.get('totalCurrentAssets', 0)) / 1e9,
                                        'current_liabilities': safe_float(report.get('totalCurrentLiabilities', 0)) / 1e9,
                                        'long_term_debt': safe_float(report.get('longTermDebt', 0)) / 1e9,
                                        'cash': safe_float(report.get('cashAndCashEquivalentsAtCarryingValue', 0)) / 1e9
                                    })
                            
                            if balance_chart_data:
                                balance_df = pd.DataFrame(balance_chart_data).sort_values('year')
                                
                                # Assets vs Liabilities Chart
                                fig_balance = go.Figure()
                                
                                fig_balance.add_trace(go.Bar(
                                    x=balance_df['year'],
                                    y=balance_df['total_assets'],
                                    name='Total Assets',
                                    marker_color='#4e8df5'
                                ))
                                
                                fig_balance.add_trace(go.Bar(
                                    x=balance_df['year'],
                                    y=balance_df['total_liabilities'],
                                    name='Total Liabilities',
                                    marker_color='#ef4444'
                                ))
                                
                                fig_balance.add_trace(go.Bar(
                                    x=balance_df['year'],
                                    y=balance_df['shareholders_equity'],
                                    name='Shareholders Equity',
                                    marker_color='#22c55e'
                                ))
                                
                                fig_balance.update_layout(
                                    title=f"Balance Sheet Overview - {symbol}",
                                    xaxis_title="Year",
                                    yaxis_title="Amount ($ Billions)",
                                    template="plotly_white" if theme == "Light" else "plotly_dark",
                                    height=500,
                                    barmode='group'
                                )
                                
                                st.plotly_chart(fig_balance, use_container_width=True)
                                
                                # Debt Analysis
                                fig_debt = go.Figure()
                                
                                fig_debt.add_trace(go.Scatter(
                                    x=balance_df['year'],
                                    y=balance_df['long_term_debt'],
                                    mode='lines+markers',
                                    name='Long-term Debt',
                                    line=dict(color='#ef4444', width=3)
                                ))
                                
                                fig_debt.add_trace(go.Scatter(
                                    x=balance_df['year'],
                                    y=balance_df['cash'],
                                    mode='lines+markers',
                                    name='Cash & Equivalents',
                                    line=dict(color='#22c55e', width=3)
                                ))
                                
                                # Calculate net debt
                                balance_df['net_debt'] = balance_df['long_term_debt'] - balance_df['cash']
                                fig_debt.add_trace(go.Scatter(
                                    x=balance_df['year'],
                                    y=balance_df['net_debt'],
                                    mode='lines+markers',
                                    name='Net Debt',
                                    line=dict(color='#f59e0b', width=3, dash='dash')
                                ))
                                
                                fig_debt.update_layout(
                                    title=f"Debt Analysis - {symbol}",
                                    xaxis_title="Year",
                                    yaxis_title="Amount ($ Billions)",
                                    template="plotly_white" if theme == "Light" else "plotly_dark",
                                    height=400,
                                    hovermode='x unified'
                                )
                                
                                st.plotly_chart(fig_debt, use_container_width=True)
                                
                                # Balance Sheet Table
                                st.subheader("Balance Sheet Summary")
                                display_balance_df = balance_df.copy()
                                display_balance_df = display_balance_df.round(2)
                                display_balance_df = display_balance_df.rename(columns={
                                    'year': 'Year',
                                    'total_assets': 'Total Assets ($B)',
                                    'total_liabilities': 'Total Liabilities ($B)',
                                    'shareholders_equity': 'Shareholders Equity ($B)',
                                    'current_assets': 'Current Assets ($B)',
                                    'current_liabilities': 'Current Liabilities ($B)',
                                    'long_term_debt': 'Long-term Debt ($B)',
                                    'cash': 'Cash ($B)'
                                })
                                st.dataframe(display_balance_df, use_container_width=True)
                        else:
                            st.warning("No balance sheet data available")
                    
                    # Tab 3: Cash Flow
                    with analysis_tabs[2]:
                        st.subheader("💰 Cash Flow Analysis")
                        
                        if cash_flow_data and len(cash_flow_data) > 0:
                            # Process cash flow data
                            cf_chart_data = []
                            for report in cash_flow_data:
                                fiscal_year = report.get('fiscalDateEnding', '')[:4]
                                if fiscal_year and int(fiscal_year) >= cutoff_year:
                                    operating_cf = safe_float(report.get('operatingCashflow', 0))
                                    capex = safe_float(report.get('capitalExpenditures', 0))
                                    free_cf = operating_cf + capex  # capex is usually negative
                                    
                                    cf_chart_data.append({
                                        'year': int(fiscal_year),
                                        'operating_cash_flow': operating_cf / 1e9,
                                        'investing_cash_flow': safe_float(report.get('cashflowFromInvestment', 0)) / 1e9,
                                        'financing_cash_flow': safe_float(report.get('cashflowFromFinancing', 0)) / 1e9,
                                        'free_cash_flow': free_cf / 1e9,
                                        'capital_expenditures': abs(capex) / 1e9,
                                        'dividends_paid': abs(safe_float(report.get('dividendPayout', 0))) / 1e9
                                    })
                            
                            if cf_chart_data:
                                cf_df = pd.DataFrame(cf_chart_data).sort_values('year')
                                
                                # Cash Flow Components Chart
                                fig_cf_components = go.Figure()
                                
                                fig_cf_components.add_trace(go.Bar(
                                    x=cf_df['year'],
                                    y=cf_df['operating_cash_flow'],
                                    name='Operating Cash Flow',
                                    marker_color='#22c55e'
                                ))
                                
                                fig_cf_components.add_trace(go.Bar(
                                    x=cf_df['year'],
                                    y=cf_df['investing_cash_flow'],
                                    name='Investing Cash Flow',
                                    marker_color='#ef4444'
                                ))
                                
                                fig_cf_components.add_trace(go.Bar(
                                    x=cf_df['year'],
                                    y=cf_df['financing_cash_flow'],
                                    name='Financing Cash Flow',
                                    marker_color='#f59e0b'
                                ))
                                
                                fig_cf_components.update_layout(
                                    title=f"Cash Flow Components - {symbol}",
                                    xaxis_title="Year",
                                    yaxis_title="Cash Flow ($ Billions)",
                                    template="plotly_white" if theme == "Light" else "plotly_dark",
                                    height=500,
                                    barmode='group'
                                )
                                
                                st.plotly_chart(fig_cf_components, use_container_width=True)
                                
                                # Free Cash Flow Analysis
                                fig_fcf = go.Figure()
                                
                                fig_fcf.add_trace(go.Scatter(
                                    x=cf_df['year'],
                                    y=cf_df['free_cash_flow'],
                                    mode='lines+markers',
                                    name='Free Cash Flow',
                                    line=dict(color='#4e8df5', width=4)
                                ))
                                
                                fig_fcf.add_trace(go.Scatter(
                                    x=cf_df['year'],
                                    y=cf_df['dividends_paid'],
                                    mode='lines+markers',
                                    name='Dividends Paid',
                                    line=dict(color='#22c55e', width=3)
                                ))
                                
                                fig_fcf.add_trace(go.Scatter(
                                    x=cf_df['year'],
                                    y=cf_df['capital_expenditures'],
                                    mode='lines+markers',
                                    name='Capital Expenditures',
                                    line=dict(color='#ef4444', width=3)
                                ))
                                
                                fig_fcf.update_layout(
                                    title=f"Free Cash Flow vs Dividends & CapEx - {symbol}",
                                    xaxis_title="Year",
                                    yaxis_title="Amount ($ Billions)",
                                    template="plotly_white" if theme == "Light" else "plotly_dark",
                                    height=500,
                                    hovermode='x unified'
                                )
                                
                                st.plotly_chart(fig_fcf, use_container_width=True)
                                
                                # Cash Flow Coverage Analysis
                                if len(cf_df) > 0:
                                    st.subheader("Cash Flow Coverage Analysis")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    
                                    latest_cf = cf_df.iloc[-1]
                                    
                                    with col1:
                                        coverage_ratio = latest_cf['free_cash_flow'] / latest_cf['dividends_paid'] if latest_cf['dividends_paid'] > 0 else 0
                                        st.metric("Dividend Coverage Ratio", f"{coverage_ratio:.2f}x" if coverage_ratio > 0 else "N/A")
                                    
                                    with col2:
                                        fcf_margin = (latest_cf['free_cash_flow'] / metrics['revenue_ttm'] * 1e9) * 100 if metrics['revenue_ttm'] > 0 else 0
                                        st.metric("Free Cash Flow Margin", f"{fcf_margin:.2f}%" if fcf_margin != 0 else "N/A")
                                    
                                    with col3:
                                        capex_intensity = (latest_cf['capital_expenditures'] / metrics['revenue_ttm'] * 1e9) * 100 if metrics['revenue_ttm'] > 0 else 0
                                        st.metric("CapEx Intensity", f"{capex_intensity:.2f}%" if capex_intensity != 0 else "N/A")
                                
                                # Cash Flow Table
                                st.subheader("Cash Flow Summary")
                                display_cf_df = cf_df.copy()
                                display_cf_df = display_cf_df.round(2)
                                display_cf_df = display_cf_df.rename(columns={
                                    'year': 'Year',
                                    'operating_cash_flow': 'Operating CF ($B)',
                                    'investing_cash_flow': 'Investing CF ($B)',
                                    'financing_cash_flow': 'Financing CF ($B)',
                                    'free_cash_flow': 'Free CF ($B)',
                                    'capital_expenditures': 'CapEx ($B)',
                                    'dividends_paid': 'Dividends Paid ($B)'
                                })
                                st.dataframe(display_cf_df, use_container_width=True)
                        else:
                            st.warning("No cash flow data available")
                    
                    # Tab 4: Dividend Info
                    with analysis_tabs[3]:
                        st.subheader("💎 Dividend Information & Analysis")
                        
                        # Dividend Analysis Charts
                        if div_history is not None and not div_history.empty:
                            # Filter data based on time period
                            filtered_history = div_history[div_history['year'] >= cutoff_year]
                            filtered_annual = annual_divs[annual_divs['year'] >= cutoff_year] if annual_divs is not None else None
                            filtered_quarterly = quarterly_divs[quarterly_divs['year'] >= cutoff_year] if quarterly_divs is not None else None
                            
                            # Annual and Quarterly Dividend Charts
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if filtered_annual is not None and not filtered_annual.empty:
                                    fig_annual = px.bar(
                                        filtered_annual,
                                        x='year',
                                        y='dividend',
                                        title=f"Annual Dividends - {symbol}",
                                        labels={'dividend': 'Annual Dividend ($)', 'year': 'Year'},
                                        template="plotly_white" if theme == "Light" else "plotly_dark"
                                    )
                                    fig_annual.update_traces(marker_color='#4e8df5')
                                    fig_annual.update_layout(height=400)
                                    st.plotly_chart(fig_annual, use_container_width=True)
                            
                            with col2:
                                if filtered_quarterly is not None and not filtered_quarterly.empty:
                                    fig_quarterly = px.bar(
                                        filtered_quarterly,
                                        x='year_quarter',
                                        y='dividend',
                                        title=f"Quarterly Dividends - {symbol}",
                                        labels={'dividend': 'Quarterly Dividend ($)', 'year_quarter': 'Quarter'},
                                        template="plotly_white" if theme == "Light" else "plotly_dark"
                                    )
                                    fig_quarterly.update_traces(marker_color='#22c55e')
                                    fig_quarterly.update_layout(height=400, xaxis_tickangle=-45)
                                    st.plotly_chart(fig_quarterly, use_container_width=True)
                            
                            # Dividend Yield Over Time (using proper calculation)
                            if yield_df is not None and not yield_df.empty:
                                # Filter yield data based on time period
                                filtered_yield = yield_df[yield_df['date'] >= pd.to_datetime(f'{cutoff_year}-01-01')]
                                
                                if not filtered_yield.empty:
                                    period_avg = filtered_yield['dividend_yield'].mean()
                                    
                                    fig_yield = px.line(
                                        filtered_yield,
                                        x='date',
                                        y='dividend_yield',
                                        title=f"Dividend Yield Over Time (Daily Price / Trailing 12M Dividends) - {symbol}",
                                        labels={'dividend_yield': 'Dividend Yield (%)', 'date': 'Date'},
                                        template="plotly_white" if theme == "Light" else "plotly_dark"
                                    )
                                    
                                    # Add average line
                                    fig_yield.add_hline(
                                        y=period_avg,
                                        line_dash="dash",
                                        line_color="red",
                                        annotation_text=f"Period Average: {period_avg:.2f}%"
                                    )
                                    
                                    fig_yield.update_traces(line_color='#f59e0b', line_width=2)
                                    fig_yield.update_layout(height=400)
                                    st.plotly_chart(fig_yield, use_container_width=True)
                                else:
                                    st.warning("No dividend yield data available for the selected time period")
                            else:
                                # Fallback to estimated yield if daily price data not available
                                if filtered_history is not None and not filtered_history.empty:
                                    period_avg = filtered_history['estimated_yield'].mean()
                                    
                                    fig_yield = px.line(
                                        filtered_history,
                                        x='date',
                                        y='estimated_yield',
                                        title=f"Estimated Dividend Yield Over Time - {symbol}",
                                        labels={'estimated_yield': 'Estimated Dividend Yield (%)', 'date': 'Date'},
                                        template="plotly_white" if theme == "Light" else "plotly_dark"
                                    )
                                    
                                    # Add average line
                                    fig_yield.add_hline(
                                        y=period_avg,
                                        line_dash="dash",
                                        line_color="red",
                                        annotation_text=f"Period Average: {period_avg:.2f}%"
                                    )
                                    
                                    fig_yield.update_traces(line_color='#f59e0b', line_width=3)
                                    fig_yield.update_layout(height=400)
                                    st.plotly_chart(fig_yield, use_container_width=True)
                            
                            # Payout Ratio Chart
                            if income_data and len(income_data) > 0 and filtered_annual is not None:
                                payout_data = []
                                for report in income_data:
                                    fiscal_year = report.get('fiscalDateEnding', '')[:4]
                                    if fiscal_year and int(fiscal_year) >= cutoff_year:
                                        net_income = safe_float(report.get('netIncome', 0))
                                        shares = metrics['shares_outstanding']
                                        if net_income > 0 and shares > 0:
                                            eps = net_income / shares
                                            annual_div = filtered_annual[filtered_annual['year'] == int(fiscal_year)]['dividend'].iloc[0] if len(filtered_annual[filtered_annual['year'] == int(fiscal_year)]) > 0 else 0
                                            payout_ratio = (annual_div / eps) * 100 if eps > 0 else 0
                                            payout_data.append({
                                                'year': int(fiscal_year),
                                                'payout_ratio': min(payout_ratio, 200)  # Cap at 200%
                                            })
                                
                                if payout_data:
                                    payout_df = pd.DataFrame(payout_data).sort_values('year')
                                    
                                    fig_payout = px.bar(
                                        payout_df,
                                        x='year',
                                        y='payout_ratio',
                                        title=f"Payout Ratio Over Time - {symbol}",
                                        labels={'payout_ratio': 'Payout Ratio (%)', 'year': 'Year'},
                                        template="plotly_white" if theme == "Light" else "plotly_dark"
                                    )
                                    
                                    # Add safe zone (0-60%)
                                    fig_payout.add_hrect(y0=0, y1=60, fillcolor="green", opacity=0.1, annotation_text="Safe Zone")
                                    fig_payout.add_hrect(y0=60, y1=80, fillcolor="yellow", opacity=0.1, annotation_text="Caution Zone")
                                    fig_payout.add_hrect(y0=80, y1=200, fillcolor="red", opacity=0.1, annotation_text="Risk Zone")
                                    
                                    fig_payout.update_traces(marker_color='#8b5cf6')
                                    fig_payout.update_layout(height=400)
                                    st.plotly_chart(fig_payout, use_container_width=True)
                            
                            # Dividend Growth Chart
                            if filtered_annual is not None and len(filtered_annual) > 1:
                                # Calculate year-over-year growth
                                growth_data = []
                                for i in range(1, len(filtered_annual)):
                                    current_year_data = filtered_annual.iloc[i]
                                    previous_year_data = filtered_annual.iloc[i-1]
                                    
                                    if previous_year_data['dividend'] > 0:
                                        growth = ((current_year_data['dividend'] - previous_year_data['dividend']) / previous_year_data['dividend']) * 100
                                        growth_data.append({
                                            'year': current_year_data['year'],
                                            'growth': growth
                                        })
                                
                                if growth_data:
                                    growth_df = pd.DataFrame(growth_data)
                                    
                                    fig_growth = px.bar(
                                        growth_df,
                                        x='year',
                                        y='growth',
                                        title=f"Dividend Growth Rate - {symbol}",
                                        labels={'growth': 'YoY Growth (%)', 'year': 'Year'},
                                        template="plotly_white" if theme == "Light" else "plotly_dark"
                                    )
                                    
                                    # Color bars based on growth (green for positive, red for negative)
                                    fig_growth.update_traces(
                                        marker_color=['#22c55e' if x >= 0 else '#ef4444' for x in growth_df['growth']]
                                    )
                                    
                                    fig_growth.add_hline(y=0, line_dash="dash", line_color="gray")
                                    fig_growth.update_layout(height=400)
                                    st.plotly_chart(fig_growth, use_container_width=True)
                            
                            # Dividend Summary Metrics
                            st.subheader("Dividend Summary")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Current Dividend Yield", f"{metrics['dividend_yield']:.2f}%" if metrics['dividend_yield'] > 0 else "N/A")
                                st.metric("Dividend Per Share", f"${metrics['dividend_per_share']:.2f}" if metrics['dividend_per_share'] > 0 else "N/A")
                            
                            with col2:
                                st.metric("Payout Ratio", f"{metrics['payout_ratio']:.1f}%" if metrics['payout_ratio'] > 0 else "N/A")
                                st.metric("Ex-Dividend Date", metrics['ex_dividend_date'])
                            
                            with col3:
                                # Calculate average dividend growth
                                if 'growth_data' in locals() and len(growth_data) > 0:
                                    avg_growth = sum([g['growth'] for g in growth_data]) / len(growth_data)
                                    st.metric("Avg Dividend Growth", f"{avg_growth:.1f}%")
                                else:
                                    st.metric("Avg Dividend Growth", "N/A")
                                
                                st.metric("Dividend Date", metrics['dividend_date'])
                            
                            with col4:
                                # Calculate dividend coverage from free cash flow
                                if 'cf_chart_data' in locals() and len(cf_chart_data) > 0:
                                    latest_cf_data = cf_chart_data[-1]
                                    fcf_coverage = latest_cf_data['free_cash_flow'] / latest_cf_data['dividends_paid'] if latest_cf_data['dividends_paid'] > 0 else 0
                                    st.metric("FCF Coverage", f"{fcf_coverage:.2f}x" if fcf_coverage > 0 else "N/A")
                                else:
                                    st.metric("FCF Coverage", "N/A")
                                
                                # Years of dividend payments
                                years_paying = len(filtered_annual) if filtered_annual is not None else 0
                                st.metric("Years of Data", f"{years_paying} years")
                        
                        else:
                            st.warning("No dividend data available")
                            
                            # Show basic dividend info from company overview
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Current Dividend Yield", f"{metrics['dividend_yield']:.2f}%" if metrics['dividend_yield'] > 0 else "N/A")
                            
                            with col2:
                                st.metric("Dividend Per Share", f"${metrics['dividend_per_share']:.2f}" if metrics['dividend_per_share'] > 0 else "N/A")
                            
                            with col3:
                                st.metric("Ex-Dividend Date", metrics['ex_dividend_date'])
                    
                    # Risk Assessment and Investment Summary
                    st.markdown("---")
                    st.subheader("⚠️ Risk Assessment & Investment Summary")
                    
                    risk_score = 0
                    risk_factors = []
                    
                    # Analyze risk factors
                    if metrics['payout_ratio'] > 80:
                        risk_score += 20
                        risk_factors.append("High payout ratio (>80%)")
                    elif metrics['payout_ratio'] > 60:
                        risk_score += 10
                        risk_factors.append("Moderate payout ratio (60-80%)")
                    
                    if metrics['debt_to_equity'] > 1.5:
                        risk_score += 20
                        risk_factors.append("High debt-to-equity ratio")
                    elif metrics['debt_to_equity'] > 1.0:
                        risk_score += 10
                        risk_factors.append("Moderate debt levels")
                    
                    if metrics['current_ratio'] < 1.0:
                        risk_score += 15
                        risk_factors.append("Poor liquidity (current ratio < 1.0)")
                    elif metrics['current_ratio'] < 1.2:
                        risk_score += 8
                        risk_factors.append("Tight liquidity")
                    
                    if metrics['revenue_growth_yoy'] < -5:
                        risk_score += 15
                        risk_factors.append("Declining revenue")
                    
                    if metrics['pe_ratio'] > 30:
                        risk_score += 10
                        risk_factors.append("High valuation (P/E > 30)")
                    
                    # Display risk assessment
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        if risk_score <= 20:
                            risk_level = "🟢 Low Risk"
                        elif risk_score <= 40:
                            risk_level = "🟡 Moderate Risk"
                        else:
                            risk_level = "🔴 High Risk"
                        
                        st.markdown(f"**Overall Risk Level:** {risk_level}")
                        st.markdown(f"**Risk Score:** {risk_score}/100")
                    
                    with col2:
                        if risk_factors:
                            st.markdown("**Risk Factors:**")
                            for factor in risk_factors:
                                st.markdown(f"• {factor}")
                        else:
                            st.markdown("**No significant risk factors identified**")
                    
                    # Investment Recommendation
                    st.markdown("---")
                    st.subheader("🎯 Investment Summary")
                    
                    # Calculate investment score
                    investment_score = 100 - risk_score
                    
                    # Adjust based on dividend attractiveness
                    if metrics['dividend_yield'] >= 4:
                        investment_score += 10
                    elif metrics['dividend_yield'] >= 2:
                        investment_score += 5
                    
                    # Adjust based on growth
                    if metrics['revenue_growth_yoy'] >= 10:
                        investment_score += 10
                    elif metrics['revenue_growth_yoy'] >= 5:
                        investment_score += 5
                    
                    # Adjust based on profitability
                    if metrics['roe'] >= 15:
                        investment_score += 10
                    elif metrics['roe'] >= 10:
                        investment_score += 5
                    
                    investment_score = min(investment_score, 100)  # Cap at 100
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if investment_score >= 80:
                            recommendation = "🟢 Strong Buy"
                        elif investment_score >= 70:
                            recommendation = "🟢 Buy"
                        elif investment_score >= 60:
                            recommendation = "🟡 Hold"
                        elif investment_score >= 50:
                            recommendation = "🟡 Weak Hold"
                        else:
                            recommendation = "🔴 Avoid"
                        
                        st.metric("Investment Score", f"{investment_score}/100")
                        st.markdown(f"**Recommendation:** {recommendation}")
                    
                    with col2:
                        # Key strengths
                        strengths = []
                        if metrics['dividend_yield'] >= 3:
                            strengths.append("High dividend yield")
                        if metrics['payout_ratio'] <= 60 and metrics['payout_ratio'] > 0:
                            strengths.append("Conservative payout ratio")
                        if metrics['roe'] >= 15:
                            strengths.append("Strong profitability")
                        if metrics['current_ratio'] >= 1.5:
                            strengths.append("Strong liquidity")
                        if metrics['revenue_growth_yoy'] >= 5:
                            strengths.append("Growing revenue")
                        
                        if strengths:
                            st.markdown("**Key Strengths:**")
                            for strength in strengths[:3]:  # Show top 3
                                st.markdown(f"✅ {strength}")
                    
                    with col3:
                        # Key considerations
                        considerations = []
                        if metrics['pe_ratio'] > 25:
                            considerations.append("High valuation")
                        if metrics['dividend_yield'] < 2:
                            considerations.append("Low dividend yield")
                        if metrics['debt_to_equity'] > 1:
                            considerations.append("High debt levels")
                        if metrics['revenue_growth_yoy'] < 0:
                            considerations.append("Revenue decline")
                        
                        if considerations:
                            st.markdown("**Considerations:**")
                            for consideration in considerations[:3]:  # Show top 3
                                st.markdown(f"⚠️ {consideration}")
                        else:
                            st.markdown("**No major concerns identified**")
                    
                else:
                    st.error(f"Could not fetch data for symbol: {symbol}")
        else:
            st.error("Please enter a stock symbol")