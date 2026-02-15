"""
Analysis and risk scoring logic for the Dividend Screener.

Contains dividend metrics, risk factor scoring, growth analysis,
analyst sentiment, and investment summary generation.
"""

from typing import List, Optional, Tuple
from app.models.screener import (
    CompanyOverview, DividendHistory, BalanceSheet, CashFlow,
    IncomeStatement, DividendMetrics, RiskFactors, GrowthMetrics,
    AnalystSentiment, AnnualEarnings,
)


def calculate_dividend_metrics(
    dividends: List[DividendHistory],
    cashflow: List[CashFlow],
) -> DividendMetrics:
    """Calculate dividend-specific metrics from history."""
    if not dividends:
        return DividendMetrics()

    amounts = [d.amount for d in dividends]
    total_paid = sum(amounts)
    avg_amount = total_paid / len(amounts) if amounts else None

    # Growth rate (sequential comparison)
    growth_rates = []
    sorted_divs = sorted(dividends, key=lambda x: x.ex_date)
    for i in range(1, len(sorted_divs)):
        prev_amount = sorted_divs[i - 1].amount
        curr_amount = sorted_divs[i].amount
        if prev_amount > 0:
            growth = ((curr_amount - prev_amount) / prev_amount) * 100
            growth_rates.append(growth)

    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else None

    # Consecutive growth years
    consecutive_years = 0
    for i in range(1, len(sorted_divs)):
        if sorted_divs[i].amount >= sorted_divs[i - 1].amount:
            consecutive_years += 1
        else:
            consecutive_years = 0

    # FCF coverage ratio
    fcf_coverage = None
    if cashflow and len(cashflow) > 0:
        latest_cf = cashflow[0]
        if latest_cf.free_cashflow and latest_cf.dividend_payout:
            div_payout = abs(latest_cf.dividend_payout)
            if div_payout > 0:
                fcf_coverage = round(latest_cf.free_cashflow / div_payout, 2)

    # Consistency rating
    if len(dividends) >= 12 and consecutive_years >= 8:
        consistency = "Excellent"
    elif len(dividends) >= 8 and consecutive_years >= 4:
        consistency = "Good"
    elif len(dividends) >= 4:
        consistency = "Fair"
    else:
        consistency = "Limited Data"

    return DividendMetrics(
        dividend_growth_rate=avg_growth,
        fcf_coverage_ratio=fcf_coverage,
        consecutive_growth_years=consecutive_years,
        dividend_consistency=consistency,
        avg_dividend_amount=avg_amount,
        total_dividends_paid=total_paid,
    )


