# /Users/cameronroberts/Finances/dividends/tabs/forecast.py
# Complete updated code (2025-04-25)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

# --- statsmodels is the core forecasting library now ---
try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    STATSMODELS_INSTALLED = True
except ImportError:
    st.error("Core forecasting library `statsmodels` is missing! Please install it (`pip install statsmodels`)")
    STATSMODELS_INSTALLED = False
# ---------------------------

# --- Helper Functions ---

def format_currency(value: float, currency_code: str) -> str:
    """Basic currency formatter"""
    symbol_map = {"GBP": "£", "USD": "$", "EUR": "€"}
    symbol = symbol_map.get(currency_code, "")
    # This function is now primarily for non-Plotly formatting needs
    # as Plotly formatting is handled directly in hovertemplate
    try:
        return f"{symbol}{float(value):,.2f}"
    except (ValueError, TypeError):
        # Handle cases where input might not be purely numeric initially
        return f"{symbol}{value}"


# --- Forecasting Functions ---

@st.cache_data
def statsmodels_sarimax_forecast(
    monthly_data: pd.DataFrame, forecast_months: int
) -> Tuple[Optional[pd.DataFrame], bool]:
    """
    SARIMAX forecasting model using statsmodels with fixed orders.

    Args:
        monthly_data: DataFrame with 'Date' (datetime) and 'Total' (float) columns.
        forecast_months: Number of months to forecast ahead.

    Returns:
        A tuple containing:
        - DataFrame with 'Date', 'Forecast', 'Lower_CI', 'Upper_CI' if successful, else None.
        - Boolean indicating success.
    """
    if not STATSMODELS_INSTALLED:
        return None, False

    try:
        # Prepare training data - use last 60 months or all if less
        num_months_for_training = min(60, len(monthly_data))
        training_data_series = monthly_data['Total'].iloc[-num_months_for_training:]

        # Handle potential zero or negative values before log transform
        if (training_data_series <= 1e-6).any(): # Use a small threshold > 0
             st.warning("SARIMAX: Zeros/Negatives found. Applying log transform might be unstable or fail. Attempting without log transform and simplified orders.")
             y_train = training_data_series
             apply_log = False
             # Use simpler non-seasonal order
             model_order = (1, 1, 1) # ARIMA(p,d,q)
             seasonal_order = (0, 0, 0, 0) # No seasonality
        else:
             y_train = np.log(training_data_series)
             apply_log = True
             # Reasonable starting orders for seasonal data - MAY NEED TUNING for better accuracy
             model_order = (1, 1, 1)          # ARIMA(p,d,q)
             seasonal_order = (1, 1, 0, 12)   # SARIMA(P,D,Q,m)

        st.info(f"SARIMAX using fixed orders: order={model_order}, seasonal_order={seasonal_order}. Log applied: {apply_log}")

        # Fit SARIMAX model
        model = SARIMAX(
            y_train,
            order=model_order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        model_fit = model.fit(disp=False, maxiter=200) # Suppress convergence output, increase iterations

        # Forecast using get_forecast for confidence intervals
        forecast_obj = model_fit.get_forecast(steps=forecast_months)
        forecast_values_log = forecast_obj.predicted_mean
        conf_int_log = forecast_obj.conf_int(alpha=0.05) # 95% CI

        # Inverse transform if log was applied
        if apply_log:
            forecast_values = np.exp(forecast_values_log)
            lower_ci = np.exp(conf_int_log.iloc[:, 0])
            upper_ci = np.exp(conf_int_log.iloc[:, 1])
        else:
            forecast_values = forecast_values_log
            lower_ci = conf_int_log.iloc[:, 0]
            upper_ci = conf_int_log.iloc[:, 1]

        # Generate forecast dates
        last_date = monthly_data['Date'].iloc[-1]
        forecast_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=forecast_months,
            freq='M' # Use month-end frequency
        )

        forecasted_data = pd.DataFrame({
            'Date': forecast_dates,
            'Forecast': forecast_values,
            'Lower_CI': lower_ci,
            'Upper_CI': upper_ci
        })

        # Ensure forecast is not negative
        forecasted_data['Forecast'] = forecasted_data['Forecast'].clip(lower=0)
        forecasted_data['Lower_CI'] = forecasted_data['Lower_CI'].clip(lower=0)
        forecasted_data['Upper_CI'] = forecasted_data['Upper_CI'].clip(lower=0)

        return forecasted_data, True
    except Exception as e:
        st.error(f"Statsmodels SARIMAX forecasting failed: {e}")
        import traceback
        st.error(traceback.format_exc()) # More detailed error for debugging
        return None, False


