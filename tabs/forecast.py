# /Users/cameronroberts/Finances/dividends/tabs/forecast.py
# Simplified & Refactored Code - Attempting more stable Fixed SARIMAX
# No pmdarima - 2025-05-01

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Tuple, Optional, Dict, Any, Callable
import traceback  # For detailed error logging
import warnings  # To suppress specific statsmodels warnings if needed

# --- Model Dependencies ---
STATSMODELS_INSTALLED = False
PROPHET_INSTALLED = False
SKTIME_INSTALLED = False

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    # Suppress common statsmodels warnings during fitting if desired
    from statsmodels.tools.sm_exceptions import ConvergenceWarning, SpecificationWarning

    warnings.simplefilter("ignore", ConvergenceWarning)
    warnings.simplefilter("ignore", SpecificationWarning)
    warnings.simplefilter(
        "ignore", UserWarning
    )  # Can sometimes hide useful info though
    STATSMODELS_INSTALLED = True
except ImportError:
    st.error(
        "`statsmodels` is required for SARIMAX & Holt-Winters. Please install it (`pip install statsmodels`)."
    )

try:
    from prophet import Prophet
    import logging

    logging.getLogger("prophet").setLevel(logging.WARNING)
    logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
    PROPHET_INSTALLED = True
except ImportError:
    pass

try:
    from sktime.forecasting.theta import ThetaForecaster

    SKTIME_INSTALLED = True
except ImportError:
    pass


# --- Helper Functions ---
# (format_currency, prepare_data remain unchanged from previous version)
def format_currency(value: float, currency_code: str) -> str:
    symbol_map = {"GBP": "£", "USD": "$", "EUR": "€"}
    symbol = symbol_map.get(currency_code, "")
    try:
        return f"{symbol}{float(value):,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}{value}"


