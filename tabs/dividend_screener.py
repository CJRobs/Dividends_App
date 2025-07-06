import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import json

# Alpha Vantage API configuration
ALPHA_VANTAGE_API_KEY = "7SJSMIH29T07IB8L"
BASE_URL = "https://www.alphavantage.co/query"

# Rate limiting for API calls
def rate_limit():
    """Add delay between API calls to respect rate limits"""
    time.sleep(0.2)  # 200ms delay between calls

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_company_overview(symbol):
    """Get company overview data from Alpha Vantage"""
    try:
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        rate_limit()
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if 'Symbol' in data:
            return data
        else:
            st.warning(f"No data found for symbol: {symbol}")
            return None
            
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_dividend_data(symbol):
    """Get dividend data from Alpha Vantage"""
    try:
        params = {
            'function': 'TIME_SERIES_MONTHLY_ADJUSTED',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        rate_limit()
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if 'Monthly Adjusted Time Series' in data:
            return data['Monthly Adjusted Time Series']
        else:
            return None
            
    except Exception as e:
        st.error(f"Error fetching dividend data for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_income_statement(symbol):
    """Get income statement data from Alpha Vantage"""
    try:
        params = {
            'function': 'INCOME_STATEMENT',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        rate_limit()
        response = requests.get(BASE_URL, params=params)
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
        params = {
            'function': 'BALANCE_SHEET',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        rate_limit()
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if 'annualReports' in data:
            return data['annualReports']
        else:
            return None
            
    except Exception as e:
        st.error(f"Error fetching balance sheet for {symbol}: {str(e)}")
        return None

def calculate_dividend_metrics(overview_data, dividend_data, income_data):
    """Calculate comprehensive dividend metrics"""
    metrics = {}
    
    try:
        # Basic metrics from overview
        metrics['symbol'] = overview_data.get('Symbol', 'N/A')
        metrics['name'] = overview_data.get('Name', 'N/A')
        metrics['sector'] = overview_data.get('Sector', 'N/A')
        metrics['market_cap'] = float(overview_data.get('MarketCapitalization', 0))
        metrics['pe_ratio'] = float(overview_data.get('PERatio', 0)) if overview_data.get('PERatio', 'None') != 'None' else 0
        metrics['dividend_yield'] = float(overview_data.get('DividendYield', 0)) * 100 if overview_data.get('DividendYield', '0') != '0' else 0
        metrics['payout_ratio'] = float(overview_data.get('PayoutRatio', 0)) * 100 if overview_data.get('PayoutRatio', '0') != '0' else 0
        metrics['ex_dividend_date'] = overview_data.get('ExDividendDate', 'N/A')
        metrics['dividend_date'] = overview_data.get('DividendDate', 'N/A')
        
        # Stock price metrics
        metrics['52_week_high'] = float(overview_data.get('52WeekHigh', 0))
        metrics['52_week_low'] = float(overview_data.get('52WeekLow', 0))
        metrics['current_price'] = float(overview_data.get('Price', 0)) if overview_data.get('Price') else 0
        
        # Financial strength metrics
        metrics['book_value'] = float(overview_data.get('BookValue', 0))
        metrics['pb_ratio'] = float(overview_data.get('PriceToBookRatio', 0))
        metrics['debt_to_equity'] = float(overview_data.get('DebtToEquityRatio', 0))
        metrics['current_ratio'] = float(overview_data.get('CurrentRatio', 0))
        metrics['quick_ratio'] = float(overview_data.get('QuickRatio', 0))
        
        # Profitability metrics
        metrics['roe'] = float(overview_data.get('ReturnOnEquityTTM', 0)) * 100 if overview_data.get('ReturnOnEquityTTM', '0') != '0' else 0
        metrics['roa'] = float(overview_data.get('ReturnOnAssetsTTM', 0)) * 100 if overview_data.get('ReturnOnAssetsTTM', '0') != '0' else 0
        metrics['profit_margin'] = float(overview_data.get('ProfitMargin', 0)) * 100 if overview_data.get('ProfitMargin', '0') != '0' else 0
        
        # Growth metrics
        metrics['revenue_growth'] = float(overview_data.get('QuarterlyRevenueGrowthYOY', 0)) * 100 if overview_data.get('QuarterlyRevenueGrowthYOY', '0') != '0' else 0
        metrics['earnings_growth'] = float(overview_data.get('QuarterlyEarningsGrowthYOY', 0)) * 100 if overview_data.get('QuarterlyEarningsGrowthYOY', '0') != '0' else 0
        
        # Calculate dividend growth if historical data available
        if dividend_data and len(dividend_data) >= 24:  # Need at least 2 years of data
            dates = sorted(dividend_data.keys(), reverse=True)
            
            # Calculate annual dividends for last 3 years
            annual_dividends = {}
            for date in dates:
                year = date[:4]
                if year not in annual_dividends:
                    annual_dividends[year] = 0
                
                dividend_amount = float(dividend_data[date].get('7. dividend amount', 0))
                annual_dividends[year] += dividend_amount
            
            # Calculate dividend growth rate
            years = sorted(annual_dividends.keys(), reverse=True)
            if len(years) >= 2:
                recent_year = annual_dividends[years[0]]
                previous_year = annual_dividends[years[1]]
                if previous_year > 0:
                    metrics['dividend_growth_1yr'] = ((recent_year - previous_year) / previous_year) * 100
                else:
                    metrics['dividend_growth_1yr'] = 0
                
                # 3-year average growth
                if len(years) >= 3:
                    three_year_old = annual_dividends[years[2]]
                    if three_year_old > 0:
                        cagr = ((recent_year / three_year_old) ** (1/2)) - 1
                        metrics['dividend_growth_3yr'] = cagr * 100
                    else:
                        metrics['dividend_growth_3yr'] = 0
                else:
                    metrics['dividend_growth_3yr'] = 0
            else:
                metrics['dividend_growth_1yr'] = 0
                metrics['dividend_growth_3yr'] = 0
        else:
            metrics['dividend_growth_1yr'] = 0
            metrics['dividend_growth_3yr'] = 0
        
        # Calculate dividend safety score (0-100)
        safety_score = 0
        
        # Payout ratio score (30 points max)
        if metrics['payout_ratio'] > 0:
            if metrics['payout_ratio'] <= 50:
                safety_score += 30
            elif metrics['payout_ratio'] <= 70:
                safety_score += 20
            elif metrics['payout_ratio'] <= 90:
                safety_score += 10
        
        # Debt to equity score (20 points max)
        if metrics['debt_to_equity'] > 0:
            if metrics['debt_to_equity'] <= 0.5:
                safety_score += 20
            elif metrics['debt_to_equity'] <= 1.0:
                safety_score += 15
            elif metrics['debt_to_equity'] <= 1.5:
                safety_score += 10
            elif metrics['debt_to_equity'] <= 2.0:
                safety_score += 5
        
        # Current ratio score (15 points max)
        if metrics['current_ratio'] >= 1.5:
            safety_score += 15
        elif metrics['current_ratio'] >= 1.2:
            safety_score += 10
        elif metrics['current_ratio'] >= 1.0:
            safety_score += 5
        
        # ROE score (20 points max)
        if metrics['roe'] >= 15:
            safety_score += 20
        elif metrics['roe'] >= 10:
            safety_score += 15
        elif metrics['roe'] >= 5:
            safety_score += 10
        elif metrics['roe'] > 0:
            safety_score += 5
        
        # Revenue growth score (15 points max)
        if metrics['revenue_growth'] >= 10:
            safety_score += 15
        elif metrics['revenue_growth'] >= 5:
            safety_score += 10
        elif metrics['revenue_growth'] >= 0:
            safety_score += 5
        
        metrics['dividend_safety_score'] = safety_score
        
        # Overall investment score (0-100)
        investment_score = 0
        
        # Dividend yield score (25 points)
        if metrics['dividend_yield'] >= 4:
            investment_score += 25
        elif metrics['dividend_yield'] >= 3:
            investment_score += 20
        elif metrics['dividend_yield'] >= 2:
            investment_score += 15
        elif metrics['dividend_yield'] > 0:
            investment_score += 10
        
        # Dividend growth score (25 points)
        if metrics['dividend_growth_3yr'] >= 10:
            investment_score += 25
        elif metrics['dividend_growth_3yr'] >= 5:
            investment_score += 20
        elif metrics['dividend_growth_3yr'] >= 0:
            investment_score += 15
        elif metrics['dividend_growth_1yr'] > 0:
            investment_score += 10
        
        # Valuation score (25 points)
        if metrics['pe_ratio'] > 0:
            if metrics['pe_ratio'] <= 15:
                investment_score += 25
            elif metrics['pe_ratio'] <= 20:
                investment_score += 20
            elif metrics['pe_ratio'] <= 25:
                investment_score += 15
            elif metrics['pe_ratio'] <= 30:
                investment_score += 10
        
        # Safety score contribution (25 points)
        investment_score += (safety_score / 100) * 25
        
        metrics['investment_score'] = investment_score
        
    except Exception as e:
        st.error(f"Error calculating metrics: {str(e)}")
    
    return metrics

def screen_stocks(symbols, filters):
    """Screen multiple stocks based on criteria"""
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, symbol in enumerate(symbols):
        status_text.text(f"Analyzing {symbol}... ({i+1}/{len(symbols)})")
        progress_bar.progress((i + 1) / len(symbols))
        
        # Get data for the symbol
        overview = get_company_overview(symbol.strip().upper())
        if overview:
            dividend_data = get_dividend_data(symbol.strip().upper())
            income_data = get_income_statement(symbol.strip().upper())
            
            metrics = calculate_dividend_metrics(overview, dividend_data, income_data)
            
            # Apply filters
            passes_filter = True
            
            if filters['min_yield'] > 0 and metrics['dividend_yield'] < filters['min_yield']:
                passes_filter = False
            if filters['max_payout'] < 100 and metrics['payout_ratio'] > filters['max_payout']:
                passes_filter = False
            if filters['min_market_cap'] > 0 and metrics['market_cap'] < filters['min_market_cap']:
                passes_filter = False
            if filters['min_roe'] > 0 and metrics['roe'] < filters['min_roe']:
                passes_filter = False
            if filters['max_debt_equity'] < 10 and metrics['debt_to_equity'] > filters['max_debt_equity']:
                passes_filter = False
            if filters['min_current_ratio'] > 0 and metrics['current_ratio'] < filters['min_current_ratio']:
                passes_filter = False
            if filters['min_dividend_growth'] != 0 and metrics['dividend_growth_1yr'] < filters['min_dividend_growth']:
                passes_filter = False
            
            if passes_filter:
                results.append(metrics)
    
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(results)

def show_dividend_screener_tab(df, monthly_data, currency, theme, current_date, current_year, current_month, format_currency, **kwargs):
    """
    Display the Dividend Screener tab content
    """
    st.subheader("🔍 Dividend Stock Screener")
    st.markdown("Analyze dividend stocks using Alpha Vantage data with comprehensive quantitative metrics")
    
    # Create tabs for different screener views
    screener_tabs = st.tabs(["Stock Screener", "Individual Analysis", "Comparison Tool"])
    
    # Tab 1: Stock Screener
    with screener_tabs[0]:
        st.subheader("Multi-Stock Dividend Screener")
        
        # Input section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            symbols_input = st.text_area(
                "Enter stock symbols (comma-separated)",
                placeholder="AAPL, MSFT, JNJ, KO, PEP, T, VZ, XOM, CVX, PFE",
                height=100,
                help="Enter stock symbols separated by commas. Up to 25 symbols recommended due to API limits."
            )
        
        with col2:
            st.subheader("Screening Filters")
            min_yield = st.number_input("Min Dividend Yield (%)", 0.0, 20.0, 0.0, 0.1)
            max_payout = st.number_input("Max Payout Ratio (%)", 0.0, 200.0, 100.0, 5.0)
            min_market_cap = st.number_input("Min Market Cap (Millions)", 0, 1000000, 0, 1000)
            min_roe = st.number_input("Min ROE (%)", 0.0, 50.0, 0.0, 1.0)
            max_debt_equity = st.number_input("Max Debt/Equity", 0.0, 10.0, 10.0, 0.1)
            min_current_ratio = st.number_input("Min Current Ratio", 0.0, 5.0, 0.0, 0.1)
            min_dividend_growth = st.number_input("Min 1-Year Dividend Growth (%)", -50.0, 100.0, 0.0, 1.0)
        
        filters = {
            'min_yield': min_yield,
            'max_payout': max_payout,
            'min_market_cap': min_market_cap * 1000000,  # Convert to actual value
            'min_roe': min_roe,
            'max_debt_equity': max_debt_equity,
            'min_current_ratio': min_current_ratio,
            'min_dividend_growth': min_dividend_growth
        }
        
        if st.button("🔍 Screen Stocks", type="primary"):
            if symbols_input.strip():
                symbols = [s.strip() for s in symbols_input.split(',') if s.strip()]
                
                if len(symbols) > 25:
                    st.warning("⚠️ Limited to 25 symbols due to API rate limits. Processing first 25 symbols.")
                    symbols = symbols[:25]
                
                with st.spinner("Screening stocks... This may take a few minutes due to API rate limits."):
                    screened_df = screen_stocks(symbols, filters)
                
                if not screened_df.empty:
                    st.success(f"✅ Found {len(screened_df)} stocks matching your criteria")
                    
                    # Sort by investment score
                    screened_df = screened_df.sort_values('investment_score', ascending=False)
                    
                    # Display results table
                    display_cols = [
                        'symbol', 'name', 'sector', 'dividend_yield', 'payout_ratio',
                        'dividend_growth_1yr', 'pe_ratio', 'roe', 'debt_to_equity',
                        'current_ratio', 'dividend_safety_score', 'investment_score'
                    ]
                    
                    display_df = screened_df[display_cols].copy()
                    
                    # Format numeric columns
                    numeric_cols = ['dividend_yield', 'payout_ratio', 'dividend_growth_1yr', 
                                  'pe_ratio', 'roe', 'debt_to_equity', 'current_ratio',
                                  'dividend_safety_score', 'investment_score']
                    
                    for col in numeric_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].round(2)
                    
                    # Rename columns for display
                    column_names = {
                        'symbol': 'Symbol',
                        'name': 'Company Name',
                        'sector': 'Sector',
                        'dividend_yield': 'Div Yield (%)',
                        'payout_ratio': 'Payout Ratio (%)',
                        'dividend_growth_1yr': '1Y Div Growth (%)',
                        'pe_ratio': 'P/E Ratio',
                        'roe': 'ROE (%)',
                        'debt_to_equity': 'Debt/Equity',
                        'current_ratio': 'Current Ratio',
                        'dividend_safety_score': 'Safety Score',
                        'investment_score': 'Investment Score'
                    }
                    
                    display_df = display_df.rename(columns=column_names)
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        height=400
                    )
                    
                    # Visualization of results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Scatter plot: Dividend Yield vs Safety Score
                        fig_scatter = px.scatter(
                            screened_df,
                            x='dividend_yield',
                            y='dividend_safety_score',
                            size='market_cap',
                            color='investment_score',
                            hover_name='symbol',
                            title="Dividend Yield vs Safety Score",
                            labels={
                                'dividend_yield': 'Dividend Yield (%)',
                                'dividend_safety_score': 'Dividend Safety Score',
                                'investment_score': 'Investment Score'
                            },
                            template="plotly_white" if theme == "Light" else "plotly_dark"
                        )
                        
                        st.plotly_chart(fig_scatter, use_container_width=True)
                    
                    with col2:
                        # Bar chart: Top stocks by investment score
                        top_10 = screened_df.head(10)
                        fig_bar = px.bar(
                            top_10,
                            x='investment_score',
                            y='symbol',
                            orientation='h',
                            title="Top 10 Stocks by Investment Score",
                            labels={
                                'investment_score': 'Investment Score',
                                'symbol': 'Symbol'
                            },
                            template="plotly_white" if theme == "Light" else "plotly_dark"
                        )
                        
                        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig_bar, use_container_width=True)
                    
                    # Sector analysis
                    if 'sector' in screened_df.columns:
                        st.subheader("Sector Analysis")
                        sector_analysis = screened_df.groupby('sector').agg({
                            'dividend_yield': 'mean',
                            'dividend_safety_score': 'mean',
                            'investment_score': 'mean',
                            'symbol': 'count'
                        }).round(2)
                        
                        sector_analysis = sector_analysis.rename(columns={
                            'dividend_yield': 'Avg Dividend Yield (%)',
                            'dividend_safety_score': 'Avg Safety Score',
                            'investment_score': 'Avg Investment Score',
                            'symbol': 'Stock Count'
                        })
                        
                        st.dataframe(sector_analysis, use_container_width=True)
                    
                    # Store results in session state for other tabs
                    st.session_state['screened_stocks'] = screened_df
                    
                else:
                    st.warning("❌ No stocks found matching your criteria. Try adjusting the filters.")
            else:
                st.error("Please enter at least one stock symbol")
    
    # Tab 2: Individual Analysis
    with screener_tabs[1]:
        st.subheader("Individual Stock Analysis")
        
        symbol = st.text_input("Enter stock symbol for detailed analysis", "AAPL").upper()
        
        if st.button("📊 Analyze Stock"):
            if symbol:
                with st.spinner(f"Analyzing {symbol}..."):
                    overview = get_company_overview(symbol)
                    
                    if overview:
                        dividend_data = get_dividend_data(symbol)
                        income_data = get_income_statement(symbol)
                        balance_data = get_balance_sheet(symbol)
                        
                        metrics = calculate_dividend_metrics(overview, dividend_data, income_data)
                        
                        # Display comprehensive analysis
                        st.subheader(f"{metrics['name']} ({metrics['symbol']})")
                        st.write(f"**Sector:** {metrics['sector']}")
                        
                        # Key metrics in columns
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "Dividend Yield",
                                f"{metrics['dividend_yield']:.2f}%",
                                delta=None
                            )
                            st.metric(
                                "P/E Ratio",
                                f"{metrics['pe_ratio']:.2f}" if metrics['pe_ratio'] > 0 else "N/A",
                                delta=None
                            )
                        
                        with col2:
                            st.metric(
                                "Payout Ratio",
                                f"{metrics['payout_ratio']:.2f}%" if metrics['payout_ratio'] > 0 else "N/A",
                                delta=None
                            )
                            st.metric(
                                "ROE",
                                f"{metrics['roe']:.2f}%" if metrics['roe'] > 0 else "N/A",
                                delta=None
                            )
                        
                        with col3:
                            st.metric(
                                "Debt/Equity",
                                f"{metrics['debt_to_equity']:.2f}" if metrics['debt_to_equity'] > 0 else "N/A",
                                delta=None
                            )
                            st.metric(
                                "Current Ratio",
                                f"{metrics['current_ratio']:.2f}" if metrics['current_ratio'] > 0 else "N/A",
                                delta=None
                            )
                        
                        with col4:
                            st.metric(
                                "Safety Score",
                                f"{metrics['dividend_safety_score']:.0f}/100",
                                delta=None
                            )
                            st.metric(
                                "Investment Score",
                                f"{metrics['investment_score']:.0f}/100",
                                delta=None
                            )
                        
                        # Dividend history visualization
                        if dividend_data:
                            st.subheader("Dividend History")
                            
                            # Process dividend data for visualization
                            div_df = []
                            for date, data in dividend_data.items():
                                div_amount = float(data.get('7. dividend amount', 0))
                                if div_amount > 0:
                                    div_df.append({
                                        'date': pd.to_datetime(date),
                                        'dividend': div_amount
                                    })
                            
                            if div_df:
                                div_df = pd.DataFrame(div_df).sort_values('date')
                                
                                fig_div = px.line(
                                    div_df,
                                    x='date',
                                    y='dividend',
                                    title=f"{symbol} Dividend History",
                                    template="plotly_white" if theme == "Light" else "plotly_dark"
                                )
                                
                                st.plotly_chart(fig_div, use_container_width=True)
                        
                        # Financial strength radar chart
                        st.subheader("Financial Strength Analysis")
                        
                        categories = ['Dividend Yield', 'Safety Score', 'Growth', 'Profitability', 'Valuation']
                        
                        # Normalize scores to 0-100 scale
                        yield_score = min(metrics['dividend_yield'] * 25, 100)  # 4% = 100
                        safety_score = metrics['dividend_safety_score']
                        growth_score = max(0, min(metrics['dividend_growth_1yr'] * 10, 100))  # 10% = 100
                        profit_score = max(0, min(metrics['roe'] * 5, 100))  # 20% = 100
                        value_score = max(0, 100 - (metrics['pe_ratio'] * 3)) if metrics['pe_ratio'] > 0 else 50  # Lower PE = higher score
                        
                        values = [yield_score, safety_score, growth_score, profit_score, value_score]
                        
                        fig_radar = go.Figure()
                        
                        fig_radar.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name=symbol,
                            line_color='#4e8df5'
                        ))
                        
                        fig_radar.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 100]
                                )),
                            showlegend=True,
                            title=f"{symbol} Financial Strength Radar",
                            template="plotly_white" if theme == "Light" else "plotly_dark"
                        )
                        
                        st.plotly_chart(fig_radar, use_container_width=True)
                        
                    else:
                        st.error(f"Could not fetch data for symbol: {symbol}")
            else:
                st.error("Please enter a stock symbol")
    
    # Tab 3: Comparison Tool
    with screener_tabs[2]:
        st.subheader("Stock Comparison Tool")
        
        symbols_compare = st.text_input(
            "Enter symbols to compare (comma-separated)",
            placeholder="AAPL, MSFT, JNJ",
            help="Enter 2-5 stock symbols for comparison"
        )
        
        if st.button("📈 Compare Stocks"):
            if symbols_compare.strip():
                symbols_list = [s.strip().upper() for s in symbols_compare.split(',') if s.strip()]
                
                if len(symbols_list) < 2:
                    st.error("Please enter at least 2 symbols for comparison")
                elif len(symbols_list) > 5:
                    st.warning("Limited to 5 symbols for comparison. Using first 5.")
                    symbols_list = symbols_list[:5]
                else:
                    comparison_data = []
                    
                    with st.spinner("Fetching comparison data..."):
                        for symbol in symbols_list:
                            overview = get_company_overview(symbol)
                            if overview:
                                dividend_data = get_dividend_data(symbol)
                                income_data = get_income_statement(symbol)
                                metrics = calculate_dividend_metrics(overview, dividend_data, income_data)
                                comparison_data.append(metrics)
                    
                    if comparison_data:
                        comp_df = pd.DataFrame(comparison_data)
                        
                        # Comparison metrics
                        st.subheader("Comparison Metrics")
                        
                        metrics_to_compare = [
                            'dividend_yield', 'payout_ratio', 'dividend_growth_1yr',
                            'pe_ratio', 'roe', 'debt_to_equity', 'current_ratio',
                            'dividend_safety_score', 'investment_score'
                        ]
                        
                        comparison_display = comp_df[['symbol', 'name'] + metrics_to_compare].copy()
                        
                        # Format for display
                        for col in metrics_to_compare:
                            if col in comparison_display.columns:
                                comparison_display[col] = comparison_display[col].round(2)
                        
                        # Rename columns
                        display_names = {
                            'symbol': 'Symbol',
                            'name': 'Company',
                            'dividend_yield': 'Div Yield (%)',
                            'payout_ratio': 'Payout (%)',
                            'dividend_growth_1yr': '1Y Growth (%)',
                            'pe_ratio': 'P/E',
                            'roe': 'ROE (%)',
                            'debt_to_equity': 'D/E',
                            'current_ratio': 'Current Ratio',
                            'dividend_safety_score': 'Safety Score',
                            'investment_score': 'Investment Score'
                        }
                        
                        comparison_display = comparison_display.rename(columns=display_names)
                        
                        st.dataframe(comparison_display, use_container_width=True)
                        
                        # Comparison charts
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Dividend yield comparison
                            fig_yield = px.bar(
                                comp_df,
                                x='symbol',
                                y='dividend_yield',
                                title="Dividend Yield Comparison",
                                labels={'dividend_yield': 'Dividend Yield (%)', 'symbol': 'Symbol'},
                                template="plotly_white" if theme == "Light" else "plotly_dark"
                            )
                            st.plotly_chart(fig_yield, use_container_width=True)
                        
                        with col2:
                            # Investment score comparison
                            fig_score = px.bar(
                                comp_df,
                                x='symbol',
                                y='investment_score',
                                title="Investment Score Comparison",
                                labels={'investment_score': 'Investment Score', 'symbol': 'Symbol'},
                                template="plotly_white" if theme == "Light" else "plotly_dark"
                            )
                            st.plotly_chart(fig_score, use_container_width=True)
                        
                        # Multi-metric radar chart comparison
                        st.subheader("Multi-Stock Radar Comparison")
                        
                        fig_multi_radar = go.Figure()
                        
                        categories = ['Div Yield', 'Safety', 'Growth', 'Profitability', 'Valuation']
                        colors = ['#4e8df5', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6']
                        
                        for i, (_, row) in enumerate(comp_df.iterrows()):
                            # Normalize scores
                            yield_score = min(row['dividend_yield'] * 25, 100)
                            safety_score = row['dividend_safety_score']
                            growth_score = max(0, min(row['dividend_growth_1yr'] * 10, 100))
                            profit_score = max(0, min(row['roe'] * 5, 100))
                            value_score = max(0, 100 - (row['pe_ratio'] * 3)) if row['pe_ratio'] > 0 else 50
                            
                            values = [yield_score, safety_score, growth_score, profit_score, value_score]
                            
                            fig_multi_radar.add_trace(go.Scatterpolar(
                                r=values,
                                theta=categories,
                                fill='toself',
                                name=row['symbol'],
                                line_color=colors[i % len(colors)]
                            ))
                        
                        fig_multi_radar.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 100]
                                )),
                            showlegend=True,
                            title="Multi-Stock Comparison Radar",
                            template="plotly_white" if theme == "Light" else "plotly_dark"
                        )
                        
                        st.plotly_chart(fig_multi_radar, use_container_width=True)
                        
                        # Risk vs Return scatter plot
                        st.subheader("Risk vs Return Analysis")
                        
                        fig_risk_return = px.scatter(
                            comp_df,
                            x='dividend_safety_score',
                            y='dividend_yield',
                            size='market_cap',
                            color='symbol',
                            title="Risk vs Return (Safety Score vs Dividend Yield)",
                            labels={
                                'dividend_safety_score': 'Dividend Safety Score',
                                'dividend_yield': 'Dividend Yield (%)',
                                'symbol': 'Symbol'
                            },
                            template="plotly_white" if theme == "Light" else "plotly_dark"
                        )
                        
                        # Add quadrant lines
                        fig_risk_return.add_hline(y=comp_df['dividend_yield'].mean(), 
                                                line_dash="dash", line_color="gray",
                                                annotation_text="Avg Yield")
                        fig_risk_return.add_vline(x=comp_df['dividend_safety_score'].mean(), 
                                                line_dash="dash", line_color="gray",
                                                annotation_text="Avg Safety")
                        
                        st.plotly_chart(fig_risk_return, use_container_width=True)
                        
                        # Best/Worst performers summary
                        st.subheader("Performance Summary")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            highest_yield = comp_df.loc[comp_df['dividend_yield'].idxmax()]
                            st.metric(
                                "Highest Dividend Yield",
                                f"{highest_yield['symbol']}",
                                f"{highest_yield['dividend_yield']:.2f}%"
                            )
                        
                        with col2:
                            safest_dividend = comp_df.loc[comp_df['dividend_safety_score'].idxmax()]
                            st.metric(
                                "Safest Dividend",
                                f"{safest_dividend['symbol']}",
                                f"{safest_dividend['dividend_safety_score']:.0f}/100"
                            )
                        
                        with col3:
                            best_investment = comp_df.loc[comp_df['investment_score'].idxmax()]
                            st.metric(
                                "Best Overall Investment",
                                f"{best_investment['symbol']}",
                                f"{best_investment['investment_score']:.0f}/100"
                            )
                    
                    else:
                        st.error("Could not fetch data for any of the symbols")
            else:
                st.error("Please enter stock symbols to compare")
    
    # Information section
    with st.expander("ℹ️ About the Dividend Screener"):
        st.markdown("""
        ### How the Dividend Screener Works
        
        This tool uses Alpha Vantage API to fetch real-time financial data and performs comprehensive quantitative analysis on dividend stocks.
        
        #### Key Metrics Explained:
        
        **Dividend Safety Score (0-100):**
        - Payout Ratio (30 pts): Lower ratios indicate more sustainable dividends
        - Debt-to-Equity (20 pts): Lower debt levels reduce financial risk
        - Current Ratio (15 pts): Higher ratios indicate better liquidity
        - Return on Equity (20 pts): Higher ROE indicates efficient management
        - Revenue Growth (15 pts): Positive growth supports future dividends
        
        **Investment Score (0-100):**
        - Dividend Yield (25 pts): Higher yields provide better income
        - Dividend Growth (25 pts): Growing dividends protect against inflation
        - Valuation (25 pts): Lower P/E ratios indicate better value
        - Safety Score (25 pts): Safer dividends are more reliable
        
        #### Screening Filters:
        - **Min Dividend Yield**: Minimum annual dividend yield percentage
        - **Max Payout Ratio**: Maximum percentage of earnings paid as dividends
        - **Min Market Cap**: Minimum company size (larger companies often more stable)
        - **Min ROE**: Minimum return on equity (efficiency measure)
        - **Max Debt/Equity**: Maximum debt relative to equity (risk measure)
        - **Min Current Ratio**: Minimum liquidity ratio (ability to pay short-term debts)
        - **Min Dividend Growth**: Minimum 1-year dividend growth rate
        
        #### Data Sources:
        - Financial data: Alpha Vantage API
        - Real-time pricing and fundamental data
        - Historical dividend payments
        - Income statements and balance sheets
        
        **Note**: API rate limits may cause delays. Results are cached for 1 hour to improve performance.
        """)
    
    # API usage information
    st.sidebar.markdown("---")
    st.sidebar.subheader("📡 API Information")
    st.sidebar.info("Using Alpha Vantage API for real-time financial data")
    st.sidebar.warning("⚠️ API has rate limits. Large screenings may take time.")
    
    # Quick stock lookup in sidebar
    st.sidebar.subheader("🔍 Quick Lookup")
    quick_symbol = st.sidebar.text_input("Stock Symbol", "").upper()
    if st.sidebar.button("Quick Analysis") and quick_symbol:
        with st.spinner(f"Analyzing {quick_symbol}..."):
            overview = get_company_overview(quick_symbol)
            if overview:
                dividend_data = get_dividend_data(quick_symbol)
                income_data = get_income_statement(quick_symbol)
                metrics = calculate_dividend_metrics(overview, dividend_data, income_data)
                
                st.sidebar.success(f"**{metrics['name']}**")
                st.sidebar.metric("Div Yield", f"{metrics['dividend_yield']:.2f}%")
                st.sidebar.metric("Safety Score", f"{metrics['dividend_safety_score']:.0f}/100")
                st.sidebar.metric("Investment Score", f"{metrics['investment_score']:.0f}/100")
            else:
                st.sidebar.error("Symbol not found")