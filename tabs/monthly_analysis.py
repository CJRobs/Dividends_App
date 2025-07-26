import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_monthly_analysis_tab(df, monthly_data, currency, theme, current_date, current_year, current_month, format_currency, get_month_order, **kwargs):
    """
    Display the Monthly Analysis tab content
    
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
    get_month_order : function
        Function to get the proper month order
    """
    month_order = get_month_order()
    
    # Monthly totals by year
    monthly_by_year = df.pivot_table(
        index='MonthName',
        columns='Year',
        values='Total',
        aggfunc='sum'
    ).reset_index()
    
    # Correct month order
    monthly_by_year['MonthNum'] = monthly_by_year['MonthName'].apply(lambda x: month_order.index(x))
    monthly_by_year = monthly_by_year.sort_values('MonthNum')
    monthly_by_year = monthly_by_year.drop('MonthNum', axis=1)
    
    # Monthly line chart
    # Prep data for plotly
    years = [col for col in monthly_by_year.columns if col not in ['MonthName', 'MonthNum']]
    
    fig_monthly_line = go.Figure()
    
    for year in years:
        fig_monthly_line.add_trace(go.Scatter(
            x=monthly_by_year['MonthName'],
            y=monthly_by_year[year],
            mode='lines+markers',
            name=str(year),
            line=dict(width=3)
        ))
    
    fig_monthly_line.update_layout(
        title="Monthly Dividends by Year",
        template="plotly_white" if theme == "Light" else "plotly_dark",
        xaxis=dict(
            title="Month",
            categoryorder='array',
            categoryarray=month_order
        ),
        yaxis=dict(title=f"Dividend Amount ({currency})"),
        legend=dict(
            title="Year",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )
    
    st.plotly_chart(fig_monthly_line, use_container_width=True)
    
    # Monthly heatmap
    monthly_pivot = df.pivot_table(
        index='Year',
        columns='MonthName',
        values='Total',
        aggfunc='sum'
    ).fillna(0)
    
    # Ensure all months are present
    for month in month_order:
        if month not in monthly_pivot.columns:
            monthly_pivot[month] = 0
    
    # Reorder columns
    monthly_pivot = monthly_pivot[month_order]
    
    fig_heatmap = px.imshow(
        monthly_pivot,
        labels=dict(x="Month", y="Year", color=f"Dividend Amount ({currency})"),
        x=month_order,
        y=monthly_pivot.index,
        color_continuous_scale="Blues",
        template="plotly_white" if theme == "Light" else "plotly_dark",
        title="Monthly Dividend Heatmap"
    )
    
    fig_heatmap.update_layout(
        height=500,
        xaxis=dict(title="Month"),
        yaxis=dict(title="Year")
    )
    
    # Add text annotations to heatmap
    for i, year in enumerate(monthly_pivot.index):
        for j, month in enumerate(month_order):
            value = monthly_pivot.loc[year, month]
            currency_symbol = {'GBP': '£', 'USD': '$', 'EUR': '€'}.get(currency, '£')
            fig_heatmap.add_annotation(
                x=month,
                y=year,
                text=f"{currency_symbol}{value:.0f}" if value > 0 else "",
                showarrow=False,
                font=dict(color="black" if value < 50 else "white")
            )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Dividends by Company by Month (stacked bar chart)
    st.subheader("Dividends by Company by Month")
    
    # Get unique companies
    companies = sorted(df['Name'].unique())
    
    # Stock/company selection dropdown
    selected_stocks = st.multiselect(
        "Select Companies to View (leave empty to see all)",
        options=companies,
        default=[]
    )
    
    # Filter data based on selection
    if selected_stocks:
        filtered_df = df[df['Name'].isin(selected_stocks)]
    else:
        filtered_df = df
    
    # Group by month and company
    monthly_by_company = filtered_df.groupby(['MonthName', 'Month', 'Name'])['Total'].sum().reset_index()
    monthly_by_company['MonthNum'] = monthly_by_company['MonthName'].apply(lambda x: month_order.index(x))
    monthly_by_company = monthly_by_company.sort_values('MonthNum')
    
    # Create stacked bar chart
    fig_monthly_company = px.bar(
        monthly_by_company,
        x='MonthName',
        y='Total',
        color='Name',
        title="Monthly Dividends by Company",
        template="plotly_white" if theme == "Light" else "plotly_dark",
        labels={"Total": f"Dividend Amount ({currency})", "MonthName": "Month", "Name": "Company"}
    )
    
    fig_monthly_company.update_layout(
        height=500,
        xaxis=dict(
            categoryorder='array',
            categoryarray=month_order,
            title="Month"
        ),
        yaxis=dict(title=f"Dividend Amount ({currency})"),
        legend=dict(
            title="Company",
            orientation="v"
        ),
        barmode='stack'
    )
    
    # Ensure all text is black
    fig_monthly_company.update_layout(
        font=dict(color='black')
    )
    
    st.plotly_chart(fig_monthly_company, use_container_width=True)
    
    # Monthly Income Coverage Analysis - using most recent complete month
    st.subheader("Monthly Income Coverage Analysis")
    
    # Get most recent complete month data
    recent_months = monthly_data[
        (monthly_data['Time'].dt.year < current_year) | 
        ((monthly_data['Time'].dt.year == current_year) & 
         (monthly_data['Time'].dt.month < current_month))
    ]
    
    if not recent_months.empty:
        most_recent_month_data = recent_months.iloc[-1]
        most_recent_month_amount = most_recent_month_data['Total_Sum']
        most_recent_month_name = most_recent_month_data['Time'].strftime('%B %Y')
    else:
        most_recent_month_amount = 0
        most_recent_month_name = "No data"
    
    # Calculate percentage of living expenses covered
    monthly_expenses = st.number_input(
        "Your Monthly Expenses", 
        min_value=0.0, 
        value=2000.0, 
        step=100.0,
        format="%.2f",
        help="Enter your average monthly expenses to see how much is covered by dividends",
        key="monthly_analysis_expenses"
    )
    
    # Calculate coverage based on most recent month
    coverage_percent = (most_recent_month_amount / monthly_expenses) * 100 if monthly_expenses > 0 else 0
    coverage_percent = min(coverage_percent, 100)  # Cap at 100%
    
    # Create a progress bar
    st.subheader(f"Expense Coverage for {most_recent_month_name}")
    st.progress(coverage_percent / 100)
    
    st.metric(
        "Current Coverage",
        f"{coverage_percent:.1f}%",
        delta=None
    )
    
    st.metric(
        "Amount Received",
        format_currency(most_recent_month_amount, currency),
        delta=None
    )
    
    # Gap to goal
    gap_amount = max(0, monthly_expenses - most_recent_month_amount)
    if gap_amount > 0:
        st.metric(
            "Gap to 100% Coverage",
            format_currency(gap_amount, currency),
            delta=None,
            delta_color="inverse"
        )