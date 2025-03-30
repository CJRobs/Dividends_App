import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

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

@st.cache_data
def create_dividend_calendar(df, future_months=12, lookback_months=24):
    """Create a simplified monthly dividend payment calendar based on recent payment patterns"""
    # Get current date
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Get next month as starting point
    if current_month == 12:
        next_month = 1
        next_month_year = current_year + 1
    else:
        next_month = current_month + 1
        next_month_year = current_year
        
    # Filter to include the past X months of data for pattern detection
    lookback_date = current_date - timedelta(days=lookback_months*30)
    recent_df = df[df['Time'] >= lookback_date]
    
    # Get list of stocks that have paid in the lookback period
    recent_stocks = recent_df['Name'].unique()
    
    # Create a calendar for the next X months starting from next month
    calendar_months = []
    for i in range(future_months):
        month_to_add = (next_month + i - 1) % 12 + 1  # Ensure month is 1-12
        year_to_add = next_month_year + ((next_month + i - 1) // 12)  # Increment year when needed
        calendar_months.append((year_to_add, month_to_add))
    
    # Get the historical payment pattern by stock and month
    payment_pattern = recent_df.groupby(['Name', 'Month']).agg({
        'Total': ['mean', 'count', 'last'],
        'Time': ['max']
    }).reset_index()
    
    payment_pattern.columns = ['Name', 'Month', 'Average Amount', 'Frequency', 'Last Amount', 'Last Payment']
    
    # Find monthly payers (stocks that have paid in at least 6 different months)
    monthly_payers = recent_df.groupby('Name')['Month'].nunique()
    monthly_payers = monthly_payers[monthly_payers >= 6].index.tolist()
    
    # Special handling for monthly payers
    monthly_pattern = pd.DataFrame()
    for payer in monthly_payers:
        payer_data = recent_df[recent_df['Name'] == payer]
        latest_amount = payer_data.sort_values('Time', ascending=False).iloc[0]['Total']
        
        # For monthly payers, add entries for all 12 months
        for month in range(1, 13):
            monthly_pattern = pd.concat([monthly_pattern, pd.DataFrame({
                'Name': [payer],
                'Month': [month],
                'Average Amount': [latest_amount],
                'Frequency': [payer_data.shape[0]],
                'Last Amount': [latest_amount],
                'Last Payment': [payer_data['Time'].max()]
            })])
    
    # Combine regular patterns with monthly payer patterns
    # For monthly payers, the monthly_pattern will override the regular pattern
    payment_pattern = pd.concat([
        payment_pattern[~payment_pattern['Name'].isin(monthly_payers)],
        monthly_pattern
    ]).reset_index(drop=True)
    
    # Keep only stocks that pay regularly (at least twice) or are monthly payers
    payment_pattern = payment_pattern[
        (payment_pattern['Frequency'] >= 2) | 
        (payment_pattern['Name'].isin(monthly_payers))
    ]
    
    # Create calendar events for the upcoming months
    calendar_events = []
    
    for year, month in calendar_months:
        month_name = month_names[month]
        
        # Get payments typically occurring in this month
        month_payments = payment_pattern[payment_pattern['Month'] == month].copy()
        
        for _, payment in month_payments.iterrows():
            # Calculate confidence level
            if payment['Name'] in monthly_payers:
                confidence = "High"  # Monthly payers get high confidence
            else:
                confidence = "High" if payment['Frequency'] >= 4 else "Medium" if payment['Frequency'] >= 3 else "Low"
            
            calendar_events.append({
                'Year': year,
                'Month': month,
                'Month Name': month_name,
                'Period': f"{month_name} {year}",
                'Name': payment['Name'],
                'Estimated Amount': payment['Last Amount'],
                'Frequency': payment['Frequency'],
                'Last Payment': payment['Last Payment'],
                'Days Since Last': (current_date - payment['Last Payment']).days,
                'Confidence': confidence,
                'Is Monthly': payment['Name'] in monthly_payers
            })
    
    calendar_df = pd.DataFrame(calendar_events)
    if not calendar_df.empty:
        calendar_df = calendar_df.sort_values(['Year', 'Month', 'Name'])
    
    return calendar_df, recent_stocks

@st.cache_data
def analyze_dividend_cadence(df):
    """
    Analyze the dividend payment cadence for each stock and predict next payment dates
    """
    # Get unique stocks in portfolio
    stocks = df['Name'].unique()
    
    # Results container
    results = []
    
    for stock in stocks:
        # Get payments for this stock
        stock_payments = df[df['Name'] == stock].copy()
        stock_payments = stock_payments.sort_values('Time')
        
        # Skip if less than 2 payments
        if len(stock_payments) < 2:
            results.append({
                'Name': stock,
                'Total Payments': len(stock_payments),
                'Last Payment Date': stock_payments['Time'].max() if len(stock_payments) > 0 else None,
                'Last Amount': stock_payments['Total'].iloc[-1] if len(stock_payments) > 0 else None,
                'Payment Cadence': 'Unknown',
                'Expected Next Payment': None,
                'Confidence': 'Low'
            })
            continue
            
        # Get payment dates and intervals
        payment_dates = stock_payments['Time'].sort_values().reset_index(drop=True)
        intervals = []
        for i in range(1, len(payment_dates)):
            interval_days = (payment_dates[i] - payment_dates[i-1]).days
            intervals.append(interval_days)
        
        # Analyze payment pattern
        if len(intervals) == 0:
            cadence = "Unknown"
            confidence = "Low"
            next_payment = None
        else:
            avg_interval = sum(intervals) / len(intervals)
            std_interval = pd.Series(intervals).std() if len(intervals) > 1 else 0
            
            # Determine cadence
            if avg_interval >= 85 and avg_interval <= 95:
                cadence = "Quarterly"
            elif avg_interval >= 28 and avg_interval <= 32:
                cadence = "Monthly"
            elif avg_interval >= 175 and avg_interval <= 185:
                cadence = "Semi-annual"
            elif avg_interval >= 355 and avg_interval <= 375:
                cadence = "Annual"
            else:
                # Check if it's quarterly but with irregular months
                months = stock_payments['Time'].dt.month
                unique_months = sorted(months.unique())
                
                if len(unique_months) <= 4 and len(stock_payments) >= 4:
                    months_str = ", ".join([month_names[m] for m in unique_months])
                    cadence = f"Quarterly ({months_str})"
                else:
                    cadence = f"Irregular (avg {avg_interval:.1f} days)"
            
            # Determine confidence based on consistency
            if std_interval < 5:
                confidence = "High"
            elif std_interval < 15:
                confidence = "Medium"
            else:
                confidence = "Low"
                
            # Predict next payment date
            last_payment = stock_payments['Time'].max()
            
            # Use pattern to predict next payment
            if cadence == "Monthly":
                next_payment = last_payment + pd.DateOffset(months=1)
            elif cadence == "Quarterly":
                next_payment = last_payment + pd.DateOffset(months=3)
            elif cadence == "Semi-annual":
                next_payment = last_payment + pd.DateOffset(months=6)
            elif cadence == "Annual":
                next_payment = last_payment + pd.DateOffset(months=12)
            elif "Quarterly" in cadence:
                # For quarterly with specific months
                next_payment = last_payment + pd.DateOffset(months=3)
                
                # Check if we need to adjust based on known payment months
                try:
                    known_months = [m for m in unique_months]
                    target_month = next_payment.month
                    while target_month not in known_months:
                        next_payment += pd.DateOffset(months=1)
                        target_month = next_payment.month
                except:
                    pass
            else:
                # Use average interval for irregular payments
                next_payment = last_payment + pd.DateOffset(days=int(avg_interval))
                
        # Get last payment amount
        last_payment = stock_payments['Time'].max()
        last_amount = stock_payments.loc[stock_payments['Time'] == last_payment, 'Total'].iloc[0]
                
        # Store results
        results.append({
            'Name': stock,
            'Total Payments': len(stock_payments),
            'Last Payment Date': last_payment,
            'Last Amount': last_amount,
            'Payment Cadence': cadence,
            'Average Interval': f"{avg_interval:.1f} days" if 'avg_interval' in locals() else "Unknown",
            'Expected Next Payment': next_payment,
            'Confidence': confidence
        })
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Sort by next expected payment date
    if not results_df.empty:
        # Convert None to NaT for sorting
        results_df['Next Payment Sort'] = pd.to_datetime(
            results_df['Expected Next Payment'], errors='coerce'
        )
        results_df = results_df.sort_values('Next Payment Sort')
        results_df = results_df.drop('Next Payment Sort', axis=1)
    
    return results_df

def show_dividend_calendar_tab(df, monthly_data, currency, theme, current_date, current_year, current_month, format_currency, **kwargs):
    """
    Display the Dividend Calendar tab content
    
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
    st.subheader("Dividend Calendar & Cadence Analysis")
    
    # Use the local functions instead of ones passed from main app
    
    # Create tabs for different views
    calendar_views = st.tabs(["Stock Cadence & Next Payment", "Monthly Payment Calendar"])
    
    # Tab 1: Stock Cadence Analysis
    with calendar_views[0]:
        st.subheader("Payment Cadence & Next Expected Dividend")
        
        # Get dividend cadence analysis using the local function
        cadence_results = analyze_dividend_cadence(df)
        
        if cadence_results.empty:
            st.warning("No dividend payment data available for analysis.")
        else:
            # Format data for display
            display_df = cadence_results.copy()
            
            # Format dates
            if 'Last Payment Date' in display_df.columns:
                display_df['Last Payment Date'] = display_df['Last Payment Date'].apply(
                    lambda x: x.strftime('%d %b %Y') if isinstance(x, pd.Timestamp) else x
                )
            
            if 'Expected Next Payment' in display_df.columns:
                display_df['Expected Next Payment'] = display_df['Expected Next Payment'].apply(
                    lambda x: x.strftime('%d %b %Y') if isinstance(x, pd.Timestamp) else x
                )
            
            # Format amounts
            if 'Last Amount' in display_df.columns:
                display_df['Last Amount'] = display_df['Last Amount'].apply(
                    lambda x: format_currency(x, currency) if pd.notnull(x) else "Unknown"
                )
            
            # Highlight upcoming payments (within next 30 days)
            current_date = datetime.now()
            upcoming_stocks = []
            
            for _, row in cadence_results.iterrows():
                if isinstance(row['Expected Next Payment'], pd.Timestamp):
                    days_until = (row['Expected Next Payment'] - current_date).days
                    if days_until <= 30 and days_until >= 0:
                        upcoming_stocks.append(row['Name'])
            
            # Display upcoming payments
            if upcoming_stocks:
                st.info(f"**Upcoming payments expected within 30 days**: {', '.join(upcoming_stocks)}")
            
            # Display table
            # Select columns to display
            display_columns = ['Name', 'Payment Cadence', 'Last Payment Date', 'Last Amount', 
                              'Expected Next Payment', 'Confidence', 'Total Payments']
            
            st.dataframe(
                display_df[display_columns], 
                use_container_width=True,
                height=600
            )
            
            # Timeline visualization of upcoming payments
            st.subheader("Upcoming Payment Timeline")
            
            # Filter to only include known dates for next 90 days
            timeline_data = cadence_results.copy()
            # Ensure we only look at datetime values for Expected Next Payment
            timeline_data = timeline_data[timeline_data['Expected Next Payment'].apply(
                lambda x: isinstance(x, pd.Timestamp)
            )]
            
            # Filter to next 90 days
            timeline_data = timeline_data[
                (timeline_data['Expected Next Payment'] >= current_date) & 
                (timeline_data['Expected Next Payment'] <= current_date + pd.DateOffset(days=90))
            ]
            
            if not timeline_data.empty:
                # Create timeline chart
                fig = go.Figure()
                
                for _, row in timeline_data.iterrows():
                    # Set color based on confidence
                    confidence_color = "#3CB371" if row['Confidence'] == "High" else \
                                       "#FFA500" if row['Confidence'] == "Medium" else "#FF6347"
                    
                    payment_date = row['Expected Next Payment']
                    stock_name = row['Name']
                    
                    fig.add_trace(go.Scatter(
                        x=[payment_date],
                        y=[stock_name],
                        mode='markers',
                        marker=dict(
                            symbol='diamond',
                            size=12,
                            color=confidence_color
                        ),
                        name=stock_name,
                        text=f"{stock_name}: {payment_date.strftime('%d %b %Y')}",
                        hoverinfo='text'
                    ))
                
                # Add vertical line for today using a scatter trace
                y_values = list(timeline_data['Name'].unique())
                fig.add_trace(go.Scatter(
                    x=[current_date, current_date],
                    y=[y_values[0], y_values[-1]],
                    mode='lines',
                    line=dict(color='gray', width=2, dash='dash'),
                    name='Today',
                    showlegend=True
                ))
                
                # Add "Today" annotation
                fig.add_annotation(
                    x=current_date,
                    y=y_values[-1],
                    text="Today",
                    showarrow=False,
                    yshift=10
                )
                
                # Layout
                fig.update_layout(
                    title="Expected Payments (Next 90 Days)",
                    xaxis_title="Date",
                    yaxis_title="Stock",
                    height=max(300, len(timeline_data) * 30 + 100),
                    margin=dict(l=20, r=20, t=40, b=20),
                    showlegend=False,
                    template="plotly_white" if theme == "Light" else "plotly_dark",
                    font=dict(color='black')
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expected payments in the next 90 days based on the analysis.")
    
    # Tab 2: Monthly Calendar
    with calendar_views[1]:
        st.subheader("Monthly Dividend Payment Calendar")
        
        # Settings
        col1, col2 = st.columns(2)
        with col1:
            future_months = st.slider("Number of Months to Forecast", 1, 24, 12)
        with col2:
            lookback_months = st.slider("Historical Data to Consider (Months)", 6, 36, 24)
        
        # Create calendar using the local function
        calendar_df, recent_stocks = create_dividend_calendar(df, future_months, lookback_months)
        
        if calendar_df.empty:
            st.warning("Not enough historical data to create reliable payment predictions.")
        else:
            # Summary of stocks with predicted payments
            st.subheader(f"Stocks with Predicted Payments ({len(recent_stocks)})")
            
            # Find monthly payers
            monthly_payers = []
            if 'Is Monthly' in calendar_df.columns:
                monthly_payers = calendar_df[calendar_df['Is Monthly']]['Name'].unique().tolist()
            
            if monthly_payers:
                st.write("**Monthly Dividend Payers:** " + ", ".join(sorted(monthly_payers)))
            
            # Month by month view
            st.subheader("Monthly Dividend Forecast")
            
            # Group by month
            months_to_display = calendar_df[['Year', 'Month', 'Month Name', 'Period']].drop_duplicates().sort_values(['Year', 'Month'])
            
            for _, month_row in months_to_display.iterrows():
                period = month_row['Period']
                
                # Get payments for this month
                month_payments = calendar_df[calendar_df['Period'] == period].copy()
                
                # Calculate total for the month
                month_total = month_payments['Estimated Amount'].sum()
                
                # Display month header with total
                st.write(f"### {period} — Total: {format_currency(month_total, currency)}")
                
                # Create columns for better layout
                cols = st.columns(3)
                
                # Prepare payment data
                display_df = month_payments[['Name', 'Estimated Amount', 'Confidence', 'Frequency']].copy()
                display_df['Estimated Amount'] = display_df['Estimated Amount'].apply(lambda x: format_currency(x, currency))
                
                # Sort by stock name
                display_df = display_df.sort_values('Name')
                
                # Split stocks into columns for better layout
                stocks_per_col = len(display_df) // 3 + (1 if len(display_df) % 3 > 0 else 0)
                
                for i, col in enumerate(cols):
                    start_idx = i * stocks_per_col
                    end_idx = min((i + 1) * stocks_per_col, len(display_df))
                    
                    if start_idx < len(display_df):
                        col_stocks = display_df.iloc[start_idx:end_idx]
                        
                        # Create a color-coded list for each column
                        for _, row in col_stocks.iterrows():
                            confidence_color = "green" if row['Confidence'] == "High" else "orange" if row['Confidence'] == "Medium" else "red"
                            col.markdown(
                                f"<div style='padding: 4px 0;'>"
                                f"<span style='font-weight: bold;'>{row['Name']}</span>: "
                                f"{row['Estimated Amount']} "
                                f"<span style='color: {confidence_color};'>({row['Confidence']})</span>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                
                st.markdown("---")
            
            # Table view of all upcoming payments
            st.subheader("All Upcoming Predicted Payments")
            
            # Prepare data for table display
            table_df = calendar_df.copy()
            table_df['Estimated Amount'] = table_df['Estimated Amount'].apply(lambda x: format_currency(x, currency))
            if 'Last Payment' in table_df.columns:
                table_df['Last Payment'] = table_df['Last Payment'].dt.strftime('%b %Y')
            
            # Select columns to display
            display_cols = ['Period', 'Name', 'Estimated Amount', 'Confidence', 'Frequency']
            if 'Last Payment' in table_df.columns:
                display_cols.append('Last Payment')
            if 'Is Monthly' in table_df.columns:
                display_cols.append('Is Monthly')
                
            display_table = table_df[display_cols]
            
            # Allow filtering
            col1, col2 = st.columns(2)
            with col1:
                confidence_filter = st.multiselect(
                    "Filter by Confidence Level",
                    options=["High", "Medium", "Low"],
                    default=["High", "Medium", "Low"]
                )
            
            with col2:
                stock_filter = st.multiselect(
                    "Filter by Stock",
                    options=sorted(calendar_df['Name'].unique()),
                    default=[]
                )
            
            filtered_table = display_table.copy()
            if confidence_filter:
                filtered_table = filtered_table[filtered_table['Confidence'].isin(confidence_filter)]
                
            if stock_filter:
                filtered_table = filtered_table[filtered_table['Name'].isin(stock_filter)]
                
            st.dataframe(filtered_table, use_container_width=True)
            
            # Monthly summary chart
            monthly_payments = calendar_df.groupby('Period').agg({
                'Estimated Amount': 'sum'
            }).reset_index()
            
            # Sort by year and month
            monthly_payments['Year'] = calendar_df.groupby('Period')['Year'].first().values
            monthly_payments['Month'] = calendar_df.groupby('Period')['Month'].first().values
            monthly_payments = monthly_payments.sort_values(['Year', 'Month'])
            
            fig_monthly_payments = px.bar(
                monthly_payments,
                x='Period',
                y='Estimated Amount',
                title="Estimated Monthly Dividend Income",
                template="plotly_white" if theme == "Light" else "plotly_dark",
                text_auto=True
            )
            
            fig_monthly_payments.update_traces(
                marker_color='#4e8df5',
                textfont=dict(color='black')
            )
            
            fig_monthly_payments.update_layout(
                height=400,
                xaxis=dict(title="Month"),
                yaxis=dict(title=f"Expected Dividend Income ({currency})"),
                font=dict(color='black')
            )
            
            st.plotly_chart(fig_monthly_payments, use_container_width=True)