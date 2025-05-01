import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import io
from datetime import datetime, timedelta
import calendar
import warnings

# Import tab modules
from tabs.overview import show_overview_tab
from tabs.monthly_analysis import show_monthly_analysis_tab
from tabs.stock_analysis import show_stock_analysis_tab
from tabs.dividend_calendar import show_dividend_calendar_tab
from tabs.forecast import show_forecast_tab

# Import functions from tab modules to make them available
from tabs.dividend_calendar import create_dividend_calendar, analyze_dividend_cadence

# Filter unnecessary warnings
class WarningFilter(io.StringIO):
    def write(self, s):
        if "missing ScriptRunContext" not in s and "No runtime found" not in s:
            sys.__stderr__.write(s)
            
sys.stderr = WarningFilter()
warnings.filterwarnings("ignore")

# Utility functions for data processing
@st.cache_data(ttl=3600)
def parse_datetime(column):
    """Parse date columns with multiple potential formats"""
    try:
        return pd.to_datetime(column, format='%Y-%m-%d %H:%M:%S', dayfirst=True)
    except ValueError:
        pass
    try:
        return pd.to_datetime(column, format='%d/%m/%Y %H:%M', dayfirst=True)
    except ValueError:
        pass
    return pd.to_datetime(column, dayfirst=True, errors='coerce')

@st.cache_data(ttl=3600)
def load_data():
    """Load data using the imsciences module or fallback to demo data"""
    try:
        from imsciences import dataprocessing
        import os
        dp = dataprocessing()
        fp = dp.get_wd_levels(0)
        fp = os.path.join(fp, "dividends")
        df = dp.read_and_concatenate_files(fp, "csv")
        df['Time'] = df['Time'].apply(parse_datetime)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Return empty DataFrame with expected columns to prevent crashes
        return pd.DataFrame(columns=['Time', 'Name', 'Total'])

@st.cache_data
def preprocess_data(df):
    """Preprocess the data for analysis"""
    # Ensure Time is datetime
    if 'Time' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['Time']):
        df['Time'] = pd.to_datetime(df['Time'])
    
    # Extract Year and Month
    df['Year'] = df['Time'].dt.year
    df['Month'] = df['Time'].dt.month
    df['MonthName'] = df['Time'].dt.month_name()
    
    # Add quarter for quarterly analysis
    df['Quarter'] = 'Q' + df['Time'].dt.quarter.astype(str) + ' ' + df['Year'].astype(str)
    
    # Add day of month for calendar view
    df['Day'] = df['Time'].dt.day
    
    return df

def format_currency(value, currency='GBP'):
    """Format values as currency with appropriate symbol"""
    symbols = {'GBP': '£', 'USD': '$', 'EUR': '€'}
    symbol = symbols.get(currency, '£')
    return f"{symbol}{value:,.2f}"

# Get monthly data for reuse across tabs
@st.cache_data
def get_monthly_data(df):
    """Aggregate data to monthly level for reuse across tabs"""
    monthly_data = df.groupby(df['Time'].dt.to_period('M')).agg({
        'Total': 'sum',
        'Time': lambda x: x.iloc[0]
    }).reset_index(drop=True)
    
    monthly_data = monthly_data.sort_values('Time')
    monthly_data['Date'] = monthly_data['Time']
    return monthly_data

# Get proper month ordering for consistent display
def get_month_order():
    return ['January', 'February', 'March', 'April', 'May', 'June', 
            'July', 'August', 'September', 'October', 'November', 'December']

# Month names for calendar
month_names = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}

def main():
    # Set page configuration
    st.set_page_config(
        page_title="Dividend Portfolio Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load CSS
    try:
        with open(os.path.join("static", "styles.css")) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        st.warning("Could not load CSS file. Using default styling.")
    
    # App title
    st.title("📊 Dividend Portfolio Dashboard")
    st.markdown("Track, analyze, forecast and optimize your dividend income over time")
    
    # Default values for settings
    currency = "GBP"
    theme = "Light"
    forecast_months = 12
    
    # Navigation in sidebar
    st.sidebar.title("Navigation")
    
    # Use radio buttons for navigation instead of tabs
    page = st.sidebar.radio(
        "Select Page",
        ["📈 Overview", "📅 Monthly Analysis", "🏢 Stock Analysis", 
         "📆 Dividend Calendar", "🔮 Forecast"]
    )
    
    # Load and preprocess data with error handling
    with st.spinner("Loading data..."):
        try:
            df = load_data()
            df = preprocess_data(df)
            
            if df.empty:
                st.error("No data available. Please check your data source.")
                return
                
            # Prepare monthly data (used across multiple tabs)
            monthly_data = get_monthly_data(df)
            
        except Exception as e:
            st.error(f"Error loading or processing data: {e}")
            return
    
    # Get current date for filtering
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    # Create a dict with common parameters to pass to each tab
    common_params = {
        'df': df,
        'monthly_data': monthly_data,
        'currency': currency,
        'theme': theme,
        'current_date': current_date,
        'current_year': current_year,
        'current_month': current_month,
        'format_currency': format_currency,
        'get_month_order': get_month_order
    }
    
    # Main content based on selection
    if page == "📈 Overview":
        show_overview_tab(**common_params)
    elif page == "📅 Monthly Analysis":
        show_monthly_analysis_tab(**common_params)
    elif page == "🏢 Stock Analysis":
        show_stock_analysis_tab(**common_params)
    elif page == "📆 Dividend Calendar":
        show_dividend_calendar_tab(**common_params)
    elif page == "🔮 Forecast":
        show_forecast_tab(**common_params)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        import traceback
        st.error(traceback.format_exc())