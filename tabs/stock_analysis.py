import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_stock_analysis_tab(df, monthly_data, currency, theme, current_date, current_year, current_month, format_currency, **kwargs):
    """
    Display the Stock Analysis tab content with improved individual company selection
    
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
    # Create subtabs for different analysis views
    analysis_tabs = st.tabs(["Overall Analysis", "Individual Company Analysis"])
    
    with analysis_tabs[0]:
        # Add time period selection
        time_period = st.radio(
            "Select Time Period",
            ["Monthly", "Quarterly", "Yearly"],
            horizontal=True
        )
        
        # Stock breakdown - aggregated by selected time period
        if time_period == "Monthly":
            time_data = df.copy()
            # Create sorting field for chronological order
            time_data['Period'] = pd.to_datetime(time_data['Year'].astype(str) + '-' + 
                                               time_data['Month'].astype(str) + '-01')
            time_data['PeriodName'] = time_data['Period'].dt.strftime('%b %Y')
            time_data['PeriodKey'] = time_data['Period'].dt.strftime('%Y-%m')
        elif time_period == "Quarterly":
            time_data = df.copy()
            # Extract quarter number and year
            time_data['QuarterNum'] = time_data['Quarter'].str.split(' ').str[0].str[1].astype(int)
            time_data['QuarterYear'] = time_data['Quarter'].str.split(' ').str[1].astype(int)
            # Create period field for chronological order
            time_data['Period'] = pd.to_datetime(time_data['QuarterYear'].astype(str) + '-' + 
                                               ((time_data['QuarterNum'] * 3) - 2).astype(str) + '-01')
            time_data['PeriodName'] = time_data['Quarter']
            time_data['PeriodKey'] = time_data['QuarterYear'].astype(str) + '-Q' + time_data['QuarterNum'].astype(str)
        else:  # Yearly
            time_data = df.copy()
            time_data['Period'] = pd.to_datetime(time_data['Year'].astype(str) + '-01-01')
            time_data['PeriodName'] = time_data['Year'].astype(str)
            time_data['PeriodKey'] = time_data['Year'].astype(str)
        
        # Group by period and stock
        period_stock_data = time_data.groupby(['Period', 'PeriodName', 'PeriodKey', 'Name'])['Total'].sum().reset_index()
        
        # Sort chronologically by the Period datetime
        period_stock_data = period_stock_data.sort_values('Period')
        
        # Get ordered period names based on chronological sorting
        ordered_periods = period_stock_data['PeriodName'].unique()
        
        # Create pivot and unpivot for plotting
        period_pivot = period_stock_data.pivot(
            index='PeriodName', 
            columns='Name', 
            values='Total'
        ).fillna(0)
        
        # Ensure the index is in the right chronological order
        period_pivot = period_pivot.reindex(ordered_periods)
        
        # Convert to long format for Plotly
        period_long = pd.melt(
            period_pivot.reset_index(), 
            id_vars=['PeriodName'],
            var_name='Stock',
            value_name='Total'
        )
        
        # Create stacked bar chart showing all stocks
        fig_period = px.bar(
            period_long,
            x='PeriodName',
            y='Total',
            color='Stock',
            title=f"{time_period} Dividends by Stock",
            template="plotly_white" if theme == "Light" else "plotly_dark",
            labels={"Total": f"Dividend Amount ({currency})", "PeriodName": "Time Period"}
        )
        
        fig_period.update_layout(
            height=600,
            barmode='stack',
            xaxis=dict(
                title="Time Period",
                tickangle=-45,
                categoryorder='array',
                categoryarray=ordered_periods
            ),
            yaxis=dict(title=f"Dividend Amount ({currency})"),
            legend=dict(
                title="Stock"
            ),
            font=dict(color='black')
        )
        
        st.plotly_chart(fig_period, use_container_width=True)
        
        # Complete pie chart of all dividends
        stock_totals = df.groupby('Name')['Total'].sum().reset_index()
        stock_totals = stock_totals.sort_values('Total', ascending=False)
        
        # Calculate percentages
        stock_totals['Percentage'] = (stock_totals['Total'] / stock_totals['Total'].sum()) * 100
        
        # Full pie chart
        fig_pie = px.pie(
            stock_totals,
            values='Total',
            names='Name',
            title="Complete Dividend Distribution by Stock",
            template="plotly_white" if theme == "Light" else "plotly_dark",
            hole=0.4
        )
        
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            insidetextorientation='radial',
            textfont=dict(color='black'),
            insidetextfont=dict(color='black')
        )
        
        fig_pie.update_layout(
            height=600
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Stock table
        st.subheader("Stock Breakdown")
        
        # Format the table
        table_df = stock_totals.copy()
        table_df['Rank'] = range(1, len(table_df) + 1)
        table_df['Total'] = table_df['Total'].apply(lambda x: format_currency(x, currency))
        table_df['Percentage'] = table_df['Percentage'].apply(lambda x: f"{x:.1f}%")
        table_df = table_df[['Rank', 'Name', 'Total', 'Percentage']]
        
        # Add search/filter capability
        search_term = st.text_input("Search stocks", "", key="overall_search")
        if search_term:
            table_df = table_df[table_df['Name'].str.contains(search_term, case=False)]
        
        st.dataframe(table_df, use_container_width=True, height=400)
        
        # Concentration Risk Analysis
        st.subheader("Concentration Risk Analysis")
        
        # Calculate concentration metrics
        top_10_pct = stock_totals.head(10)['Percentage'].sum()
        top_5_pct = stock_totals.head(5)['Percentage'].sum()
        top_3_pct = stock_totals.head(3)['Percentage'].sum()
        top_1_pct = stock_totals.head(1)['Percentage'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Define risk levels
        def get_concentration_risk(pct, thresholds):
            if pct > thresholds[0]:
                return "High", "red"
            elif pct > thresholds[1]:
                return "Medium", "orange"
            else:
                return "Low", "green"
        
        top_1_risk, top_1_color = get_concentration_risk(top_1_pct, [15, 10])
        top_3_risk, top_3_color = get_concentration_risk(top_3_pct, [40, 25])
        top_5_risk, top_5_color = get_concentration_risk(top_5_pct, [60, 40])
        top_10_risk, top_10_color = get_concentration_risk(top_10_pct, [80, 60])
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{top_1_pct:.1f}%</div>
                <div class="metric-label">Top Stock</div>
                <div style="color: {top_1_color};">Risk: {top_1_risk}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{top_3_pct:.1f}%</div>
                <div class="metric-label">Top 3 Stocks</div>
                <div style="color: {top_3_color};">Risk: {top_3_risk}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{top_5_pct:.1f}%</div>
                <div class="metric-label">Top 5 Stocks</div>
                <div style="color: {top_5_color};">Risk: {top_5_risk}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{top_10_pct:.1f}%</div>
                <div class="metric-label">Top 10 Stocks</div>
                <div style="color: {top_10_color};">Risk: {top_10_risk}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # New Individual Company Analysis tab
    with analysis_tabs[1]:
        st.subheader("Individual Company Analysis")
        
        # Get unique companies
        companies = sorted(df['Name'].unique())
        
        # Company selection dropdown
        selected_company = st.selectbox(
            "Select Company to Analyze",
            options=companies,
            key="individual_company_selector"
        )
        
        if selected_company:
            # Filter data for the selected company
            company_data = df[df['Name'] == selected_company].copy()
            
            # Calculate key metrics
            total_dividends = company_data['Total'].sum()
            
            # Latest payment details
            latest_payment = company_data.sort_values('Time', ascending=False).iloc[0] if not company_data.empty else None
            latest_date = latest_payment['Time'] if latest_payment is not None else None
            latest_amount = latest_payment['Total'] if latest_payment is not None else 0
            
            # Payment frequency analysis
            payment_counts = len(company_data)
            unique_years = company_data['Year'].nunique()
            avg_frequency = payment_counts / unique_years if unique_years > 0 else 0
            
            # Determine payment cadence
            cadence = "Unknown"
            if avg_frequency >= 10:
                cadence = "Monthly"
            elif avg_frequency >= 3.5:
                cadence = "Quarterly"
            elif avg_frequency >= 1.5:
                cadence = "Semi-annual"
            elif avg_frequency >= 0.8:
                cadence = "Annual"
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Dividends Received",
                    format_currency(total_dividends, currency)
                )
            
            with col2:
                st.metric(
                    "Latest Payment",
                    format_currency(latest_amount, currency),
                    delta=f"{latest_date.strftime('%d %b %Y')}" if latest_date else None
                )
            
            with col3:
                st.metric(
                    "Payment Pattern",
                    cadence,
                    delta=f"{avg_frequency:.1f} payments/year"
                )
            
            # Create monthly/yearly aggregation
            company_monthly = company_data.copy()
            company_monthly['YearMonth'] = company_monthly['Time'].dt.strftime('%Y-%m')
            company_monthly['MonthYear'] = company_monthly['Time'].dt.strftime('%b %Y')
            monthly_totals = company_monthly.groupby(['YearMonth', 'MonthYear'])['Total'].sum().reset_index()
            monthly_totals = monthly_totals.sort_values('YearMonth')
            
            # Create a yearly aggregation
            yearly_totals = company_data.groupby('Year')['Total'].sum().reset_index()
            yearly_totals = yearly_totals.sort_values('Year')
            
            # Time series plot of payments
            fig_time = go.Figure()
            
            fig_time.add_trace(go.Scatter(
                x=company_data['Time'],
                y=company_data['Total'],
                mode='markers+lines',
                name='Individual Payments',
                marker=dict(size=10),
                line=dict(width=0)
            ))
            
            # Add trend line (moving average)
            if len(company_data) >= 3:
                company_data_sorted = company_data.sort_values('Time')
                company_data_sorted['MA3'] = company_data_sorted['Total'].rolling(window=3).mean()
                
                fig_time.add_trace(go.Scatter(
                    x=company_data_sorted['Time'],
                    y=company_data_sorted['MA3'],
                    mode='lines',
                    name='3-Point Moving Average',
                    line=dict(color='rgba(255, 165, 0, 0.7)', width=3)
                ))
            
            fig_time.update_layout(
                title=f"{selected_company} Dividend Payment History",
                template="plotly_white" if theme == "Light" else "plotly_dark",
                xaxis=dict(title="Date"),
                yaxis=dict(title=f"Dividend Amount ({currency})"),
                hovermode="closest",
                height=500
            )
            
            st.plotly_chart(fig_time, use_container_width=True)
            
            # Yearly bar chart
            fig_yearly = px.bar(
                yearly_totals,
                x='Year',
                y='Total',
                title=f"{selected_company} Annual Dividend Totals",
                template="plotly_white" if theme == "Light" else "plotly_dark",
                labels={"Total": f"Dividend Amount ({currency})", "Year": "Year"}
            )
            
            fig_yearly.update_traces(
                marker_color='#4e8df5',
                texttemplate='%{y:$.2f}',
                textposition='outside',
                textfont=dict(color='black')
            )
            
            fig_yearly.update_layout(
                height=400,
                xaxis=dict(type='category'),
                yaxis=dict(title=f"Dividend Amount ({currency})")
            )
            
            st.plotly_chart(fig_yearly, use_container_width=True)
            
            # Month-over-month growth analysis (if enough data)
            if len(monthly_totals) >= 3:
                st.subheader("Payment Growth Analysis")
                
                # Calculate changes in payment amounts
                monthly_totals['Previous'] = monthly_totals['Total'].shift(1)
                monthly_totals['Change'] = monthly_totals['Total'] - monthly_totals['Previous']
                monthly_totals['PercentChange'] = (monthly_totals['Change'] / monthly_totals['Previous'] * 100).fillna(0)
                
                # Filter out rows with missing previous values
                growth_data = monthly_totals.dropna(subset=['Previous'])
                
                if not growth_data.empty:
                    fig_growth = go.Figure()
                    
                    fig_growth.add_trace(go.Bar(
                        x=growth_data['MonthYear'],
                        y=growth_data['PercentChange'],
                        marker_color=growth_data['PercentChange'].apply(
                            lambda x: 'rgba(76, 175, 80, 0.7)' if x >= 0 else 'rgba(239, 83, 80, 0.7)'
                        ),
                        name='Percent Change'
                    ))
                    
                    fig_growth.update_layout(
                        title=f"{selected_company} Dividend Growth (Month-to-Month)",
                        template="plotly_white" if theme == "Light" else "plotly_dark",
                        xaxis=dict(title="Month", tickangle=-45),
                        yaxis=dict(title="Percent Change (%)"),
                        height=400
                    )
                    
                    st.plotly_chart(fig_growth, use_container_width=True)
            
            # Payment details table
            st.subheader("Payment History")
            
            payment_history = company_data.sort_values('Time', ascending=False).copy()
            payment_history['FormattedDate'] = payment_history['Time'].dt.strftime('%d %b %Y')
            payment_history['FormattedAmount'] = payment_history['Total'].apply(lambda x: format_currency(x, currency))
            
            display_history = payment_history[['FormattedDate', 'FormattedAmount']].rename(
                columns={'FormattedDate': 'Payment Date', 'FormattedAmount': 'Amount'}
            )
            
            st.dataframe(display_history, use_container_width=True, height=300)