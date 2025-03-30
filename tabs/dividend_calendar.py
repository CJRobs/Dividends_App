import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

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
    """
    Create a monthly dividend payment calendar based on payment patterns
    Only includes stocks with more than 1 payment
    """
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
    
    # Count payments per stock to filter out those with only 1 payment
    payment_counts = recent_df.groupby('Name').size()
    stocks_with_multiple_payments = payment_counts[payment_counts > 1].index.tolist()
    
    # Filter to only include stocks with multiple payments
    recent_df = recent_df[recent_df['Name'].isin(stocks_with_multiple_payments)]
    
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
        'Total': ['last'],
        'Time': ['max']
    }).reset_index()
    
    payment_pattern.columns = ['Name', 'Month', 'Last Amount', 'Last Payment']
    
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
                'Last Amount': [latest_amount],
                'Last Payment': [payer_data['Time'].max()]
            })])
    
    # Combine regular patterns with monthly payer patterns
    # For monthly payers, the monthly_pattern will override the regular pattern
    payment_pattern = pd.concat([
        payment_pattern[~payment_pattern['Name'].isin(monthly_payers)],
        monthly_pattern
    ]).reset_index(drop=True)
    
    # Create calendar events for the upcoming months
    calendar_events = []
    
    for year, month in calendar_months:
        month_name = month_names[month]
        
        # Get payments typically occurring in this month
        month_payments = payment_pattern[payment_pattern['Month'] == month].copy()
        
        for _, payment in month_payments.iterrows():
            calendar_events.append({
                'Year': year,
                'Month': month,
                'Month Name': month_name,
                'Period': f"{month_name} {year}",
                'Name': payment['Name'],
                'Estimated Amount': payment['Last Amount'],
                'Last Payment': payment['Last Payment'],
                'Days Since Last': (current_date - payment['Last Payment']).days,
                'Is Monthly': payment['Name'] in monthly_payers
            })
    
    calendar_df = pd.DataFrame(calendar_events)
    if not calendar_df.empty:
        calendar_df = calendar_df.sort_values(['Year', 'Month', 'Name'])
    
    return calendar_df, recent_stocks

