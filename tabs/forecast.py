import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Forecasting functions
@st.cache_data
def simple_moving_average_forecast(monthly_data, forecast_months):
    """Simple moving average forecast with seasonal adjustment"""
    # Calculate recent average
    recent_months = min(12, len(monthly_data))
    recent_avg = monthly_data['Total'].tail(recent_months).mean()
    
    # Generate forecast dates
    last_date = monthly_data['Date'].iloc[-1]
    forecast_dates = pd.date_range(
        start=last_date + pd.DateOffset(months=1),
        periods=forecast_months,
        freq='M'
    )
    
    # Simple forecast with seasonal adjustment
    if len(monthly_data) >= 12:
        # Calculate monthly seasonal factors
        monthly_data['Month'] = monthly_data['Date'].dt.month
        seasonal_factors = monthly_data.groupby('Month')['Total'].mean() / monthly_data['Total'].mean()
        
        forecasts = []
        for date in forecast_dates:
            month = date.month
            seasonal_factor = seasonal_factors.get(month, 1.0)
            forecasts.append(recent_avg * seasonal_factor)
    else:
        # Without enough data for seasonality
        forecasts = [recent_avg] * len(forecast_dates)
    
    forecasted_data = pd.DataFrame({
        'Date': forecast_dates,
        'Forecast': forecasts
    })
    
    # Add simple confidence intervals
    forecasted_data['Lower_CI'] = forecasted_data['Forecast'] * 0.8
    forecasted_data['Upper_CI'] = forecasted_data['Forecast'] * 1.2
    
    return forecasted_data

@st.cache_data
def sarimax_forecast(monthly_data, forecast_months):
    """SARIMAX forecasting model with error handling"""
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        
        # Prepare training data - use the last 36 months or all if less
        num_months_for_training = min(36, len(monthly_data))
        training_data = monthly_data.iloc[-num_months_for_training:]
        
        # Log transformation to stabilize variance
        training_data['Log_Total'] = np.log(training_data['Total'])
        
        # Fit SARIMAX model
        model = SARIMAX(
            training_data['Log_Total'],
            order=(0, 1, 1),
            seasonal_order=(0, 0, 1, 12)
        )
        model_fit = model.fit(disp=False, maxiter=200)
        
        # Forecast
        forecast_log = model_fit.forecast(steps=forecast_months)
        forecast = np.exp(forecast_log)
        
        # Generate forecast dates
        last_date = training_data['Date'].iloc[-1]
        forecast_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=forecast_months,
            freq='M'
        )
        
        forecasted_data = pd.DataFrame({
            'Date': forecast_dates,
            'Forecast': forecast
        })
        
        # Calculate confidence intervals
        forecasted_data['Lower_CI'] = forecasted_data['Forecast'] * 0.85
        forecasted_data['Upper_CI'] = forecasted_data['Forecast'] * 1.15
        
        return forecasted_data, True
    except Exception as e:
        st.warning(f"SARIMAX forecasting failed: {e}")
        return None, False

@st.cache_data
def holtwinters_forecast(monthly_data, forecast_months):
    """Holt-Winters forecasting model with error handling"""
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        
        # Prepare training data
        num_months_for_training = min(36, len(monthly_data))
        training_data = monthly_data.iloc[-num_months_for_training:]
        
        # Fit Holt-Winters model
        hw_model = ExponentialSmoothing(
            training_data['Total'],
            trend='add',
            seasonal='add',
            seasonal_periods=12,
            damped_trend=True
        )
        hw_fit = hw_model.fit()
        
        # Forecast
        hw_forecast = hw_fit.forecast(steps=forecast_months)
        
        # Generate forecast dates
        last_date = training_data['Date'].iloc[-1]
        forecast_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=forecast_months,
            freq='M'
        )
        
        forecasted_data = pd.DataFrame({
            'Date': forecast_dates,
            'Forecast': hw_forecast.values
        })
        
        # Calculate confidence intervals (simplified approach)
        forecasted_data['Lower_CI'] = forecasted_data['Forecast'] * 0.85
        forecasted_data['Upper_CI'] = forecasted_data['Forecast'] * 1.15
        
        return forecasted_data, True
    except Exception as e:
        st.warning(f"Holt-Winters forecasting failed: {e}")
        return None, False