def prepare_data(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    try:
        data_clean = df.copy()
        # Handle both Date/Time column names
        if "Date" in data_clean.columns:
            data_clean["Date"] = pd.to_datetime(data_clean["Date"])
        elif "Time" in data_clean.columns:
            data_clean["Date"] = pd.to_datetime(data_clean["Time"])
        else:
            return None

        data_clean = data_clean.sort_values("Date").reset_index(drop=True)

        # Handle both Total/Total_Sum column names
        if "Total_Sum" in data_clean.columns:
            data_clean["Total"] = pd.to_numeric(
                data_clean["Total_Sum"], errors="coerce"
            ).fillna(0.0)
        elif "Total" in data_clean.columns:
            data_clean["Total"] = pd.to_numeric(
                data_clean["Total"], errors="coerce"
            ).fillna(0.0)
        else:
            return None

        if not np.all(np.isfinite(data_clean["Total"])):
            return None
        return data_clean[["Date", "Total"]]
    except Exception:
        return None


# --- Forecasting Models ---


@st.cache_data(ttl=3600)
def run_sarimax_fixed(  # MODIFIED FOR STABILITY
    data: pd.DataFrame, forecast_months: int
) -> Tuple[Optional[pd.DataFrame], bool, Optional[str]]:
    """
    Runs SARIMAX forecast using simpler fixed orders and enforcing stability.
    No automatic log transform is applied.
    """
    if not STATSMODELS_INSTALLED:
        st.error("`statsmodels` is required for SARIMAX.")
        return None, False, "statsmodels not installed"

    try:
        training_data_series = data["Total"].astype(float)
        if len(training_data_series) < 24:  # Need more data for seasonal differencing
            st.warning(
                "SARIMAX: Less than 24 data points may make seasonal differencing unreliable."
            )

        # --- Define Simpler Fixed Orders & Enforce Stability ---
        # Assume first differencing (d=1) and seasonal differencing (D=1) are needed.
        # Use simple AR(1) for non-seasonal and SAR(1) for seasonal parts.
        model_order = (1, 1, 0)  # (p=1, d=1, q=0) -> AR(1) on differenced data
        seasonal_order = (
            1,
            1,
            0,
            12,
        )  # (P=1, D=1, Q=0, m=12) -> SAR(1) on seasonally differenced data
        model_params_str = f"Fixed (Stable Attempt) - Order: {model_order}, Seasonal: {seasonal_order}, Enforced: True"

        st.info(
            f"Using SARIMAX with: {model_params_str}. Enforcing stationarity/invertibility."
        )
        st.caption(
            "Model fitting might fail if data is unsuitable for these fixed orders & constraints."
        )

        # Fit SARIMAX model - NO log transform here
        model = SARIMAX(
            training_data_series,  # Use original data
            order=model_order,
            seasonal_order=seasonal_order,
            enforce_stationarity=True,  # CRUCIAL for stability
            enforce_invertibility=True,  # CRUCIAL for stability
            # simple_differencing=False # Default, handles initial conditions better
        )

        # Fit the model, catching potential errors due to enforcement/fixed orders
        try:
            # Suppress verbose output during fitting
            model_fit = model.fit(disp=False, maxiter=200)  # Increase iterations
        except (np.linalg.LinAlgError, ValueError, Exception) as fit_error:
            # Catch common fitting errors when constraints are enforced
            st.error("SARIMAX model fitting failed with fixed orders & enforcement.")
            st.error(f"Error details: {fit_error}")
            st.info(
                "This can happen if the fixed (p,d,q)(P,D,Q,m) orders are incompatible with the data structure under stability constraints. Consider trying different fixed orders or exploring models like Prophet/Holt-Winters."
            )
            # Optionally: Could try simpler orders like (0,1,1)(0,1,1,12) or non-seasonal (1,1,0)(0,0,0,0) here as a fallback
            return None, False, f"Fitting Failed: {model_params_str}"

        # Forecast using get_forecast for confidence intervals
        forecast_obj = model_fit.get_forecast(steps=forecast_months)
        forecast_values = forecast_obj.predicted_mean  # No inverse transform needed
        conf_int = forecast_obj.conf_int(alpha=0.05)  # 95% CI

        # Extract CI - ensure it's numpy array
        lower_ci = np.asarray(conf_int.iloc[:, 0])
        upper_ci = np.asarray(conf_int.iloc[:, 1])

        # Clip numeric numpy arrays *before* creating the DataFrame
        forecast_values = np.clip(forecast_values, 0, None)
        lower_ci = np.clip(lower_ci, 0, None)
        upper_ci = np.clip(upper_ci, 0, None)

        # Generate dates
        last_date = data["Date"].iloc[-1]
        forecast_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1), periods=forecast_months, freq="M"
        )

        # Create DataFrame
        forecast_df = pd.DataFrame(
            {
                "Date": forecast_dates,
                "Forecast": forecast_values,
                "Lower_CI": lower_ci,
                "Upper_CI": upper_ci,
            }
        )

        return forecast_df, True, model_params_str

    except Exception as e:
        st.error(f"An unexpected error occurred during SARIMAX forecasting: {e}")
        st.error(traceback.format_exc())  # Show detailed error
        return None, False, f"Failed Unexpectedly: {e}"


@st.cache_data(ttl=3600)
def run_prophet(  # Definition remains the same
    data: pd.DataFrame, forecast_months: int
) -> Tuple[Optional[pd.DataFrame], bool, Optional[str]]:
    """Runs forecast using Facebook Prophet."""
    if not PROPHET_INSTALLED:
        st.error("`prophet` is required...")
        return None, False, "prophet not installed"
    # ... (rest of prophet logic is identical to previous version) ...
    model_params_str = "Prophet Defaults (Yearly Seasonality)"
    try:
        prophet_data = data.rename(columns={"Date": "ds", "Total": "y"})
        prophet_data["y"] = prophet_data["y"].astype(float)
        prophet_data = prophet_data.dropna(subset=["ds", "y"])
        if len(prophet_data) < 12:
            st.warning("Prophet: < 12 data points.")
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode="additive",
        )
        model.fit(prophet_data)
        future = model.make_future_dataframe(periods=forecast_months, freq="M")
        forecast = model.predict(future)
        forecast_df = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(
            forecast_months
        )
        forecast_df = forecast_df.rename(
            columns={
                "ds": "Date",
                "yhat": "Forecast",
                "yhat_lower": "Lower_CI",
                "yhat_upper": "Upper_CI",
            }
        )
        numeric_cols = ["Forecast", "Lower_CI", "Upper_CI"]
        forecast_df[numeric_cols] = forecast_df[numeric_cols].clip(lower=0)
        return forecast_df, True, model_params_str
    except Exception as e:
        st.error(f"Prophet failed: {e}")
        st.error(traceback.format_exc())
        return None, False, f"Failed: {e}"