def calculate_risk_factors(
    overview: CompanyOverview,
    balance: List[BalanceSheet],
    cashflow: List[CashFlow],
    dividend_metrics: DividendMetrics,
) -> Tuple[RiskFactors, float, str, str]:
    """
    Calculate individual risk factors and overall risk score.
    Returns (risk_factors, risk_score, risk_level, risk_grade).
    """
    yield_risk = 50.0
    payout_risk = 50.0
    valuation_risk = 50.0
    leverage_risk = 50.0
    volatility_risk = 50.0
    coverage_risk = 50.0

    # 1. Yield Risk
    if overview.dividend_yield:
        if overview.dividend_yield > 0.08:
            yield_risk = 90
        elif overview.dividend_yield > 0.06:
            yield_risk = 70
        elif overview.dividend_yield > 0.04:
            yield_risk = 50
        elif overview.dividend_yield > 0.02:
            yield_risk = 30
        else:
            yield_risk = 40

    # 2. Payout Risk
    if overview.payout_ratio:
        if overview.payout_ratio > 1.0:
            payout_risk = 95
        elif overview.payout_ratio > 0.9:
            payout_risk = 80
        elif overview.payout_ratio > 0.7:
            payout_risk = 60
        elif overview.payout_ratio > 0.5:
            payout_risk = 40
        else:
            payout_risk = 25

    # 3. Valuation Risk
    if overview.pe_ratio:
        if overview.pe_ratio > 40:
            valuation_risk = 85
        elif overview.pe_ratio > 30:
            valuation_risk = 70
        elif overview.pe_ratio > 20:
            valuation_risk = 50
        elif overview.pe_ratio > 10 and overview.pe_ratio > 0:
            valuation_risk = 35
        elif overview.pe_ratio > 0:
            valuation_risk = 25

    # 4. Leverage Risk
    if balance and len(balance) > 0:
        latest = balance[0]
        if latest.debt_to_equity is not None:
            if latest.debt_to_equity > 3:
                leverage_risk = 90
            elif latest.debt_to_equity > 2:
                leverage_risk = 75
            elif latest.debt_to_equity > 1:
                leverage_risk = 55
            elif latest.debt_to_equity > 0.5:
                leverage_risk = 35
            else:
                leverage_risk = 20

    # 5. Volatility Risk
    if overview.beta:
        if overview.beta > 2.0:
            volatility_risk = 90
        elif overview.beta > 1.5:
            volatility_risk = 75
        elif overview.beta > 1.2:
            volatility_risk = 60
        elif overview.beta > 0.8:
            volatility_risk = 40
        else:
            volatility_risk = 25

    # 6. Coverage Risk
    if dividend_metrics.fcf_coverage_ratio is not None:
        if dividend_metrics.fcf_coverage_ratio < 1.0:
            coverage_risk = 90
        elif dividend_metrics.fcf_coverage_ratio < 1.2:
            coverage_risk = 70
        elif dividend_metrics.fcf_coverage_ratio < 1.5:
            coverage_risk = 50
        elif dividend_metrics.fcf_coverage_ratio < 2.0:
            coverage_risk = 35
        else:
            coverage_risk = 20

    risk_factors = RiskFactors(
        yield_risk=yield_risk,
        payout_risk=payout_risk,
        valuation_risk=valuation_risk,
        leverage_risk=leverage_risk,
        volatility_risk=volatility_risk,
        coverage_risk=coverage_risk,
    )

    # Weighted overall score
    overall_score = (
        yield_risk * 0.15 +
        payout_risk * 0.20 +
        valuation_risk * 0.15 +
        leverage_risk * 0.20 +
        volatility_risk * 0.10 +
        coverage_risk * 0.20
    )
    overall_score = max(0, min(100, overall_score))

    if overall_score >= 70:
        risk_level = "High"
    elif overall_score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    if overall_score <= 25:
        risk_grade = "A"
    elif overall_score <= 40:
        risk_grade = "B"
    elif overall_score <= 55:
        risk_grade = "C"
    elif overall_score <= 70:
        risk_grade = "D"
    else:
        risk_grade = "F"

    return risk_factors, overall_score, risk_level, risk_grade


def generate_investment_summary(
    overview: CompanyOverview,
    dividend_metrics: DividendMetrics,
) -> Optional[str]:
    """Generate a human-readable investment summary."""
    summary_parts = []

    if overview.dividend_yield:
        yield_pct = overview.dividend_yield * 100
        if yield_pct > 6:
            summary_parts.append(f"High yield of {yield_pct:.2f}% may signal risk")
        elif yield_pct > 3:
            summary_parts.append(f"Attractive yield of {yield_pct:.2f}%")
        else:
            summary_parts.append(f"Moderate yield of {yield_pct:.2f}%")

    if overview.payout_ratio:
        payout_pct = overview.payout_ratio * 100
        if payout_pct > 90:
            summary_parts.append(f"payout ratio of {payout_pct:.0f}% is unsustainable")
        elif payout_pct > 70:
            summary_parts.append(f"payout ratio of {payout_pct:.0f}% is elevated")
        else:
            summary_parts.append(f"sustainable payout ratio of {payout_pct:.0f}%")

    if dividend_metrics.fcf_coverage_ratio:
        if dividend_metrics.fcf_coverage_ratio >= 2:
            summary_parts.append("strong free cash flow coverage")
        elif dividend_metrics.fcf_coverage_ratio >= 1.2:
            summary_parts.append("adequate FCF coverage")
        else:
            summary_parts.append("weak FCF coverage of dividends")

    if overview.beta:
        if overview.beta > 1.5:
            summary_parts.append(f"high volatility (beta: {overview.beta:.2f})")
        elif overview.beta < 0.8:
            summary_parts.append(f"defensive stock (beta: {overview.beta:.2f})")

    return ". ".join(summary_parts).capitalize() if summary_parts else None