def show_forecast_tab(df, monthly_data, currency, theme, current_date, current_year, current_month, 
                     format_currency, **kwargs):
    """
    Display the Forecast tab content
    
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
    # Forecast settings
    forecast_months = st.slider("Forecast Months", 6, 24, 12)
    
    # Check if we have enough data for forecasting
    if len(monthly_data) < 12:
        st.warning("⚠️ Not enough historical data for reliable forecasting. Need at least 12 months of data.")
        st.info("Using simplified forecast model due to limited data.")
        forecast_method = "simple"
    else:
        forecast_method = st.radio(
            "Select Forecasting Method",
            ["SARIMAX (Seasonal ARIMA)", "Holt-Winters", "Simple Moving Average"],
            index=0,
            horizontal=True
        )
    
    with st.spinner("Generating forecast..."):
        if forecast_method == "SARIMAX (Seasonal ARIMA)" and len(monthly_data) >= 24:
            # Using local sarimax_forecast function
            forecasted_data, success = sarimax_forecast(monthly_data, forecast_months)
            if not success:
                st.warning("SARIMAX modeling failed. Falling back to Simple Moving Average.")
                # Using local simple_moving_average_forecast function
                forecasted_data = simple_moving_average_forecast(monthly_data, forecast_months)
            
        elif forecast_method == "Holt-Winters" and len(monthly_data) >= 24:
            # Using local holtwinters_forecast function
            forecasted_data, success = holtwinters_forecast(monthly_data, forecast_months)
            if not success:
                st.warning("Holt-Winters modeling failed. Falling back to Simple Moving Average.")
                # Using local simple_moving_average_forecast function
                forecasted_data = simple_moving_average_forecast(monthly_data, forecast_months)
        else:
            # Simple moving average forecast using local function
            forecast_method = "Simple Moving Average"
            forecasted_data = simple_moving_average_forecast(monthly_data, forecast_months)
    
    # Display forecast results
    st.subheader(f"Dividend Forecast ({forecast_method})")
    
    # Combine actual and forecasted data for plotting
    historical_for_plot = monthly_data[['Date', 'Total']].rename(columns={'Total': 'Actual'})
    combined_data = pd.concat([
        historical_for_plot,
        forecasted_data
    ], ignore_index=True)
    
    # Plot the forecast
    fig_forecast = go.Figure()
    
    # Add actual data as bars
    fig_forecast.add_trace(go.Bar(
        x=historical_for_plot['Date'],
        y=historical_for_plot['Actual'],
        name='Actual',
        marker_color='rgba(78, 141, 245, 0.8)'
    ))
    
    # Add forecast as a line
    fig_forecast.add_trace(go.Scatter(
        x=forecasted_data['Date'],
        y=forecasted_data['Forecast'],
        name='Forecast',
        mode='lines+markers',
        line=dict(color='rgba(255, 165, 0, 1)', width=3)
    ))
    
    # Add confidence interval
    fig_forecast.add_trace(go.Scatter(
        x=pd.concat([forecasted_data['Date'], forecasted_data['Date'].iloc[::-1]]),
        y=pd.concat([forecasted_data['Upper_CI'], forecasted_data['Lower_CI'].iloc[::-1]]),
        fill='toself',
        fillcolor='rgba(255, 165, 0, 0.2)',
        line=dict(color='rgba(255, 165, 0, 0)'),
        hoverinfo='skip',
        showlegend=True,
        name='95% Confidence Interval'
    ))
    
    # Update layout
    fig_forecast.update_layout(
        title=f"{forecast_months}-Month Dividend Forecast",
        template="plotly_white" if theme == "Light" else "plotly_dark",
        xaxis=dict(
            title="Date",
            tickangle=-45,
            tickformat="%b %Y"
        ),
        yaxis=dict(title=f"Dividend Amount ({currency})"),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )
    
    st.plotly_chart(fig_forecast, use_container_width=True)
    
    # Forecast statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_forecast = forecasted_data['Forecast'].sum()
        st.metric(
            "Total Forecasted Dividends",
            format_currency(total_forecast, currency)
        )
        
    with col2:
        monthly_avg_forecast = forecasted_data['Forecast'].mean()
        st.metric(
            "Average Monthly Forecast",
            format_currency(monthly_avg_forecast, currency)
        )
        
    with col3:
        # Calculate growth rate
        if len(historical_for_plot) >= 12:
            recent_actual = historical_for_plot['Actual'].tail(12).sum()
            forecast_first_year = forecasted_data['Forecast'].head(12).sum()
            growth_rate = ((forecast_first_year - recent_actual) / recent_actual) * 100
            st.metric(
                "Projected Annual Growth",
                f"{growth_rate:.1f}%"
            )
        else:
            st.metric(
                "Projected Annual Growth",
                "Insufficient data"
            )
    
    # Forecast data table
    with st.expander("View Forecast Data Table"):
        forecast_table = forecasted_data.copy()
        forecast_table['Date'] = forecast_table['Date'].dt.strftime('%b %Y')
        forecast_table['Forecast'] = forecast_table['Forecast'].apply(lambda x: format_currency(x, currency))
        forecast_table['Lower CI'] = forecast_table['Lower_CI'].apply(lambda x: format_currency(x, currency))
        forecast_table['Upper CI'] = forecast_table['Upper_CI'].apply(lambda x: format_currency(x, currency))
        forecast_table = forecast_table[['Date', 'Forecast', 'Lower CI', 'Upper CI']]
        st.dataframe(forecast_table, use_container_width=True)
    
    # Forecasted Annual Income
    st.subheader("Forecasted Annual Income")
    
    # Group forecasts by year
    forecasted_data['Year'] = forecasted_data['Date'].dt.year
    annual_forecast = forecasted_data.groupby('Year')['Forecast'].sum().reset_index()
    
    # Get historical annual totals
    historical_annual = df.groupby('Year')['Total'].sum().reset_index()
    
    # Combine historical and forecast
    combined_annual = pd.concat([
        historical_annual.rename(columns={'Total': 'Amount'}),
        annual_forecast.rename(columns={'Forecast': 'Amount'})
    ], ignore_index=True).drop_duplicates(subset=['Year'])
    
    combined_annual['Type'] = combined_annual['Year'].apply(
        lambda x: 'Forecast' if x > datetime.now().year else 'Actual'
    )
    
    # Plot annual totals and forecasts
    fig_annual = px.bar(
        combined_annual,
        x='Year',
        y='Amount',
        color='Type',
        title="Annual Dividend Income (Historical & Forecast)",
        template="plotly_white" if theme == "Light" else "plotly_dark",
        color_discrete_map={'Actual': 'rgba(78, 141, 245, 0.8)', 'Forecast': 'rgba(255, 165, 0, 0.8)'}
    )
    
    fig_annual.update_layout(
        height=400,
        xaxis=dict(title="Year"),
        yaxis=dict(title=f"Annual Dividend Income ({currency})"),
        font=dict(color='black')
    )
    
    st.plotly_chart(fig_annual, use_container_width=True)
    
    # Financial Independence Calculator
    st.subheader("Financial Independence Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_expenses = st.number_input(
            "Monthly Expenses", 
            min_value=0.0, 
            value=2000.0, 
            step=100.0,
            format="%.2f",
            key="fi_expenses"
        )
        
        annual_expenses = monthly_expenses * 12
        
        st.write(f"Annual Expenses: {format_currency(annual_expenses, currency)}")
    
    with col2:
        withdrawal_rate = st.slider(
            "Safe Withdrawal Rate (%)", 
            min_value=1.0, 
            max_value=10.0, 
            value=4.0, 
            step=0.1,
            help="Percentage of portfolio you can safely withdraw each year"
        )
        
        # Calculate FI target
        fi_target = (annual_expenses / withdrawal_rate) * 100
        
        st.write(f"Financial Independence Target: {format_currency(fi_target, currency)}")
    
    # Now calculate the dividend coverage
    latest_annual_forecast = annual_forecast['Forecast'].iloc[-1] if len(annual_forecast) > 0 else 0
    
    coverage_percent = (latest_annual_forecast / annual_expenses) * 100 if annual_expenses > 0 else 0
    remaining_amount = annual_expenses - latest_annual_forecast
    
    # Create progress bar for dividend coverage
    st.subheader("Dividend Coverage of Annual Expenses")
    
    st.progress(min(coverage_percent / 100, 1.0))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Current Coverage",
            f"{coverage_percent:.1f}%",
            delta=None
        )
    
    with col2:
        st.metric(
            "Remaining Gap",
            format_currency(max(0, remaining_amount), currency),
            delta=None
        )
    
    # Additional portfolio needed
    if remaining_amount > 0:
        additional_portfolio = (remaining_amount / withdrawal_rate) * 100
        
        st.write(f"Additional portfolio needed: {format_currency(additional_portfolio, currency)} at {withdrawal_rate}% withdrawal rate")
        
        # Calculate time to FI with current growth rate
        if 'growth_rate' in locals() and growth_rate > 0:
            years_to_double = 72 / growth_rate  # Rule of 72
            
            st.write(f"At current growth rate of {growth_rate:.1f}%, your dividend income would double every {years_to_double:.1f} years")