@st.cache_data(ttl=3600)
def run_holtwinters(  # Definition remains the same
    data: pd.DataFrame,
    forecast_months: int,
    trend: Optional[str],
    seasonal: Optional[str],
    damped: bool,
) -> Tuple[Optional[pd.DataFrame], bool, Optional[str]]:
    """Runs Holt-Winters forecast with specified parameters."""
    if not STATSMODELS_INSTALLED:
        st.error("`statsmodels` is required...")
        return None, False, "statsmodels not installed"
    # ... (rest of holt-winters logic is identical to previous version, including clipping fix) ...
    trend = trend if trend in ["add", "mul"] else None
    seasonal = seasonal if seasonal in ["add", "mul"] else None
    model_params_str = f"HW - Trend: {trend}, Seasonal: {seasonal}, Damped: {damped}"
    try:
        training_data = data["Total"].astype(float)
        added_constant = 0.0
        min_hw_months = 24 if seasonal else 12
        if len(training_data) < min_hw_months:
            st.warning(f"HW: < {min_hw_months} points.")
        if (trend == "mul" or seasonal == "mul") and (training_data <= 1e-6).any():
            st.warning("HW: Multiplicative + non-positive data. Adding 1.0.")
            training_data = training_data + 1.0
            added_constant = 1.0
        hw_model = ExponentialSmoothing(
            training_data,
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=12 if seasonal else None,
            damped_trend=damped,
        )
        hw_fit = hw_model.fit()
        forecast_values = hw_fit.forecast(steps=forecast_months)
        if added_constant > 0:
            forecast_values = forecast_values - added_constant
        resid = hw_fit.resid
        lower_ci = forecast_values
        upper_ci = forecast_values  # Defaults if resid invalid
        if resid is not None and len(resid) > 1 and np.all(np.isfinite(resid)):
            forecast_std_err = np.std(resid)
            lower_ci = forecast_values - 1.96 * forecast_std_err
            upper_ci = forecast_values + 1.96 * forecast_std_err
        else:
            st.warning("Could not calculate HW CIs.")
        forecast_values = np.clip(np.asarray(forecast_values), 0, None)
        lower_ci = np.clip(np.asarray(lower_ci), 0, None)
        upper_ci = np.clip(np.asarray(upper_ci), 0, None)
        last_date = data["Date"].iloc[-1]
        forecast_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1), periods=forecast_months, freq="M"
        )
        forecast_df = pd.DataFrame(
            {
                "Date": forecast_dates,
                "Forecast": forecast_values,
                "Lower_CI": lower_ci,
                "Upper_CI": upper_ci,
            }
        )
        return forecast_df, True, model_params_str
    except Exception as e:
        st.error(f"HW failed: {e}")
        st.error(traceback.format_exc())
        return None, False, f"Failed: {e}"