@st.cache_data
def holtwinters_forecast(
    monthly_data: pd.DataFrame, forecast_months: int
) -> Tuple[Optional[pd.DataFrame], bool]:
    """
    Holt-Winters forecasting model with error handling and approximate CIs.
    """
    if not STATSMODELS_INSTALLED:
        return None, False

    try:
        # Prepare training data - use the last 36 months or all if less
        num_months_for_training = min(36, len(monthly_data))
        training_data = monthly_data['Total'].iloc[-num_months_for_training:]

        # Ensure data is suitable
        if training_data.isnull().any() or len(training_data) < 12:
             st.warning("Holt-Winters: Insufficient or invalid data.")
             return None, False

        # Fit Holt-Winters model
        hw_model = ExponentialSmoothing(
            training_data,
            trend='add',       # Consider 'mul' if trend is multiplicative
            seasonal='add',    # Consider 'mul' if seasonality is multiplicative
            seasonal_periods=12,
            damped_trend=True  # Helps prevent unrealistic long-term explosion
        )
        hw_fit = hw_model.fit()

        # Forecast
        hw_forecast_values = hw_fit.forecast(steps=forecast_months)

        # Generate forecast dates
        last_date = monthly_data['Date'].iloc[-1]
        forecast_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=forecast_months,
            freq='M' # Use month-end frequency
        )

        forecasted_data = pd.DataFrame({
            'Date': forecast_dates,
            'Forecast': hw_forecast_values
        })

        # Approximate Confidence Intervals using standard deviation of residuals
        forecast_std_err = np.std(hw_fit.resid)
        forecasted_data['Lower_CI'] = forecasted_data['Forecast'] - 1.96 * forecast_std_err
        forecasted_data['Upper_CI'] = forecasted_data['Forecast'] + 1.96 * forecast_std_err

        # Ensure forecast is not negative
        forecasted_data['Forecast'] = forecasted_data['Forecast'].clip(lower=0)
        forecasted_data['Lower_CI'] = forecasted_data['Lower_CI'].clip(lower=0)
        forecasted_data['Upper_CI'] = forecasted_data['Upper_CI'].clip(lower=0)

        return forecasted_data, True
    except Exception as e:
        st.warning(f"Holt-Winters forecasting failed: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None, False


# --- Display Functions ---

def display_forecast(
    forecasted_data: pd.DataFrame,
    monthly_data: pd.DataFrame,
    currency: str,
    theme: str,
    method_name: str,
    # model_params arg kept for signature consistency but not used for fixed models
    model_params: Optional[str] = None
):
    """Helper function to display forecast results visualization and stats."""
    st.subheader(f"Dividend Forecast ({method_name})")
    if method_name == "SARIMAX":
        st.caption("Note: Using fixed SARIMAX parameters. Accuracy may vary.")

    # Combine actual and forecasted data for plotting
    historical_for_plot = monthly_data[['Date', 'Total']].rename(columns={'Total': 'Actual'})
    historical_for_plot['Date'] = pd.to_datetime(historical_for_plot['Date'])
    forecasted_data['Date'] = pd.to_datetime(forecasted_data['Date'])

    # --- Get Currency Symbol for Plotly Formatting ---
    symbol_map = {"GBP": "£", "USD": "$", "EUR": "€"}
    symbol = symbol_map.get(currency, "")
    # -------------------------------------------------

    # Plot the forecast
    fig_forecast = go.Figure()

    # Add actual data as bars
    fig_forecast.add_trace(go.Bar(
        x=historical_for_plot['Date'],
        y=historical_for_plot['Actual'],
        name='Actual Dividends',
        marker_color='rgba(78, 141, 245, 0.8)',
        # Use Plotly's formatting with Python f-string for symbol
        hovertemplate=f'<b>Date</b>: %{{x|%b %Y}}<br><b>Actual</b>: {symbol}%{{y:,.2f}}<extra></extra>'
    ))

    # Add forecast as a line with markers
    fig_forecast.add_trace(go.Scatter(
        x=forecasted_data['Date'],
        y=forecasted_data['Forecast'],
        name='Forecasted Dividends',
        mode='lines+markers',
        line=dict(color='rgba(255, 165, 0, 1)', width=2.5),
        marker=dict(size=5),
        hovertemplate=f'<b>Date</b>: %{{x|%b %Y}}<br><b>Forecast</b>: {symbol}%{{y:,.2f}}<extra></extra>'
    ))

    # Add confidence interval
    ci_name = "95% Confidence Interval"
    if method_name == "Holt-Winters":
        ci_name += " (Approximate)" # Label HW CIs as approximate

    fig_forecast.add_trace(go.Scatter(
        x=pd.concat([forecasted_data['Date'], forecasted_data['Date'].iloc[::-1]]),
        y=pd.concat([forecasted_data['Upper_CI'], forecasted_data['Lower_CI'].iloc[::-1]]),
        fill='toself',
        fillcolor='rgba(255, 165, 0, 0.2)',
        line=dict(color='rgba(255, 255, 255, 0)'),
        hoverinfo='skip', # Don't show hover for the fill area
        showlegend=True,
        name=ci_name
    ))

    # Update layout
    fig_forecast.update_layout(
        title=f"{len(forecasted_data)}-Month Dividend Forecast ({method_name})",
        template="plotly_white" if theme == "Light" else "plotly_dark",
        xaxis=dict(
            title="Date",
            tickangle=-45,
            tickformat="%b %Y",
            # Dynamically adjust range
            range=[historical_for_plot['Date'].iloc[-24] if len(historical_for_plot) > 24 else historical_for_plot['Date'].iloc[0],
                   forecasted_data['Date'].iloc[-1]]
        ),
        yaxis=dict(title=f"Dividend Amount ({currency})"),
        hovermode="x unified", # Show tooltips for all traces at a given x
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    st.plotly_chart(fig_forecast, use_container_width=True)

    # --- Forecast Statistics ---
    st.markdown("---")
    st.subheader("Forecast Summary Statistics")
    col1, col2, col3 = st.columns(3)

    total_forecast = forecasted_data['Forecast'].sum()
    monthly_avg_forecast = forecasted_data['Forecast'].mean()

    with col1:
        st.metric(
            f"Total Forecasted ({len(forecasted_data)} mo.)",
            format_currency(total_forecast, currency) # Use helper here for metric display
        )

    with col2:
        st.metric(
            "Average Monthly Forecast",
            format_currency(monthly_avg_forecast, currency) # Use helper here
        )

    with col3:
        growth_rate_str = "Insufficient data"
        if len(historical_for_plot) >= 12 and len(forecasted_data) >= 12:
            last_12m_actual_sum = historical_for_plot['Actual'].tail(12).sum()
            next_12m_forecast_sum = forecasted_data['Forecast'].head(12).sum()
            # Check for division by zero or near-zero
            if abs(last_12m_actual_sum) > 1e-6:
                growth_rate = ((next_12m_forecast_sum - last_12m_actual_sum) / last_12m_actual_sum) * 100
                growth_rate_str = f"{growth_rate:.1f}%"
            else:
                 growth_rate_str = "N/A (prev year zero)"

        st.metric(
            "Projected 1yr Growth (vs last 12m)",
            growth_rate_str
        )

    # --- Forecast Data Table ---
    with st.expander("View Forecast Data Table"):
        forecast_table = forecasted_data.copy()
        forecast_table['Date'] = forecast_table['Date'].dt.strftime('%b %Y')
        # Use helper function for display formatting in table
        forecast_table['Forecast'] = forecast_table['Forecast'].apply(lambda x: format_currency(x, currency))
        forecast_table['Lower CI'] = forecast_table['Lower_CI'].apply(lambda x: format_currency(x, currency))
        forecast_table['Upper CI'] = forecast_table['Upper_CI'].apply(lambda x: format_currency(x, currency))
        forecast_table = forecast_table[['Date', 'Forecast', 'Lower CI', 'Upper CI']]
        st.dataframe(forecast_table, use_container_width=True, hide_index=True)

    # --- Forecasted Annual Income ---
    st.markdown("---")
    st.subheader("Forecasted Annual Income")

    # Group forecasts by year
    forecasted_data['Year'] = forecasted_data['Date'].dt.year
    annual_forecast = forecasted_data.groupby('Year')['Forecast'].sum().reset_index()

    # Get historical annual totals
    monthly_data['Year'] = monthly_data['Date'].dt.year # Ensure Year column exists
    historical_annual = monthly_data.groupby('Year')['Total'].sum().reset_index()
    historical_annual.columns = ['Year', 'Total']

    # Combine historical and forecast
    historical_annual['Amount'] = historical_annual['Total']
    annual_forecast['Amount'] = annual_forecast['Forecast']
    historical_annual['Type'] = 'Actual'
    annual_forecast['Type'] = 'Forecast'

    combined_annual = pd.concat([
        historical_annual[['Year', 'Amount', 'Type']],
        annual_forecast[['Year', 'Amount', 'Type']]
    ], ignore_index=True).drop_duplicates(subset=['Year'], keep='last') # Keep forecast if year overlaps

    combined_annual = combined_annual.sort_values(by='Year')

    # Plot annual totals and forecasts
    fig_annual = px.bar(
        combined_annual,
        x='Year',
        y='Amount',
        color='Type',
        title="Annual Dividend Income (Historical & Forecast)",
        template="plotly_white" if theme == "Light" else "plotly_dark",
        color_discrete_map={'Actual': 'rgba(78, 141, 245, 0.8)', 'Forecast': 'rgba(255, 165, 0, 0.8)'},
        labels={'Amount': f'Annual Dividend Income ({currency})'},
        text_auto='.2s' # Display bar values using SI notation
    )

    fig_annual.update_layout(
        height=400,
        xaxis=dict(title="Year", type='category'), # Treat year as category
        yaxis=dict(title=f"Annual Dividend Income ({currency})"),
        legend_title_text='Income Type',
        font=dict(color="#333" if theme == "Light" else "#EEE"),
    )
    fig_annual.update_traces(textposition='outside')

    st.plotly_chart(fig_annual, use_container_width=True)


def display_fi_calculator(
    forecasted_data: pd.DataFrame,
    currency: str,
    method_name: str # Used for unique keys: "SARIMAX" or "HoltWinters"
):
    """Helper function to display Financial Independence calculator based on forecast."""
    # This function remains largely unchanged, uses forecasted_data structure
    st.markdown("---")
    st.subheader(f"Financial Independence Projection ({method_name})")
    st.caption("Estimate how forecasted dividends cover expenses.")

    col1, col2 = st.columns(2)

    with col1:
        # Unique key using method_name and currency
        monthly_expenses_key = f"fi_expenses_{method_name}_{currency}"
        monthly_expenses = st.number_input(
            f"Your Estimated Monthly Expenses ({currency})",
            min_value=0.0,
            value=2000.0,
            step=100.0,
            format="%.2f",
            key=monthly_expenses_key,
            help="Enter your target monthly spending in retirement."
        )
        annual_expenses = monthly_expenses * 12
        if annual_expenses > 0:
            st.write(f"Target Annual Expenses: **{format_currency(annual_expenses, currency)}**")
        else:
             st.write("Enter monthly expenses to calculate FI metrics.")

    with col2:
        withdrawal_rate_key = f"withdrawal_rate_{method_name}_{currency}"
        withdrawal_rate = st.slider(
            "Target Safe Withdrawal Rate (%)",
            min_value=1.0,
            max_value=10.0,
            value=4.0,
            step=0.1,
            help="Percentage of your portfolio you aim to withdraw annually.",
            key=withdrawal_rate_key
        )
        # Calculate FI target only if inputs are valid
        fi_target = (annual_expenses / (withdrawal_rate / 100)) if withdrawal_rate > 0 and annual_expenses > 0 else 0
        if annual_expenses > 0:
            st.write(f"FI Portfolio Target: **{format_currency(fi_target, currency)}**")

    if annual_expenses <= 0:
        st.info("Please enter your estimated monthly expenses above to see the coverage analysis.")
        return # Don't proceed if no expenses entered

    # --- Dividend Coverage Calculation ---
    st.markdown("#### Dividend Coverage of Annual Expenses")

    # Use average of next 12 months forecast
    projected_annual_dividend = 0
    if len(forecasted_data) > 0:
        if len(forecasted_data) >= 12:
            avg_next_12m_dividend = forecasted_data['Forecast'].head(12).mean()
            projected_annual_dividend = avg_next_12m_dividend * 12
            st.write(f"Projected Annual Dividend (next 12m avg): {format_currency(projected_annual_dividend, currency)}")
        else:
            # Annualize if forecast is shorter than 12 months
            avg_forecast_dividend = forecasted_data['Forecast'].mean()
            projected_annual_dividend = avg_forecast_dividend * 12
            st.warning(f"Forecast is less than 12 months. Annualizing based on {len(forecasted_data)} months average.")
            st.write(f"Projected Annual Dividend (annualized): {format_currency(projected_annual_dividend, currency)}")
    else:
        st.warning("No forecast data available to calculate coverage.")


    coverage_percent = (projected_annual_dividend / annual_expenses) * 100 if annual_expenses > 0 else 100
    remaining_gap = max(0, annual_expenses - projected_annual_dividend) # Ensure gap isn't negative

    st.progress(min(coverage_percent / 100, 1.0)) # Cap progress at 100%

    col1_fi, col2_fi = st.columns(2)

    with col1_fi:
        st.metric(
            "Dividend Coverage",
            f"{coverage_percent:.1f}%",
            help="Percentage of target annual expenses covered by projected annual dividends."
        )

    with col2_fi:
        st.metric(
            "Annual Income Gap",
            format_currency(remaining_gap, currency),
            help="Additional annual income needed to reach your expense target."
        )

    # --- Time to FI Estimation ---
    st.markdown("#### Time to FI Estimate (Dividends Only)")
    st.caption("Note: Simplified projection based *only* on dividend growth, does not account for reinvestment or new capital.")

    if remaining_gap > 1e-6: # Check if there is a meaningful gap
        additional_portfolio_needed = (remaining_gap / (withdrawal_rate / 100)) if withdrawal_rate > 0 else 0
        st.write(f"Additional portfolio needed to cover gap (at {withdrawal_rate:.1f}% SWR): "
                 f"**{format_currency(additional_portfolio_needed, currency)}**")

        # Estimate growth rate based on forecast trend (needs >= 2 years)
        forecasted_annual_growth = 0
        if len(forecasted_data) >= 24:
            first_year_avg = forecasted_data['Forecast'].iloc[:12].mean()
            second_year_avg = forecasted_data['Forecast'].iloc[12:24].mean()
            # Avoid division by zero/small numbers
            if abs(first_year_avg) > 1e-6:
                 forecasted_annual_growth = ((second_year_avg / first_year_avg) - 1) * 100

        if forecasted_annual_growth > 0.1: # Require some minimal positive growth
            st.write(f"Projected annual dividend growth rate (based on forecast): **{forecasted_annual_growth:.1f}%**")

            # Calculate years to FI using logarithm formula
            current_level = projected_annual_dividend
            target_level = annual_expenses
            try:
                 # Ensure valid inputs for log
                 if target_level > 0 and current_level > 0 and (1 + forecasted_annual_growth/100) > 1:
                    years_to_fi = np.log(target_level / current_level) / np.log(1 + forecasted_annual_growth/100)
                    if years_to_fi > 0 and years_to_fi < 100: # Check for realistic timeframe
                        st.success(f"Estimated **~{years_to_fi:.1f} years** to reach expense target with dividends alone at this growth rate.")
                    elif years_to_fi >= 100:
                         st.warning("Estimated >100 years to reach target at this growth rate.")
                    # If years_to_fi <= 0, it means current projection already meets/exceeds target
                    elif years_to_fi <= 0:
                         # This case should be caught by remaining_gap check, but added for safety
                         st.info("Projected dividend income already meets or exceeds target expenses.")
                 else:
                    st.warning("Cannot calculate time to FI (growth rate too low or zero starting income).")

            except (ValueError, OverflowError, RuntimeWarning) as calc_e:
                st.warning(f"Could not calculate time to FI due to numerical issues: {calc_e}")
        else:
            st.info("Insufficient forecast data (need >= 24 months) or growth rate too low to project a reliable FI timeline based on dividend growth alone.")
    else:
        # This case handles when remaining_gap is zero or negligible
        st.success("Congratulations! Your projected annual dividend income meets or exceeds your target annual expenses.")


# --- Main Tab Function ---

def show_forecast_tab(
    monthly_data: pd.DataFrame,
    currency: str,
    theme: str,
    **kwargs: Dict[str, Any] # Catch any extra args like format_currency if passed from main app
):
    """
    Display the Forecast tab content using statsmodels SARIMAX and Holt-Winters.
    """
    st.subheader("Dividend Forecast Analysis")
    st.caption("Use time series models to project future dividend income.")

    if not STATSMODELS_INSTALLED:
         # Error already shown in import block
         return

    # Forecast settings
    forecast_months = st.slider(
        "Select Forecast Horizon (Months)",
        min_value=6,
        max_value=36, # Max forecast horizon
        value=12,     # Default forecast horizon
        step=3,
        help="How many months into the future would you like to forecast?"
        )

    # Check data sufficiency
    min_data_points = 15 # Minimum months needed for seasonal models
    if len(monthly_data) < min_data_points:
        st.warning(f"⚠️ Not enough historical data for reliable forecasting. Need at least {min_data_points} months of data. You currently have {len(monthly_data)}.")
        return

    # Prepare data (ensure Date is datetime, sorted, and NaN handled)
    try:
        monthly_data['Date'] = pd.to_datetime(monthly_data['Date'])
        monthly_data = monthly_data.sort_values('Date').reset_index(drop=True)
        # Simple fill with 0 for missing months, consider interpolation if appropriate
        monthly_data['Total'] = monthly_data['Total'].fillna(0)
    except Exception as e:
        st.error(f"Error preparing data for forecasting: {e}")
        return

    # Tabs for different models
    tab1, tab2 = st.tabs(["SARIMAX Forecast", "Holt-Winters Forecast"])

    # Tab 1: SARIMAX (statsmodels)
    with tab1:
        with st.spinner("Generating SARIMAX forecast..."):
            # Pass a copy to cached function to prevent mutation issues
            forecasted_data_sarimax, success_sarimax = statsmodels_sarimax_forecast(
                monthly_data.copy(),
                forecast_months
            )

        if not success_sarimax or forecasted_data_sarimax is None:
            # Errors/warnings are typically displayed within the forecast function
            st.error("SARIMAX forecasting process failed.")
        else:
            display_forecast(
                forecasted_data_sarimax,
                monthly_data,
                currency,
                theme,
                "SARIMAX" # Method name for display
            )
            display_fi_calculator(
                forecasted_data_sarimax,
                currency,
                "SARIMAX" # Unique key part for widgets
            )

    # Tab 2: Holt-Winters
    with tab2:
        with st.spinner("Generating Holt-Winters forecast..."):
            # Pass a copy to cached function
            forecasted_data_hw, success_hw = holtwinters_forecast(
                 monthly_data.copy(),
                 forecast_months
            )

        if not success_hw or forecasted_data_hw is None:
             # Errors/warnings displayed within the forecast function
             st.error("Holt-Winters forecasting process failed.")
        else:
            display_forecast(
                forecasted_data_hw,
                monthly_data,
                currency,
                theme,
                "Holt-Winters"
            )
            display_fi_calculator(
                forecasted_data_hw,
                currency,
                "HoltWinters" # Unique key part
            )

