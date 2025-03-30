import streamlit as st
import pandas as pd
import plotly.express as px

def show_stock_analysis_tab(df, monthly_data, currency, theme, current_date, current_year, current_month, format_currency, **kwargs):
    """
    Display the Stock Analysis tab content
    
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
    search_term = st.text_input("Search stocks", "")
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