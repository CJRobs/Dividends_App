"""
yfinance provider implementation (final fallback).

Priority 3. No API key required. Synchronous library wrapped
in asyncio.to_thread for async compatibility.
"""

import asyncio
from typing import Optional, List, Dict
from datetime import datetime

from app.utils.logging_config import get_logger
from app.models.screener import (
    CompanyOverview, DividendHistory, IncomeStatement,
    BalanceSheet, CashFlow, EarningsData, AnnualEarnings,
    safe_float,
)
from .base import BaseProvider, ProviderResult, ProviderStatus

logger = get_logger()


def _safe_df_val(df, row_name: str, col, default=None):
    """Safely extract a value from a pandas DataFrame."""
    try:
        if row_name in df.index:
            val = df.loc[row_name, col]
            import pandas as pd
            if pd.isna(val):
                return default
            return float(val)
    except Exception:
        pass
    return default


class YFinanceProvider(BaseProvider):
    name = "yfinance"
    priority = 3

    def __init__(self, settings):
        super().__init__(settings)
        self._daily_limit = None  # No formal limit

    def _get_ticker(self, symbol: str):
        import yfinance as yf
        return yf.Ticker(symbol.upper())

    @staticmethod
    def _format_timestamp(val) -> Optional[str]:
        """Convert a Unix timestamp or other value to a date string."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return datetime.fromtimestamp(val).strftime("%Y-%m-%d")
        return str(val)

    async def fetch_overview(self, symbol, client, **kwargs):
        try:
            def _sync():
                ticker = self._get_ticker(symbol)
                info = ticker.info
                if not info or not info.get("shortName"):
                    return None
                return CompanyOverview(
                    symbol=symbol.upper(),
                    name=info.get("shortName", info.get("longName", "Unknown")),
                    description=info.get("longBusinessSummary"),
                    sector=info.get("sector"),
                    industry=info.get("industry"),
                    exchange=info.get("exchange"),
                    currency=info.get("currency"),
                    current_price=safe_float(info.get("currentPrice")),
                    shares_outstanding=safe_float(info.get("sharesOutstanding")),
                    market_cap=safe_float(info.get("marketCap")),
                    pe_ratio=safe_float(info.get("trailingPE")),
                    forward_pe=safe_float(info.get("forwardPE")),
                    trailing_pe=safe_float(info.get("trailingPE")),
                    peg_ratio=safe_float(info.get("pegRatio")),
                    dividend_yield=safe_float(info.get("dividendYield")),
                    dividend_per_share=safe_float(info.get("dividendRate")),
                    eps=safe_float(info.get("trailingEps")),
                    beta=safe_float(info.get("beta")),
                    fifty_two_week_high=safe_float(info.get("fiftyTwoWeekHigh")),
                    fifty_two_week_low=safe_float(info.get("fiftyTwoWeekLow")),
                    book_value=safe_float(info.get("bookValue")),
                    profit_margin=safe_float(info.get("profitMargins")),
                    operating_margin=safe_float(info.get("operatingMargins")),
                    return_on_equity=safe_float(info.get("returnOnEquity")),
                    revenue_ttm=safe_float(info.get("totalRevenue")),
                    gross_profit_ttm=safe_float(info.get("grossProfits")),
                    payout_ratio=safe_float(info.get("payoutRatio")),
                    analyst_target_price=safe_float(info.get("targetMeanPrice")),
                    ex_dividend_date=self._format_timestamp(info.get("exDividendDate")),
                    price_to_book_ratio=safe_float(info.get("priceToBook")),
                )

            result = await asyncio.to_thread(_sync)
            if result is None:
                return ProviderResult(status=ProviderStatus.NO_DATA)
            return ProviderResult(status=ProviderStatus.SUCCESS, data=result)
        except Exception as e:
            logger.error(f"yfinance overview error for {symbol}: {e}")
            return ProviderResult(status=ProviderStatus.PROVIDER_ERROR, error_message=str(e))

    async def fetch_dividends(self, symbol, client, **kwargs):
        try:
            def _sync():
                ticker = self._get_ticker(symbol)
                divs = ticker.dividends
                if divs is None or divs.empty:
                    return []
                result = []
                for date, amount in divs.items():
                    result.append(DividendHistory(
                        ex_date=date.strftime("%Y-%m-%d"),
                        amount=float(amount),
                    ))
                result.sort(key=lambda x: x.ex_date, reverse=True)
                return result[:20]

            result = await asyncio.to_thread(_sync)
            return ProviderResult(status=ProviderStatus.SUCCESS, data=result)
        except Exception as e:
            logger.error(f"yfinance dividends error for {symbol}: {e}")
            return ProviderResult(status=ProviderStatus.PROVIDER_ERROR, error_message=str(e))

    async def fetch_income(self, symbol, client, **kwargs):
        try:
            shares = kwargs.get("shares_outstanding")
            period = kwargs.get("period", "annual")

            def _sync():
                ticker = self._get_ticker(symbol)
                df = ticker.quarterly_income_stmt if period == "quarterly" else ticker.income_stmt
                if df is None or df.empty:
                    return []

                limit = 8 if period == "quarterly" else 5
                statements = []
                cols = list(df.columns)[:limit]
                for i, col in enumerate(cols):
                    total_revenue = _safe_df_val(df, "Total Revenue", col)
                    gross_profit = _safe_df_val(df, "Gross Profit", col)
                    operating_income = _safe_df_val(df, "Operating Income", col)
                    net_income = _safe_df_val(df, "Net Income", col)

                    gross_margin = op_margin = net_margin_val = None
                    if total_revenue and total_revenue > 0:
                        if gross_profit is not None:
                            gross_margin = round(gross_profit / total_revenue * 100, 2)
                        if operating_income is not None:
                            op_margin = round(operating_income / total_revenue * 100, 2)
                        if net_income is not None:
                            net_margin_val = round(net_income / total_revenue * 100, 2)

                    revenue_growth = ni_growth = None
                    if i < len(cols) - 1:
                        prev_rev = _safe_df_val(df, "Total Revenue", cols[i + 1])
                        prev_ni = _safe_df_val(df, "Net Income", cols[i + 1])
                        if prev_rev and prev_rev != 0 and total_revenue:
                            revenue_growth = round(((total_revenue - prev_rev) / abs(prev_rev)) * 100, 2)
                        if prev_ni and prev_ni != 0 and net_income:
                            ni_growth = round(((net_income - prev_ni) / abs(prev_ni)) * 100, 2)

                    eps_val = None
                    if net_income is not None and shares and shares > 0:
                        eps_val = round(net_income / shares, 2)

                    fiscal_date = col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)

                    statements.append(IncomeStatement(
                        fiscal_date=fiscal_date,
                        total_revenue=total_revenue,
                        gross_profit=gross_profit,
                        operating_income=operating_income,
                        net_income=net_income,
                        ebitda=_safe_df_val(df, "EBITDA", col),
                        cost_of_revenue=_safe_df_val(df, "Cost Of Revenue", col),
                        research_and_development=_safe_df_val(df, "Research And Development", col),
                        selling_general_admin=_safe_df_val(df, "Selling General And Administration", col),
                        interest_expense=_safe_df_val(df, "Interest Expense", col),
                        interest_income=_safe_df_val(df, "Interest Income", col),
                        gross_margin=gross_margin,
                        operating_margin=op_margin,
                        net_margin=net_margin_val,
                        revenue_growth_yoy=revenue_growth,
                        net_income_growth_yoy=ni_growth,
                        eps=eps_val,
                    ))
                return statements

            result = await asyncio.to_thread(_sync)
            return ProviderResult(status=ProviderStatus.SUCCESS, data=result)
        except Exception as e:
            logger.error(f"yfinance income error for {symbol}: {e}")
            return ProviderResult(status=ProviderStatus.PROVIDER_ERROR, error_message=str(e))

    async def fetch_balance(self, symbol, client, **kwargs):
        try:
            period = kwargs.get("period", "annual")

            def _sync():
                ticker = self._get_ticker(symbol)
                df = ticker.quarterly_balance_sheet if period == "quarterly" else ticker.balance_sheet
                if df is None or df.empty:
                    return []

                limit = 8 if period == "quarterly" else 5
                sheets = []
                for col in list(df.columns)[:limit]:
                    total_assets = _safe_df_val(df, "Total Assets", col)
                    total_liabilities = _safe_df_val(df, "Total Liabilities Net Minority Interest", col)
                    total_equity = _safe_df_val(df, "Stockholders Equity", col)
                    total_debt = _safe_df_val(df, "Long Term Debt", col)
                    current_assets = _safe_df_val(df, "Current Assets", col)
                    current_liabilities = _safe_df_val(df, "Current Liabilities", col)
                    inventory = _safe_df_val(df, "Inventory", col)

                    current_ratio = quick_ratio = debt_to_equity = None
                    if current_assets and current_liabilities and current_liabilities > 0:
                        current_ratio = round(current_assets / current_liabilities, 2)
                        inv = inventory if inventory else 0
                        quick_ratio = round((current_assets - inv) / current_liabilities, 2)
                    if total_debt and total_equity and total_equity > 0:
                        debt_to_equity = round(total_debt / total_equity, 2)

                    fiscal_date = col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)

                    sheets.append(BalanceSheet(
                        fiscal_date=fiscal_date,
                        total_assets=total_assets,
                        total_liabilities=total_liabilities,
                        total_equity=total_equity,
                        total_debt=total_debt,
                        cash_and_equivalents=_safe_df_val(df, "Cash And Cash Equivalents", col),
                        current_assets=current_assets,
                        current_liabilities=current_liabilities,
                        inventory=inventory,
                        current_ratio=current_ratio,
                        quick_ratio=quick_ratio,
                        debt_to_equity=debt_to_equity,
                    ))
                return sheets

            result = await asyncio.to_thread(_sync)
            return ProviderResult(status=ProviderStatus.SUCCESS, data=result)
        except Exception as e:
            logger.error(f"yfinance balance error for {symbol}: {e}")
            return ProviderResult(status=ProviderStatus.PROVIDER_ERROR, error_message=str(e))

    async def fetch_cashflow(self, symbol, client, **kwargs):
        try:
            shares = kwargs.get("shares_outstanding")
            price = kwargs.get("current_price")
            revenue_by_year = kwargs.get("revenue_by_year")
            period = kwargs.get("period", "annual")

            def _sync():
                ticker = self._get_ticker(symbol)
                df = ticker.quarterly_cashflow if period == "quarterly" else ticker.cashflow
                if df is None or df.empty:
                    return []

                limit = 8 if period == "quarterly" else 5
                flows = []
                for col in list(df.columns)[:limit]:
                    operating = _safe_df_val(df, "Operating Cash Flow", col)
                    capex = _safe_df_val(df, "Capital Expenditure", col)
                    fcf = _safe_df_val(df, "Free Cash Flow", col)
                    if fcf is None and operating is not None and capex is not None:
                        fcf = operating - abs(capex)

                    dividend_payout = _safe_df_val(df, "Cash Dividends Paid", col)
                    if dividend_payout and dividend_payout < 0:
                        dividend_payout = abs(dividend_payout)

                    fcf_per_share = fcf_yield_val = fcf_margin_val = None
                    if fcf is not None and shares and shares > 0:
                        fcf_per_share = round(fcf / shares, 2)
                        if price and price > 0:
                            fcf_yield_val = round(fcf_per_share / price * 100, 2)

                    fiscal_date = col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)
                    fiscal_year = fiscal_date[:4]
                    if fcf is not None and revenue_by_year:
                        revenue = revenue_by_year.get(fiscal_year)
                        if revenue and revenue > 0:
                            fcf_margin_val = round(fcf / revenue * 100, 2)

                    flows.append(CashFlow(
                        fiscal_date=fiscal_date,
                        operating_cashflow=operating,
                        capital_expenditure=capex,
                        free_cashflow=fcf,
                        dividend_payout=dividend_payout,
                        investing_cashflow=_safe_df_val(df, "Investing Cash Flow", col),
                        financing_cashflow=_safe_df_val(df, "Financing Cash Flow", col),
                        depreciation_amortization=_safe_df_val(df, "Depreciation And Amortization", col),
                        fcf_per_share=fcf_per_share,
                        fcf_yield=fcf_yield_val,
                        fcf_margin=fcf_margin_val,
                    ))
                return flows

            result = await asyncio.to_thread(_sync)
            return ProviderResult(status=ProviderStatus.SUCCESS, data=result)
        except Exception as e:
            logger.error(f"yfinance cashflow error for {symbol}: {e}")
            return ProviderResult(status=ProviderStatus.PROVIDER_ERROR, error_message=str(e))

    async def fetch_earnings(self, symbol, client, **kwargs):
        try:
            def _sync():
                ticker = self._get_ticker(symbol)
                quarterly = []
                annual = []

                # Quarterly earnings
                try:
                    qe = ticker.quarterly_earnings
                    if qe is not None and not qe.empty:
                        for idx in qe.index:
                            reported = safe_float(qe.loc[idx, "Earnings"]) if "Earnings" in qe.columns else None
                            revenue = safe_float(qe.loc[idx, "Revenue"]) if "Revenue" in qe.columns else None
                            date_str = str(idx)
                            quarterly.append(EarningsData(
                                fiscal_date=date_str,
                                reported_eps=reported,
                            ))
                except Exception:
                    pass

                # Annual earnings
                try:
                    ae = ticker.earnings
                    if ae is not None and not ae.empty:
                        for idx in ae.index:
                            eps = safe_float(ae.loc[idx, "Earnings"]) if "Earnings" in ae.columns else None
                            annual.append(AnnualEarnings(
                                fiscal_date=f"{idx}-12-31" if isinstance(idx, (int, float)) else str(idx),
                                reported_eps=eps,
                            ))
                        annual.sort(key=lambda x: x.fiscal_date, reverse=True)
                except Exception:
                    pass

                return quarterly, annual

            quarterly, annual = await asyncio.to_thread(_sync)
            return ProviderResult(status=ProviderStatus.SUCCESS, data=(quarterly, annual))
        except Exception as e:
            logger.error(f"yfinance earnings error for {symbol}: {e}")
            return ProviderResult(status=ProviderStatus.PROVIDER_ERROR, error_message=str(e))