@st.cache_data(ttl=3600)
def run_theta_forecaster(
    data: pd.DataFrame, forecast_months: int
) -> Tuple[Optional[pd.DataFrame], bool, Optional[str]]:
    """Runs Theta forecasting using sktime - reliable and robust."""
    if not SKTIME_INSTALLED:
        st.error("`sktime` is required. Please install it (`pip install sktime`).")
        return None, False, "sktime not installed"

    model_params_str = "Theta Forecaster - Statistical with trend decomposition"
    try:
        # Prepare data for sktime - use simple integer index to avoid frequency issues
        ts_data = data["Total"].astype(float).reset_index(drop=True)

        if len(ts_data) < 6:
            st.warning(
                "Theta Forecaster: Less than 6 data points may limit model performance."
            )

        # Create and fit Theta forecaster with minimal parameters
        forecaster = ThetaForecaster(sp=12)  # Only specify seasonal period
        forecaster.fit(ts_data)

        # Generate forecast
        fh = list(range(1, forecast_months + 1))  # Forecast horizon
        forecast_values = forecaster.predict(fh)

        # Generate forecast dates to match other models (use month-end)
        last_date = data["Date"].iloc[-1]
        forecast_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1), periods=forecast_months, freq="M"
        )

        # Calculate prediction intervals
        try:
            pred_ints = forecaster.predict_interval(fh, coverage=0.95)
            lower_ci = pred_ints.iloc[:, 0].values
            upper_ci = pred_ints.iloc[:, 1].values
        except Exception:
            # Fallback: use historical volatility
            historical_std = ts_data.std()
            lower_ci = forecast_values.values - 1.96 * historical_std
            upper_ci = forecast_values.values + 1.96 * historical_std

        # Clip negative values
        forecast_vals_clipped = np.clip(forecast_values.values, 0, None)
        lower_ci_clipped = np.clip(lower_ci, 0, None)
        upper_ci_clipped = np.clip(upper_ci, 0, None)

        # Create forecast DataFrame
        forecast_df = pd.DataFrame(
            {
                "Date": forecast_dates,
                "Forecast": forecast_vals_clipped,
                "Lower_CI": lower_ci_clipped,
                "Upper_CI": upper_ci_clipped,
            }
        )

        return forecast_df, True, model_params_str

    except Exception as e:
        st.error(f"Theta Forecaster failed: {e}")
        st.error(traceback.format_exc())
        return None, False, f"Failed: {e}"


# --- Display Components ---
# (No changes needed in display functions)
def display_forecast_plot(*args, **kwargs):
    # ... (implementation) ...
    st.subheader(f"Forecast Plot ({kwargs.get('method_name', '')})")
    if kwargs.get("model_params"):
        st.caption(f"Model Details: {kwargs['model_params']}")
    if kwargs.get("method_name") == "Holt-Winters":
        st.caption("Note: HW CIs are approximate.")
    historical_data, forecast_data, currency, theme = args[0], args[1], args[2], args[3]
    symbol = {"GBP": "£", "USD": "$", "EUR": "€"}.get(currency, "")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=historical_data["Date"],
            y=historical_data["Total"],
            name="Actual",
            marker_color="rgba(78, 141, 245, 0.8)",
            hovertemplate=f"<b>Date</b>: %{{x|%b %Y}}<br><b>Actual</b>: {symbol}%{{y:,.2f}}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_data["Date"],
            y=forecast_data["Forecast"],
            name="Forecast",
            mode="lines+markers",
            line=dict(color="rgba(255, 165, 0, 1)", width=2),
            marker=dict(size=4),
            hovertemplate=f"<b>Date</b>: %{{x|%b %Y}}<br><b>Forecast</b>: {symbol}%{{y:,.2f}}<extra></extra>",
        )
    )
    if (
        "Lower_CI" in forecast_data.columns
        and "Upper_CI" in forecast_data.columns
        and not forecast_data["Lower_CI"].isnull().all()
        and not forecast_data["Upper_CI"].isnull().all()
    ):
        fig.add_trace(
            go.Scatter(
                x=pd.concat([forecast_data["Date"], forecast_data["Date"].iloc[::-1]]),
                y=pd.concat(
                    [forecast_data["Upper_CI"], forecast_data["Lower_CI"].iloc[::-1]]
                ),
                fill="toself",
                fillcolor="rgba(255, 165, 0, 0.2)",
                line=dict(color="rgba(255, 255, 255, 0)"),
                hoverinfo="skip",
                name="95% CI"
                + (" (Approx.)" if kwargs.get("method_name") == "Holt-Winters" else ""),
            )
        )
    else:
        st.info(f"CIs not available/calculable for {kwargs.get('method_name', '')}.")
    fig.update_layout(
        template="plotly_white" if theme == "Light" else "plotly_dark",
        xaxis=dict(title="Date", tickformat="%b %Y"),
        yaxis=dict(title=f"Dividend Amount ({currency})", rangemode="tozero"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=50, b=40),
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)


