import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show_stock_analysis_tab(
    df,
    monthly_data,
    currency,
    theme,
    current_date,
    current_year,
    current_month,
    format_currency,
    **kwargs,
):
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
    analysis_tabs = st.tabs(["Time Period Analysis", "Individual Company Analysis"])

    with analysis_tabs[0]:
        # Add time period selection
        time_period = st.radio(
            "Select Time Period", ["Monthly", "Quarterly", "Yearly"], horizontal=True
        )

        # Create totals by time period broken down by stock
        if time_period == "Monthly":
            time_data = df.copy()
            # Create sorting field for chronological order
            time_data["Period"] = pd.to_datetime(
                time_data["Year"].astype(str)
                + "-"
                + time_data["Month"].astype(str)
                + "-01"
            )
            time_data["PeriodName"] = time_data["Period"].dt.strftime("%b %Y")
            time_data["PeriodKey"] = time_data["Period"].dt.strftime("%Y-%m")

            # Group by period AND stock name
            period_totals = (
                time_data.groupby(["Period", "PeriodName", "PeriodKey", "Name"])["Total"]
                .sum()
                .reset_index()
            )

        elif time_period == "Quarterly":
            time_data = df.copy()
            # Extract quarter number and year
            time_data["QuarterNum"] = (
                time_data["Quarter"].str.split(" ").str[0].str[1].astype(int)
            )
            time_data["QuarterYear"] = (
                time_data["Quarter"].str.split(" ").str[1].astype(int)
            )
            # Create period field for chronological order
            time_data["Period"] = pd.to_datetime(
                time_data["QuarterYear"].astype(str)
                + "-"
                + ((time_data["QuarterNum"] * 3) - 2).astype(str)
                + "-01"
            )
            time_data["PeriodName"] = time_data["Quarter"]
            time_data["PeriodKey"] = (
                time_data["QuarterYear"].astype(str)
                + "-Q"
                + time_data["QuarterNum"].astype(str)
            )

            # Group by period AND stock name
            period_totals = (
                time_data.groupby(["Period", "PeriodName", "PeriodKey", "Name"])["Total"]
                .sum()
                .reset_index()
            )

        else:  # Yearly
            time_data = df.copy()
            time_data["Period"] = pd.to_datetime(
                time_data["Year"].astype(str) + "-01-01"
            )
            time_data["PeriodName"] = time_data["Year"].astype(str)
            time_data["PeriodKey"] = time_data["Year"].astype(str)

            # Group by period AND stock name
            period_totals = (
                time_data.groupby(["Period", "PeriodName", "PeriodKey", "Name"])["Total"]
                .sum()
                .reset_index()
            )

        # Sort chronologically by the Period datetime
        period_totals = period_totals.sort_values("Period")

        # Create stacked bar chart using graph_objects for better control
        fig_period = go.Figure()

        # Get unique stocks and periods
        stocks = period_totals["Name"].unique()
        periods = period_totals.sort_values("Period")["PeriodName"].unique()

        # Add a trace for each stock
        for stock in stocks:
            stock_data = period_totals[period_totals["Name"] == stock]

            # Create a dict mapping period to total for this stock
            period_to_total = dict(zip(stock_data["PeriodName"], stock_data["Total"]))

            # Create y values for all periods (0 if stock didn't pay in that period)
            y_values = [period_to_total.get(period, 0) for period in periods]

            fig_period.add_trace(
                go.Bar(
                    name=stock,
                    x=periods,
                    y=y_values,
                    text=[f"{v:,.0f}" if v > 0 else "" for v in y_values],
                    textposition="inside",
                    textfont=dict(color="white", size=10),
                    hovertemplate=f"<b>{stock}</b><br>Period: %{{x}}<br>Amount: {currency}%{{y:,.2f}}<extra></extra>",
                )
            )

        fig_period.update_layout(
            barmode="stack",
            title=f"{time_period} Dividend Income by Stock",
            template="plotly_white" if theme == "Light" else "plotly_dark",
            height=600,
            xaxis=dict(title="Time Period", tickangle=-45),
            yaxis=dict(title=f"Dividend Amount ({currency})"),
            showlegend=True,
            legend=dict(
                title=dict(text="Stock"),
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
            ),
            font=dict(color="black"),
        )

        st.plotly_chart(fig_period, use_container_width=True)

        # Add pie chart showing distribution by stocks
        st.subheader("Portfolio Distribution by Stock")

        # Calculate stock totals for pie chart
        stock_totals = df.groupby("Name")["Total"].sum().reset_index()
        stock_totals = stock_totals.sort_values("Total", ascending=False)

        # Calculate percentages
        stock_totals["Percentage"] = (
            stock_totals["Total"] / stock_totals["Total"].sum()
        ) * 100

        # Create pie chart
        fig_pie = px.pie(
            stock_totals,
            values="Total",
            names="Name",
            title="Complete Dividend Distribution by Stock",
            template="plotly_white" if theme == "Light" else "plotly_dark",
            hole=0.4,
        )

        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent+label",
            insidetextorientation="radial",
            textfont=dict(color="black"),
            insidetextfont=dict(color="black"),
        )

        fig_pie.update_layout(height=600)

        st.plotly_chart(fig_pie, use_container_width=True)

        # Growth analysis chart
        # For growth analysis, we need to calculate total per period first
        period_summary = period_totals.groupby(["Period", "PeriodName", "PeriodKey"])["Total"].sum().reset_index()

        if len(period_summary) > 1:
            st.subheader(f"{time_period} Growth Analysis")

            # Calculate period-over-period growth
            period_totals_sorted = period_summary.sort_values("Period").copy()
            period_totals_sorted["Previous"] = period_totals_sorted["Total"].shift(1)
            period_totals_sorted["Growth"] = (
                (period_totals_sorted["Total"] - period_totals_sorted["Previous"])
                / period_totals_sorted["Previous"]
                * 100
            )
            period_totals_sorted["Growth"] = period_totals_sorted["Growth"].fillna(0)

            # Create growth chart
            fig_growth = go.Figure()

            # Add growth bars
            colors = [
                "rgba(76, 175, 80, 0.7)" if x >= 0 else "rgba(239, 83, 80, 0.7)"
                for x in period_totals_sorted["Growth"]
            ]

            fig_growth.add_trace(
                go.Bar(
                    x=period_totals_sorted["PeriodName"],
                    y=period_totals_sorted["Growth"],
                    marker_color=colors,
                    name="Growth %",
                    text=[f"{x:.1f}%" for x in period_totals_sorted["Growth"]],
                    textposition="outside",
                )
            )

            fig_growth.update_layout(
                title=f"{time_period} Growth Rate (%)",
                template="plotly_white" if theme == "Light" else "plotly_dark",
                xaxis=dict(title="Time Period", tickangle=-45),
                yaxis=dict(title="Growth Rate (%)"),
                height=400,
                showlegend=False,
            )

            st.plotly_chart(fig_growth, use_container_width=True)

        # Time period breakdown table
        st.subheader(f"{time_period} Breakdown")

        # Format the table using period_summary (total per period)
        table_df = period_summary.copy()
        table_df["Rank"] = range(1, len(table_df) + 1)
        table_df["FormattedTotal"] = table_df["Total"].apply(
            lambda x: format_currency(x, currency)
        )

        # Calculate percentage of total
        total_sum = table_df["Total"].sum()
        table_df["Percentage"] = (table_df["Total"] / total_sum * 100).apply(
            lambda x: f"{x:.1f}%"
        )

        # Add growth rate if available
        if "Growth" in period_totals_sorted.columns:
            growth_dict = dict(
                zip(period_totals_sorted["PeriodName"], period_totals_sorted["Growth"])
            )
            table_df["Growth"] = (
                table_df["PeriodName"]
                .map(growth_dict)
                .fillna(0)
                .apply(lambda x: f"{x:.1f}%")
            )
            display_cols = [
                "Rank",
                "PeriodName",
                "FormattedTotal",
                "Percentage",
                "Growth",
            ]
        else:
            display_cols = ["Rank", "PeriodName", "FormattedTotal", "Percentage"]

        table_df = table_df[display_cols]
        table_df = table_df.rename(
            columns={
                "PeriodName": "Period",
                "FormattedTotal": "Total Amount",
                "Percentage": "% of Total",
            }
        )

        st.dataframe(table_df, use_container_width=True, height=400)

        # Summary statistics with modern dark cards
        st.subheader("Summary Statistics")
        
        # Add CSS for modern dark cards
        st.markdown("""
        <style>
        .modern-card {
            background: #2d3748;
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            border: 1px solid #4a5568;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        .modern-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        }
        .modern-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }
        .card-title {
            color: #a0aec0;
            font-size: 0.875rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .card-icon {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #667eea;
        }
        .card-value {
            color: #ffffff;
            font-size: 1.875rem;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 0.25rem;
        }
        .card-subtitle {
            color: #718096;
            font-size: 0.75rem;
            font-weight: 400;
        }
        </style>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            avg_amount = period_summary["Total"].mean()
            st.markdown(f"""
            <div class="modern-card">
                <div class="card-header">
                    <span class="card-title">Average Amount</span>
                    <div class="card-icon" style="background: #667eea;"></div>
                </div>
                <div class="card-value">{format_currency(avg_amount, currency)}</div>
                <div class="card-subtitle">Per period average</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            max_amount = period_summary["Total"].max()
            best_period = period_summary[period_summary["Total"] == max_amount][
                "PeriodName"
            ].iloc[0]
            st.markdown(f"""
            <div class="modern-card">
                <div class="card-header">
                    <span class="card-title">Best Period</span>
                    <div class="card-icon" style="background: #48bb78;"></div>
                </div>
                <div class="card-value">{best_period}</div>
                <div class="card-subtitle">{format_currency(max_amount, currency)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            if len(period_summary) > 1 and "Growth" in period_totals_sorted.columns:
                avg_growth = period_totals_sorted["Growth"].mean()
                stat_value = f"{avg_growth:.1f}%"
                stat_label = "Avg Growth Rate"
                subtitle = "Period over period"
                icon_color = "#ed8936" if avg_growth >= 0 else "#f56565"
            else:
                stat_value = str(len(period_summary))
                stat_label = "Total Periods"
                subtitle = "Data points available"
                icon_color = "#9f7aea"

            st.markdown(f"""
            <div class="modern-card">
                <div class="card-header">
                    <span class="card-title">{stat_label}</span>
                    <div class="card-icon" style="background: {icon_color};"></div>
                </div>
                <div class="card-value">{stat_value}</div>
                <div class="card-subtitle">{subtitle}</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            total_all = period_summary["Total"].sum()
            st.markdown(f"""
            <div class="modern-card">
                <div class="card-header">
                    <span class="card-title">Total Income</span>
                    <div class="card-icon" style="background: #38b2ac;"></div>
                </div>
                <div class="card-value">{format_currency(total_all, currency)}</div>
                <div class="card-subtitle">All periods combined</div>
            </div>
            """, unsafe_allow_html=True)

        # Stock concentration risk analysis with modern cards
        st.subheader("Stock Concentration Risk Analysis")

        # Calculate concentration metrics using stock_totals from pie chart
        top_10_pct = stock_totals.head(10)["Percentage"].sum()
        top_5_pct = stock_totals.head(5)["Percentage"].sum()
        top_3_pct = stock_totals.head(3)["Percentage"].sum()
        top_1_pct = stock_totals.head(1)["Percentage"].sum()

        col1, col2, col3, col4 = st.columns(4)

        # Define risk levels with modern colors
        def get_concentration_risk(pct, thresholds):
            if pct > thresholds[0]:
                return "High", "#f56565", "#fed7d7"
            elif pct > thresholds[1]:
                return "Medium", "#ed8936", "#feebc8"
            else:
                return "Low", "#48bb78", "#c6f6d5"

        top_1_risk, top_1_color, top_1_bg = get_concentration_risk(top_1_pct, [15, 10])
        top_3_risk, top_3_color, top_3_bg = get_concentration_risk(top_3_pct, [40, 25])
        top_5_risk, top_5_color, top_5_bg = get_concentration_risk(top_5_pct, [60, 40])
        top_10_risk, top_10_color, top_10_bg = get_concentration_risk(top_10_pct, [80, 60])

        with col1:
            st.markdown(f"""
            <div class="modern-card">
                <div class="card-header">
                    <span class="card-title">Top Stock</span>
                    <div class="card-icon" style="background: {top_1_color};"></div>
                </div>
                <div class="card-value">{top_1_pct:.1f}%</div>
                <div class="card-subtitle" style="color: {top_1_color};">Risk: {top_1_risk}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="modern-card">
                <div class="card-header">
                    <span class="card-title">Top 3 Stocks</span>
                    <div class="card-icon" style="background: {top_3_color};"></div>
                </div>
                <div class="card-value">{top_3_pct:.1f}%</div>
                <div class="card-subtitle" style="color: {top_3_color};">Risk: {top_3_risk}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="modern-card">
                <div class="card-header">
                    <span class="card-title">Top 5 Stocks</span>
                    <div class="card-icon" style="background: {top_5_color};"></div>
                </div>
                <div class="card-value">{top_5_pct:.1f}%</div>
                <div class="card-subtitle" style="color: {top_5_color};">Risk: {top_5_risk}</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="modern-card">
                <div class="card-header">
                    <span class="card-title">Top 10 Stocks</span>
                    <div class="card-icon" style="background: {top_10_color};"></div>
                </div>
                <div class="card-value">{top_10_pct:.1f}%</div>
                <div class="card-subtitle" style="color: {top_10_color};">Risk: {top_10_risk}</div>
            </div>
            """, unsafe_allow_html=True)

    # New Individual Company Analysis tab
    with analysis_tabs[1]:
        st.subheader("Individual Company Analysis")

        # Get unique companies
        companies = sorted(df["Name"].unique())

        # Company selection dropdown
        selected_company = st.selectbox(
            "Select Company to Analyze",
            options=companies,
            key="individual_company_selector",
        )

        if selected_company:
            # Filter data for the selected company
            company_data = df[df["Name"] == selected_company].copy()

            # Calculate key metrics
            total_dividends = company_data["Total"].sum()

            # Latest payment details
            latest_payment = (
                company_data.sort_values("Time", ascending=False).iloc[0]
                if not company_data.empty
                else None
            )
            latest_date = latest_payment["Time"] if latest_payment is not None else None
            latest_amount = latest_payment["Total"] if latest_payment is not None else 0

            # Payment frequency analysis
            payment_counts = len(company_data)
            unique_years = company_data["Year"].nunique()
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
                    format_currency(total_dividends, currency),
                )

            with col2:
                st.metric(
                    "Latest Payment",
                    format_currency(latest_amount, currency),
                    delta=f"{latest_date.strftime('%d %b %Y')}"
                    if latest_date
                    else None,
                )

            with col3:
                st.metric(
                    "Payment Pattern",
                    cadence,
                    delta=f"{avg_frequency:.1f} payments/year",
                )

            # Create monthly/yearly aggregation
            company_monthly = company_data.copy()
            company_monthly["YearMonth"] = company_monthly["Time"].dt.strftime("%Y-%m")
            company_monthly["MonthYear"] = company_monthly["Time"].dt.strftime("%b %Y")
            monthly_totals = (
                company_monthly.groupby(["YearMonth", "MonthYear"])["Total"]
                .sum()
                .reset_index()
            )
            monthly_totals = monthly_totals.sort_values("YearMonth")

            # Create a yearly aggregation
            yearly_totals = company_data.groupby("Year")["Total"].sum().reset_index()
            yearly_totals = yearly_totals.sort_values("Year")

            # Time series plot of payments
            fig_time = go.Figure()

            fig_time.add_trace(
                go.Scatter(
                    x=company_data["Time"],
                    y=company_data["Total"],
                    mode="markers+lines",
                    name="Individual Payments",
                    marker=dict(size=10),
                    line=dict(width=0),
                )
            )

            # Add trend line (moving average)
            if len(company_data) >= 3:
                company_data_sorted = company_data.sort_values("Time")
                company_data_sorted["MA3"] = (
                    company_data_sorted["Total"].rolling(window=3).mean()
                )

                fig_time.add_trace(
                    go.Scatter(
                        x=company_data_sorted["Time"],
                        y=company_data_sorted["MA3"],
                        mode="lines",
                        name="3-Point Moving Average",
                        line=dict(color="rgba(255, 165, 0, 0.7)", width=3),
                    )
                )

            fig_time.update_layout(
                title=f"{selected_company} Dividend Payment History",
                template="plotly_white" if theme == "Light" else "plotly_dark",
                xaxis=dict(title="Date"),
                yaxis=dict(title=f"Dividend Amount ({currency})"),
                hovermode="closest",
                height=500,
            )

            st.plotly_chart(fig_time, use_container_width=True)

            # Yearly bar chart
            fig_yearly = px.bar(
                yearly_totals,
                x="Year",
                y="Total",
                title=f"{selected_company} Annual Dividend Totals",
                template="plotly_white" if theme == "Light" else "plotly_dark",
                labels={"Total": f"Dividend Amount ({currency})", "Year": "Year"},
            )

            fig_yearly.update_traces(
                marker_color="#4e8df5",
                texttemplate="%{y:$.2f}",
                textposition="outside",
                textfont=dict(color="black"),
            )

            fig_yearly.update_layout(
                height=400,
                xaxis=dict(type="category"),
                yaxis=dict(title=f"Dividend Amount ({currency})"),
            )

            st.plotly_chart(fig_yearly, use_container_width=True)

            # Month-over-month growth analysis (if enough data)
            if len(monthly_totals) >= 3:
                st.subheader("Payment Growth Analysis")

                # Calculate changes in payment amounts
                monthly_totals["Previous"] = monthly_totals["Total"].shift(1)
                monthly_totals["Change"] = (
                    monthly_totals["Total"] - monthly_totals["Previous"]
                )
                monthly_totals["PercentChange"] = (
                    monthly_totals["Change"] / monthly_totals["Previous"] * 100
                ).fillna(0)

                # Filter out rows with missing previous values
                growth_data = monthly_totals.dropna(subset=["Previous"])

                if not growth_data.empty:
                    fig_growth = go.Figure()

                    fig_growth.add_trace(
                        go.Bar(
                            x=growth_data["MonthYear"],
                            y=growth_data["PercentChange"],
                            marker_color=growth_data["PercentChange"].apply(
                                lambda x: "rgba(76, 175, 80, 0.7)"
                                if x >= 0
                                else "rgba(239, 83, 80, 0.7)"
                            ),
                            name="Percent Change",
                        )
                    )

                    fig_growth.update_layout(
                        title=f"{selected_company} Dividend Growth (Month-to-Month)",
                        template="plotly_white" if theme == "Light" else "plotly_dark",
                        xaxis=dict(title="Month", tickangle=-45),
                        yaxis=dict(title="Percent Change (%)"),
                        height=400,
                    )

                    st.plotly_chart(fig_growth, use_container_width=True)

            # Payment details table
            st.subheader("Payment History")

            payment_history = company_data.sort_values("Time", ascending=False).copy()
            payment_history["FormattedDate"] = payment_history["Time"].dt.strftime(
                "%d %b %Y"
            )
            payment_history["FormattedAmount"] = payment_history["Total"].apply(
                lambda x: format_currency(x, currency)
            )

            display_history = payment_history[
                ["FormattedDate", "FormattedAmount"]
            ].rename(
                columns={"FormattedDate": "Payment Date", "FormattedAmount": "Amount"}
            )

            st.dataframe(display_history, use_container_width=True, height=300)