def compute_growth_metrics(
    income: List[IncomeStatement],
    cashflow: List[CashFlow],
    annual_earnings: Optional[List[AnnualEarnings]] = None,
) -> GrowthMetrics:
    """Compute CAGR metrics from historical data."""

    def cagr(start_val: float, end_val: float, years: int) -> Optional[float]:
        if start_val <= 0 or end_val <= 0 or years <= 0:
            return None
        return round(((end_val / start_val) ** (1 / years) - 1) * 100, 2)

    # Revenue CAGR (income sorted newest-first)
    revenues = [s.total_revenue for s in income if s.total_revenue and s.total_revenue > 0]
    rev_cagr_3 = None
    rev_cagr_5 = None
    if len(revenues) >= 4:
        rev_cagr_3 = cagr(revenues[3], revenues[0], 3)
    if len(revenues) >= 5:
        rev_cagr_5 = cagr(revenues[-1], revenues[0], len(revenues) - 1)

    # EPS CAGR from annual earnings
    eps_cagr_3 = None
    eps_cagr_5 = None
    if annual_earnings:
        eps_vals = [e.reported_eps for e in annual_earnings if e.reported_eps and e.reported_eps > 0]
        if len(eps_vals) >= 4:
            eps_cagr_3 = cagr(eps_vals[3], eps_vals[0], 3)
        if len(eps_vals) >= 5:
            eps_cagr_5 = cagr(eps_vals[-1], eps_vals[0], len(eps_vals) - 1)

    # FCF CAGR
    fcfs = [cf.free_cashflow for cf in cashflow if cf.free_cashflow and cf.free_cashflow > 0]
    fcf_cagr_3 = None
    if len(fcfs) >= 4:
        fcf_cagr_3 = cagr(fcfs[3], fcfs[0], 3)

    # Dividend CAGR from cashflow dividend_payout
    div_payouts = [abs(cf.dividend_payout) for cf in cashflow if cf.dividend_payout and cf.dividend_payout != 0]
    div_cagr_3 = None
    div_cagr_5 = None
    if len(div_payouts) >= 4:
        div_cagr_3 = cagr(div_payouts[3], div_payouts[0], 3)
    if len(div_payouts) >= 5:
        div_cagr_5 = cagr(div_payouts[-1], div_payouts[0], len(div_payouts) - 1)

    return GrowthMetrics(
        revenue_cagr_3y=rev_cagr_3,
        revenue_cagr_5y=rev_cagr_5,
        eps_cagr_3y=eps_cagr_3,
        eps_cagr_5y=eps_cagr_5,
        fcf_cagr_3y=fcf_cagr_3,
        dividend_cagr_3y=div_cagr_3,
        dividend_cagr_5y=div_cagr_5,
    )


def compute_analyst_sentiment(overview: CompanyOverview) -> AnalystSentiment:
    """Derive analyst sentiment from overview rating fields."""
    total = (
        (overview.analyst_rating_strong_buy or 0) +
        (overview.analyst_rating_buy or 0) +
        (overview.analyst_rating_hold or 0) +
        (overview.analyst_rating_sell or 0) +
        (overview.analyst_rating_strong_sell or 0)
    )

    consensus = None
    if total > 0:
        buy_pct = ((overview.analyst_rating_strong_buy or 0) + (overview.analyst_rating_buy or 0)) / total
        if buy_pct >= 0.7:
            consensus = "Strong Buy"
        elif buy_pct >= 0.5:
            consensus = "Buy"
        elif buy_pct >= 0.3:
            consensus = "Hold"
        else:
            consensus = "Sell"

    return AnalystSentiment(
        target_price=overview.analyst_target_price,
        strong_buy=overview.analyst_rating_strong_buy,
        buy=overview.analyst_rating_buy,
        hold=overview.analyst_rating_hold,
        sell=overview.analyst_rating_sell,
        strong_sell=overview.analyst_rating_strong_sell,
        total_analysts=total if total > 0 else None,
        consensus=consensus,
    )