def display_summary_stats(*args, **kwargs):
    # ... (implementation) ...
    forecast_data, historical_data, currency = args[0], args[1], args[2]
    st.subheader("Forecast Summary")
    col1, col2, col3 = st.columns(3)
    n_months = len(forecast_data)
    total_fc = forecast_data["Forecast"].sum()
    avg_fc = forecast_data["Forecast"].mean()
    with col1:
        st.metric(
            f"Total Forecasted ({n_months}mo)", format_currency(total_fc, currency)
        )
    with col2:
        st.metric("Avg Monthly Forecast", format_currency(avg_fc, currency))
    with col3:
        growth_str = "N/A"
        if (
            historical_data is not None
            and not historical_data.empty
            and len(historical_data) >= 12
            and n_months >= 12
        ):
            last_12m = historical_data["Total"].tail(12).sum()
            next_12m = forecast_data["Forecast"].head(12).sum()
            growth_str = (
                f"{((next_12m / last_12m) - 1) * 100:.1f}%"
                if abs(last_12m) > 1e-6
                else "Prev yr ~0"
            )
        elif historical_data is None or len(historical_data) < 12:
            growth_str = "<12m history"
        elif n_months < 12:
            growth_str = "<12m forecast"
        st.metric("Proj. 1yr Growth", growth_str, help="...")
    pass


def display_forecast_table(*args, **kwargs):
    # ... (implementation) ...
    forecast_data, currency = args[0], args[1]
    with st.expander("View Forecast Data Table"):
        display_df = forecast_data.copy()
        display_df["Date"] = display_df["Date"].dt.strftime("%b %Y")
        for col in ["Forecast", "Lower_CI", "Upper_CI"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: format_currency(x, currency) if pd.notna(x) else "N/A"
                )
        display_df = display_df.rename(
            columns={"Lower_CI": "Lower 95% CI", "Upper_CI": "Upper 95% CI"}
        )
        cols_to_show = ["Date", "Forecast", "Lower 95% CI", "Upper 95% CI"]
        cols_exist = [col for col in cols_to_show if col in display_df.columns]
        st.dataframe(display_df[cols_exist], hide_index=True, use_container_width=True)
    pass