@st.cache_data
def analyze_dividend_cadence(df):
    """
    Analyze the dividend payment cadence for each stock with simplified detection
    Only includes stocks with more than 1 payment
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
            continue
            
        # Get payment dates, months, and intervals
        payment_dates = stock_payments['Time'].sort_values().reset_index(drop=True)
        payment_months = stock_payments['Month'].sort_values().unique()
        
        intervals = []
        for i in range(1, len(payment_dates)):
            interval_days = (payment_dates[i] - payment_dates[i-1]).days
            intervals.append(interval_days)
        
        # Analyze payment pattern
        avg_interval = sum(intervals) / len(intervals)
            
        # Determine cadence
        if 25 <= avg_interval <= 35:
            cadence = "Monthly"
        elif 85 <= avg_interval <= 95:
            cadence = "Quarterly"
        elif 175 <= avg_interval <= 190:
            cadence = "Semi-annual"
        elif 355 <= avg_interval <= 375:
            cadence = "Annual"
        else:
            # Check if it's quarterly but with specific months
            if len(payment_months) <= 4 and len(stock_payments) >= 4:
                months_str = ", ".join([month_names[m] for m in sorted(payment_months)])
                cadence = f"Quarterly ({months_str})"
            elif len(payment_months) == 2 and len(stock_payments) >= 3:
                months_str = ", ".join([month_names[m] for m in sorted(payment_months)])
                cadence = f"Semi-annual ({months_str})"
            else:
                cadence = f"Irregular (avg {avg_interval:.1f} days)"
                
        # Predict next payment date using the pattern
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
        elif "Quarterly" in cadence or "Semi-annual" in cadence:
            # For quarterly/semi-annual with specific months
            if "Quarterly" in cadence:
                base_interval = 3
            else:  # Semi-annual
                base_interval = 6
            
            next_payment = last_payment + pd.DateOffset(months=base_interval)
            
            # Check if we need to adjust based on known payment months
            try:
                known_months = sorted(payment_months)
                target_month = next_payment.month
                
                # Find the next month in the sequence
                found = False
                for _ in range(12):  # Try for a full year
                    if target_month in known_months:
                        found = True
                        break
                    next_payment += pd.DateOffset(months=1)
                    target_month = next_payment.month
                
                if not found:
                    # Default to base interval if we can't find a match
                    next_payment = last_payment + pd.DateOffset(months=base_interval)
            except Exception:
                # Fallback
                next_payment = last_payment + pd.DateOffset(months=base_interval)
        else:
            # Use average interval for irregular payments
            next_payment = last_payment + pd.DateOffset(days=int(avg_interval))
                
        # Get last payment amount
        last_amount = stock_payments.loc[stock_payments['Time'] == last_payment, 'Total'].iloc[0]
                
        # Store results
        results.append({
            'Name': stock,
            'Total Payments': len(stock_payments),
            'Last Payment Date': last_payment,
            'Last Amount': last_amount,
            'Payment Cadence': cadence,
            'Payment Months': ", ".join([month_names[m] for m in sorted(payment_months)]) if len(payment_months) > 0 else "Unknown",
            'Average Interval': f"{avg_interval:.1f} days" if 'avg_interval' in locals() else "Unknown",
            'Expected Next Payment': next_payment
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
    Display the Dividend Calendar tab content with simplified forecasting
    Only includes stocks with more than 1 payment
    """
    st.subheader("Dividend Calendar & Cadence Analysis")
    
    # Create tabs for different views
    calendar_views = st.tabs(["Stock Cadence & Next Payment", "Monthly Payment Calendar", "Calendar Settings"])
    
    # Load saved settings from session state
    if 'calendar_stocks' not in st.session_state:
        st.session_state.calendar_stocks = []
    
    if 'future_months' not in st.session_state:
        st.session_state.future_months = 12
        
    if 'lookback_months' not in st.session_state:
        st.session_state.lookback_months = 24
    
    # Tab 3: Calendar Settings
    with calendar_views[2]:
        st.subheader("Calendar Configuration")
        
        # Settings for calendar prediction
        st.session_state.future_months = st.slider(
            "Number of Months to Forecast", 
            1, 36, st.session_state.future_months,
            key="future_months_slider"
        )
        
        st.session_state.lookback_months = st.slider(
            "Historical Data to Consider (Months)", 
            6, 48, st.session_state.lookback_months,
            key="lookback_months_slider"
        )
        
        # Option to manually manage stocks in calendar
        st.subheader("Manual Stock Selection")
        
        # Get unique stocks from the dataframe
        all_stocks = sorted(df['Name'].unique())
        
        # Multi-select for stocks to include in calendar
        selected_stocks = st.multiselect(
            "Select Stocks to Include in Calendar",
            options=all_stocks,
            default=st.session_state.calendar_stocks if st.session_state.calendar_stocks else [],
            key="calendar_stock_selector"
        )
        
        # Save selected stocks to session state
        st.session_state.calendar_stocks = selected_stocks
        
        # Show information about manually selected stocks
        if selected_stocks:
            # Get payment information for selected stocks
            manual_stock_info = df[df['Name'].isin(selected_stocks)].copy()
            
            if not manual_stock_info.empty:
                # Group by stock and get last payment date and amount
                manual_info = manual_stock_info.groupby('Name').agg({
                    'Time': 'max',
                    'Total': lambda x: x.iloc[-1]
                }).reset_index()
                
                manual_info.columns = ['Stock', 'Last Payment Date', 'Last Amount']
                manual_info['Last Payment Date'] = manual_info['Last Payment Date'].dt.strftime('%d %b %Y')
                manual_info['Last Amount'] = manual_info['Last Amount'].apply(lambda x: format_currency(x, currency))
                
                st.write("Selected Stock Information:")
                st.dataframe(manual_info, use_container_width=True)
    
    # Use the state values for prediction
    future_months = st.session_state.future_months
    lookback_months = st.session_state.lookback_months
    
    # Create calendar using the function
    calendar_df, recent_stocks = create_dividend_calendar(df, future_months, lookback_months)
    
    # Tab 1: Stock Cadence Analysis
    with calendar_views[0]:
        st.subheader("Payment Cadence & Next Expected Dividend")
        
        # Get dividend cadence analysis
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
            display_columns = ['Name', 'Payment Cadence', 'Payment Months', 'Last Payment Date', 
                              'Last Amount', 'Expected Next Payment', 'Total Payments']
            
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
                    payment_date = row['Expected Next Payment']
                    stock_name = row['Name']
                    
                    fig.add_trace(go.Scatter(
                        x=[payment_date],
                        y=[stock_name],
                        mode='markers',
                        marker=dict(
                            symbol='diamond',
                            size=12,
                            color='#1a237e'
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
        
        # Add manually selected stocks to the calendar if they're not already there
        if st.session_state.calendar_stocks:
            # Filter manually selected stocks that aren't in the calendar
            manual_stocks = [s for s in st.session_state.calendar_stocks if s not in calendar_df['Name'].unique()]
            
            if manual_stocks:
                manual_additions = []
                
                for stock in manual_stocks:
                    # Get stock data
                    stock_data = df[df['Name'] == stock]
                    
                    if not stock_data.empty:
                        # Skip if less than 2 payments
                        if len(stock_data) < 2:
                            continue
                            
                        # Get the last payment
                        last_payment = stock_data.sort_values('Time', ascending=False).iloc[0]
                        last_payment_date = last_payment['Time']
                        last_amount = last_payment['Total']
                        
                        # Try to analyze the cadence
                        cadence_info = cadence_results[cadence_results['Name'] == stock]
                        
                        if not cadence_info.empty:
                            cadence = cadence_info.iloc[0]['Payment Cadence']
                            next_payment = cadence_info.iloc[0]['Expected Next Payment']
                        else:
                            cadence = "Unknown"
                            next_payment = last_payment_date + pd.DateOffset(months=3)  # Default to quarterly
                        
                        # Add to calendar for the next year
                        for month_offset in range(future_months):
                            forecast_date = datetime.now() + pd.DateOffset(months=month_offset)
                            year = forecast_date.year
                            month = forecast_date.month
                            
                            # Only add if the payment pattern suggests this month
                            payment_months = []
                            if "Quarterly" in cadence or "Semi-annual" in cadence:
                                # Extract the months from the cadence
                                month_str = cadence.split('(')[1].split(')')[0]
                                for m_name in month_str.split(', '):
                                    for m_num, m_full in month_names.items():
                                        if m_full == m_name:
                                            payment_months.append(m_num)
                                            break
                            
                            # If we're working with specific months, only add for those months
                            if payment_months and month not in payment_months:
                                continue
                                
                            # Otherwise add the stock to this month
                            manual_additions.append({
                                'Year': year,
                                'Month': month,
                                'Month Name': month_names[month],
                                'Period': f"{month_names[month]} {year}",
                                'Name': stock,
                                'Estimated Amount': last_amount,
                                'Last Payment': last_payment_date,
                                'Days Since Last': (datetime.now() - last_payment_date).days,
                                'Is Monthly': cadence == "Monthly",
                                'Is Manual': True  # Flag as manually added
                            })
                
                # Add manual additions to the calendar
                if manual_additions:
                    manual_df = pd.DataFrame(manual_additions)
                    calendar_df = pd.concat([calendar_df, manual_df], ignore_index=True)
                    calendar_df = calendar_df.sort_values(['Year', 'Month', 'Name'])
        
        if calendar_df.empty:
            st.warning("Not enough historical data to create reliable payment predictions.")
        else:
            # Summary of stocks with predicted payments
            st.subheader(f"Stocks with Predicted Payments ({len(calendar_df['Name'].unique())})")
            
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
            
            # Create a heatmap view of monthly dividends
            heatmap_data = []
            
            for _, month_row in months_to_display.iterrows():
                period = month_row['Period']
                year = month_row['Year']
                month = month_row['Month']
                
                # Get payments for this month
                month_payments = calendar_df[calendar_df['Period'] == period].copy()
                
                # Calculate total for the month
                month_total = month_payments['Estimated Amount'].sum()
                
                heatmap_data.append({
                    'Year': year,
                    'Month': month,
                    'MonthName': month_names[month],
                    'Period': period,
                    'TotalAmount': month_total,
                    'StockCount': len(month_payments)
                })
            
            heatmap_df = pd.DataFrame(heatmap_data)
            
            # Create a heatmap of monthly dividends
            fig_heatmap = px.imshow(
                heatmap_df.pivot(index='Year', columns='MonthName', values='TotalAmount'),
                labels=dict(x="Month", y="Year", color=f"Dividend Amount ({currency})"),
                x=[month_names[i] for i in range(1, 13)],
                color_continuous_scale="Blues",
                template="plotly_white" if theme == "Light" else "plotly_dark",
                title="Monthly Dividend Heatmap"
            )
            
            # Add text annotations
            for i, year in enumerate(heatmap_df['Year'].unique()):
                for month_num in range(1, 13):
                    month_name = month_names[month_num]
                    value = heatmap_df[(heatmap_df['Year'] == year) & (heatmap_df['Month'] == month_num)]['TotalAmount'].values
                    
                    if len(value) > 0:
                        value = value[0]
                        currency_symbol = {'GBP': '£', 'USD': '$', 'EUR': '€'}.get(currency, '£')
                        fig_heatmap.add_annotation(
                            x=month_name,
                            y=year,
                            text=f"{currency_symbol}{value:.0f}" if value > 0 else "",
                            showarrow=False,
                            font=dict(color="black" if value < 50 else "white")
                        )
            
            fig_heatmap.update_layout(height=400)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Display month by month details
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
                display_df = month_payments[['Name', 'Estimated Amount']].copy()
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
                        
                        # Create a list for each column
                        for _, row in col_stocks.iterrows():
                            col.markdown(
                                f"<div style='padding: 4px 0;'>"
                                f"<span style='font-weight: bold;'>{row['Name']}</span>: "
                                f"{row['Estimated Amount']} "
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
            
            # Add indication for manually added stocks
            if 'Is Manual' in table_df.columns:
                table_df['Is Manual'] = table_df['Is Manual'].fillna(False)
                table_df['Source'] = table_df['Is Manual'].apply(lambda x: "Manual" if x else "Auto-detected")
            
            # Select columns to display
            display_cols = ['Period', 'Name', 'Estimated Amount']
            if 'Last Payment' in table_df.columns:
                display_cols.append('Last Payment')
            if 'Source' in table_df.columns:
                display_cols.append('Source')
                
            display_table = table_df[display_cols]
            
            # Allow filtering by stock
            stock_filter = st.multiselect(
                "Filter by Stock",
                options=sorted(calendar_df['Name'].unique()),
                default=[]
            )
            
            filtered_table = display_table.copy()
            if stock_filter:
                filtered_table = filtered_table[filtered_table['Name'].isin(stock_filter)]
                
            st.dataframe(filtered_table, use_container_width=True)
            
            # Monthly summary chart
            monthly_payments = calendar_df.groupby('Period').agg({
                'Estimated Amount': 'sum',
                'Name': 'nunique'
            }).reset_index()
            
            monthly_payments.columns = ['Period', 'Total Amount', 'Stock Count']
            
            # Sort by year and month
            monthly_payments['Year'] = calendar_df.groupby('Period')['Year'].first().values
            monthly_payments['Month'] = calendar_df.groupby('Period')['Month'].first().values
            monthly_payments = monthly_payments.sort_values(['Year', 'Month'])
            
            # Create dual-axis chart for amount and stock count
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=monthly_payments['Period'],
                y=monthly_payments['Total Amount'],
                name='Total Amount',
                marker_color='#1a237e'
            ))
            
            fig.add_trace(go.Scatter(
                x=monthly_payments['Period'],
                y=monthly_payments['Stock Count'],
                name='Stock Count',
                mode='lines+markers',
                marker=dict(color='#e91e63'),
                line=dict(color='#e91e63'),
                yaxis='y2'
            ))
            
            fig.update_layout(
                title="Monthly Dividend Income & Stock Count",
                xaxis=dict(title="Month"),
                yaxis=dict(
                    title=f"Dividend Amount ({currency})",
                    side="left"
                ),
                yaxis2=dict(
                    title="Number of Stocks",
                    side="right",
                    overlaying="y",
                    showgrid=False
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=500,
                template="plotly_white" if theme == "Light" else "plotly_dark"
            )
            
            st.plotly_chart(fig, use_container_width=True)