def display_annual_plot(*args, **kwargs):
    # ... (implementation) ...
    historical_data, forecast_data, currency, theme = args[0], args[1], args[2], args[3]
    st.subheader("Annual Income (Historical & Forecast)")
    try:
        hist_annual = pd.DataFrame()
        fc_annual = pd.DataFrame()
        if historical_data is not None and not historical_data.empty:
            hist_annual = (
                historical_data.groupby(historical_data["Date"].dt.year)["Total"]
                .sum()
                .reset_index()
            )
            hist_annual.columns = ["Year", "Amount"]
            hist_annual["Type"] = "Actual"
        if forecast_data is not None and not forecast_data.empty:
            fc_annual = (
                forecast_data.groupby(forecast_data["Date"].dt.year)["Forecast"]
                .sum()
                .reset_index()
            )
            fc_annual.columns = ["Year", "Amount"]
            fc_annual["Type"] = "Forecast"
        if not hist_annual.empty and not fc_annual.empty:
            combined = pd.concat([hist_annual, fc_annual])
        elif not hist_annual.empty:
            combined = hist_annual
        elif not fc_annual.empty:
            combined = fc_annual
        else:
            st.info("No annual data.")
            return
        combined = combined.drop_duplicates(subset=["Year"], keep="last").sort_values(
            "Year"
        )
        fig = px.bar(
            combined,
            x="Year",
            y="Amount",
            color="Type",
            barmode="group",
            template="plotly_white" if theme == "Light" else "plotly_dark",
            color_discrete_map={
                "Actual": "rgba(78, 141, 245, 0.8)",
                "Forecast": "rgba(255, 165, 0, 0.8)",
            },
            labels={"Amount": f"Annual Income ({currency})", "Year": "Year"},
            text_auto=".2s",
        )
        fig.update_layout(
            xaxis=dict(title="Year", type="category"),
            yaxis=dict(title=f"Annual Income ({currency})", rangemode="tozero"),
            legend_title_text="Type",
            height=400,
            margin=dict(t=30, b=20),
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not generate annual plot: {e}")
        st.error(traceback.format_exc())
    pass


def display_fi_calculator(*args, **kwargs):
    # ... (implementation) ...
    forecast_data, currency, method_key = args[0], args[1], args[2]
    if forecast_data is None or forecast_data.empty:
        st.info("FI calc requires forecast data.")
        return
    st.subheader(f"Financial Independence Projection ({method_key})")
    st.caption("Simplified estimate...")
    col1, col2 = st.columns(2)
    with col1:
        monthly_expenses = st.number_input(
            f"Est. Monthly Expenses ({currency})",
            0.0,
            None,
            2000.0,
            100.0,
            key=f"fi_exp_{method_key}",
            format="%.2f",
        )
        annual_expenses = monthly_expenses * 12
        st.write(
            f"Target Annual Expenses: **{format_currency(annual_expenses, currency)}**"
        )
    with col2:
        swr = st.slider(
            "Target SWR (%)", 1.0, 10.0, 4.0, 0.1, key=f"fi_swr_{method_key}"
        )
        fi_target = (
            (annual_expenses / (swr / 100)) if swr > 0 and annual_expenses > 0 else 0
        )
    if annual_expenses > 0:
        st.write(f"FI Portfolio Target: **{format_currency(fi_target, currency)}**")
    if annual_expenses <= 0:
        st.info("Enter expenses above.")
        return
    proj_annual_div = 0
    basis = "N/A"
    if len(forecast_data) >= 12:
        proj_annual_div = forecast_data["Forecast"].head(12).mean() * 12
        basis = "next 12m avg"
    elif len(forecast_data) > 0:
        proj_annual_div = forecast_data["Forecast"].mean() * 12
        basis = f"annualized {len(forecast_data)}m avg"
    else:
        st.warning("No forecast points for FI calc.")
        return
    st.write(
        f"Projected Annual Dividend ({basis}): **{format_currency(proj_annual_div, currency)}**"
    )
    coverage = (
        (proj_annual_div / annual_expenses) * 100
        if annual_expenses > 0
        else (100 if proj_annual_div > 0 else 0)
    )
    gap = max(0, annual_expenses - proj_annual_div)
    st.markdown("#### Coverage & Gap")
    st.progress(min(coverage / 100, 1.0))
    m1, m2 = st.columns(2)
    m1.metric("Dividend Coverage", f"{coverage:.1f}%")
    m2.metric("Annual Income Gap", format_currency(gap, currency))
    pass


# --- Main Tab Function ---
# (No changes needed in show_forecast_tab's structure)
def show_forecast_tab(
    monthly_data: pd.DataFrame,  # Expects monthly aggregated data
    currency: str,
    theme: str,
    **kwargs: Dict[str, Any],  # Allow other args passed from main app
):
    """Main function to display the forecast tab."""
    st.title("Dividend Income Forecast")
    st.caption(
        f"Current date: {datetime.now().strftime('%Y-%m-%d')}. Currency: {currency}. Theme: {theme}."
    )
    st.caption(
        "Forecasts use fixed parameters (SARIMAX) or defaults (Prophet/HW). Enforcing stability constraints on SARIMAX."
    )

    cleaned_data = prepare_data(monthly_data)
    if cleaned_data is None or cleaned_data.empty:
        st.error("Failed to prepare data for forecasting.")
        return
    if len(cleaned_data) < 12:
        st.warning(
            f"Warning: Only {len(cleaned_data)} months of data. Forecasting accuracy limited."
        )

    st.sidebar.subheader("Forecast Settings")
    forecast_months = st.sidebar.slider(
        "Forecast Horizon (Months)", 3, 36, 12, 3, key="fc_horizon_v3"
    )

    # Add lookback period control
    max_lookback = len(cleaned_data)
    lookback_months = st.sidebar.slider(
        "Lookback Period (Months)",
        min_value=6,
        max_value=max_lookback,
        value=min(24, max_lookback),
        step=1,
        key="lookback_period",
        help="Number of historical months to use for training the forecast models",
    )

    # Apply lookback period to the data
    training_data = cleaned_data.tail(lookback_months).copy()
    st.info(
        f"Using {len(training_data)} months of data for training (from {training_data['Date'].min().strftime('%Y-%m')} to {training_data['Date'].max().strftime('%Y-%m')})"
    )

    available_tabs = []
    if STATSMODELS_INSTALLED:
        available_tabs.extend(["SARIMAX", "Holt-Winters"])
    if PROPHET_INSTALLED:
        available_tabs.append("Prophet")
    if SKTIME_INSTALLED:
        available_tabs.append("Theta Forecaster")

    # Add ensemble tab if we have multiple models
    if len(available_tabs) > 1:
        available_tabs.append("Ensemble")

    if not available_tabs:
        st.error("No forecasting models available.")
        return
    tabs = st.tabs(available_tabs)
    tab_map = dict(zip(available_tabs, tabs))

    def run_and_display(model_func: Callable, model_name: str, **model_args):
        with st.spinner(f"Generating {model_name} forecast..."):
            forecast_df, success, params_str = model_func(
                training_data.copy(), forecast_months, **model_args
            )
        if success and forecast_df is not None:
            display_forecast_plot(
                cleaned_data, forecast_df, currency, theme, model_name, params_str
            )
            st.markdown("---")
            display_summary_stats(forecast_df, cleaned_data, currency)
            st.markdown("---")
            display_annual_plot(cleaned_data, forecast_df, currency, theme)
            st.markdown("---")
            display_forecast_table(forecast_df, currency)
            st.markdown("---")
            display_fi_calculator(forecast_df, currency, model_name)
        else:
            st.warning(f"{model_name} forecast could not be generated.")

    if "SARIMAX" in tab_map:
        with tab_map["SARIMAX"]:
            st.markdown(
                "Uses SARIMAX with **fixed orders** and enforced stability constraints. May fail if orders are incompatible with data."
            )
            run_and_display(
                run_sarimax_fixed, "SARIMAX"
            )  # Calls the stability-focused fixed version

    if "Prophet" in tab_map:
        with tab_map["Prophet"]:
            st.markdown("Uses Facebook's `Prophet` model.")
            run_and_display(run_prophet, "Prophet")

    if "Holt-Winters" in tab_map:
        with tab_map["Holt-Winters"]:
            st.markdown("Uses Holt-Winters exponential smoothing.")
            st.info("Configure Holt-Winters Parameters:")
            hw_cols = st.columns(3)
            trend_opts = [None, "add", "mul"]
            seasonal_opts = [None, "add", "mul"]
            # Fixed Holt-Winters parameters as requested
            trend = "add"
            seasonal = "mul" 
            damped = False
            
            # Display the fixed settings
            hw_cols[0].info(f"Trend: **{trend}** (fixed)")
            hw_cols[1].info(f"Seasonality: **{seasonal}** (fixed)")
            hw_cols[2].info(f"Damp Trend: **{damped}** (fixed)")
            run_and_display(
                run_holtwinters,
                "Holt-Winters",
                trend=trend,
                seasonal=seasonal,
                damped=damped,
            )

    if "Theta Forecaster" in tab_map:
        with tab_map["Theta Forecaster"]:
            st.markdown(
                "**Theta Forecaster** - Advanced statistical forecasting with trend decomposition."
            )
            st.info(
                "Uses the Theta method - excellent for data with trends and proven performance in forecasting competitions."
            )
            st.caption(
                "Fast, reliable, and particularly good for financial time series like dividends."
            )
            run_and_display(run_theta_forecaster, "Theta Forecaster")

    if "Ensemble" in tab_map:
        with tab_map["Ensemble"]:
            st.markdown(
                "**Ensemble Forecast** - Averages predictions from all available models for improved accuracy."
            )

            # Run all available models and collect results
            ensemble_forecasts = []
            model_names = []

            with st.spinner("Generating ensemble forecast..."):
                if STATSMODELS_INSTALLED:
                    # SARIMAX
                    sarimax_df, sarimax_success, _ = run_sarimax_fixed(
                        training_data.copy(), forecast_months
                    )
                    if sarimax_success and sarimax_df is not None:
                        ensemble_forecasts.append(
                            sarimax_df[["Date", "Forecast"]].copy()
                        )
                        model_names.append("SARIMAX")

                    # Holt-Winters with fixed parameters
                    hw_df, hw_success, _ = run_holtwinters(
                        training_data.copy(),
                        forecast_months,
                        trend="add",
                        seasonal="mul",
                        damped=False,
                    )
                    if hw_success and hw_df is not None:
                        ensemble_forecasts.append(hw_df[["Date", "Forecast"]].copy())
                        model_names.append("Holt-Winters")

                if PROPHET_INSTALLED:
                    prophet_df, prophet_success, _ = run_prophet(
                        training_data.copy(), forecast_months
                    )
                    if prophet_success and prophet_df is not None:
                        ensemble_forecasts.append(
                            prophet_df[["Date", "Forecast"]].copy()
                        )
                        model_names.append("Prophet")

                if SKTIME_INSTALLED:
                    theta_df, theta_success, _ = run_theta_forecaster(
                        training_data.copy(), forecast_months
                    )
                    if theta_success and theta_df is not None:
                        ensemble_forecasts.append(theta_df[["Date", "Forecast"]].copy())
                        model_names.append("Theta Forecaster")

            if len(ensemble_forecasts) < 2:
                st.warning(
                    "Ensemble requires at least 2 successful models. Not enough models available."
                )
            else:
                st.success(
                    f"Successfully combined {len(ensemble_forecasts)} models: {', '.join(model_names)}"
                )

                # Create ensemble by averaging forecasts
                # Normalize dates by aligning to month/year (more robust than exact date matching)
                normalized_forecasts = []
                for i, df in enumerate(ensemble_forecasts):
                    df_clean = df[["Date", "Forecast"]].copy()
                    # Create a month-year key for alignment
                    df_clean["Date"] = pd.to_datetime(df_clean["Date"])
                    df_clean["MonthYear"] = df_clean["Date"].dt.to_period("M")
                    df_clean = df_clean.rename(columns={"Forecast": f"Forecast_{i}"})
                    df_clean = df_clean[["MonthYear", f"Forecast_{i}"]].copy()
                    normalized_forecasts.append(df_clean)

                # Start with the first forecast
                ensemble_df = normalized_forecasts[0].copy()

                # Merge all other forecasts using MonthYear periods
                for i, other_df in enumerate(normalized_forecasts[1:], 1):
                    ensemble_df = ensemble_df.merge(
                        other_df, on="MonthYear", how="inner"
                    )

                # Convert MonthYear back to proper dates (use month-end)
                ensemble_df["Date"] = ensemble_df["MonthYear"].dt.to_timestamp("M")

                # Calculate average forecast
                forecast_cols = [
                    col for col in ensemble_df.columns if col.startswith("Forecast_")
                ]

                if len(ensemble_df) > 0 and len(forecast_cols) > 0:
                    ensemble_df["Forecast"] = ensemble_df[forecast_cols].mean(axis=1)

                    # Final ensemble dataframe - no confidence intervals
                    ensemble_df = ensemble_df[["Date", "Forecast"]].copy()
                else:
                    st.error(
                        "Ensemble creation failed - unable to align model forecasts."
                    )
                    return

                # Display ensemble forecast
                display_forecast_plot(
                    cleaned_data,
                    ensemble_df,
                    currency,
                    theme,
                    "Ensemble",
                    f"Average of {len(model_names)} models",
                )
                st.markdown("---")
                display_summary_stats(ensemble_df, cleaned_data, currency)
                st.markdown("---")
                display_annual_plot(cleaned_data, ensemble_df, currency, theme)
                st.markdown("---")
                display_forecast_table(ensemble_df, currency)
                st.markdown("---")
                display_fi_calculator(ensemble_df, currency, "Ensemble")
