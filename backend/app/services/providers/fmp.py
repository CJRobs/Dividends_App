"""
Financial Modeling Prep (FMP) provider implementation.

Secondary provider (priority 1). Uses FMP's stable API endpoints.
Rate limit: 250 calls/day on free tier.
"""

import httpx
from typing import Optional, List, Dict, Any

from app.utils.logging_config import get_logger
from app.models.screener import (
    CompanyOverview, DividendHistory, IncomeStatement,
    BalanceSheet, CashFlow, EarningsData, AnnualEarnings,
    safe_float,
)
from .base import BaseProvider, ProviderResult, ProviderStatus

logger = get_logger()


class FMPProvider(BaseProvider):
    name = "fmp"
    priority = 1

    def __init__(self, settings):
        super().__init__(settings)
        self._daily_limit = 250
        self._api_key = settings.fmp_api_key
        self._base_url = getattr(settings, 'fmp_base_url', 'https://financialmodelingprep.com/stable')

    async def _fetch_fmp(
        self, endpoint: str, symbol: str, client: Optional[httpx.AsyncClient],
        extra_params: Optional[dict] = None,
    ) -> tuple[Optional[Any], ProviderStatus]:
        """Common FMP fetch with auth and error detection."""
        if not self.is_endpoint_available(endpoint):
            logger.debug(f"FMP endpoint '{endpoint}' is blocked (premium)")
            return None, ProviderStatus.PROVIDER_ERROR

        self.record_call()
        url = f"{self._base_url}/{endpoint}"
        params = {"symbol": symbol.upper(), "apikey": self._api_key}
        if extra_params:
            params.update(extra_params)

        try:
            if client:
                response = await client.get(url, params=params)
            else:
                async with httpx.AsyncClient(timeout=30.0) as c:
                    response = await c.get(url, params=params)

            if response.status_code == 429:
                logger.warning("FMP rate limit hit")
                self.mark_exhausted(cooldown_minutes=60)
                return None, ProviderStatus.RATE_LIMITED

            if response.status_code == 402:
                logger.warning(f"FMP endpoint '{endpoint}' requires premium (402)")
                self.mark_endpoint_blocked(endpoint, cooldown_minutes=1440)
                return None, ProviderStatus.PROVIDER_ERROR

            if response.status_code == 403:
                logger.warning("FMP authentication failed")
                self.mark_exhausted(cooldown_minutes=1440)
                return None, ProviderStatus.PROVIDER_ERROR

            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and "Error Message" in data:
                return None, ProviderStatus.NO_DATA

            if isinstance(data, list) and len(data) == 0:
                return None, ProviderStatus.NO_DATA

            return data, ProviderStatus.SUCCESS

        except httpx.HTTPError as e:
            logger.error(f"FMP HTTP error for {endpoint}/{symbol}: {e}")
            return None, ProviderStatus.PROVIDER_ERROR
        except Exception as e:
            logger.error(f"FMP fetch error for {endpoint}/{symbol}: {e}")
            return None, ProviderStatus.PROVIDER_ERROR

    # -----------------------------------------------------------------------
    # Fetch + map methods
    # -----------------------------------------------------------------------

    async def fetch_overview(self, symbol, client, **kwargs):
        data, status = await self._fetch_fmp("profile", symbol, client)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        return ProviderResult(status=ProviderStatus.SUCCESS, data=self._map_profile(data))

    async def fetch_dividends(self, symbol, client, **kwargs):
        data, status = await self._fetch_fmp("dividends", symbol, client)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        return ProviderResult(status=ProviderStatus.SUCCESS, data=self._map_dividends(data))

    async def fetch_income(self, symbol, client, **kwargs):
        period = kwargs.get("period", "annual")
        extra = {"period": "quarter"} if period == "quarterly" else {}
        data, status = await self._fetch_fmp("income-statement", symbol, client, extra_params=extra)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        shares = kwargs.get("shares_outstanding")
        limit = 8 if period == "quarterly" else 5
        return ProviderResult(status=ProviderStatus.SUCCESS, data=self._map_income(data, shares, limit=limit))

    async def fetch_balance(self, symbol, client, **kwargs):
        period = kwargs.get("period", "annual")
        extra = {"period": "quarter"} if period == "quarterly" else {}
        data, status = await self._fetch_fmp("balance-sheet-statement", symbol, client, extra_params=extra)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        limit = 8 if period == "quarterly" else 5
        return ProviderResult(status=ProviderStatus.SUCCESS, data=self._map_balance(data, limit=limit))

    async def fetch_cashflow(self, symbol, client, **kwargs):
        period = kwargs.get("period", "annual")
        extra = {"period": "quarter"} if period == "quarterly" else {}
        data, status = await self._fetch_fmp("cash-flow-statement", symbol, client, extra_params=extra)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        shares = kwargs.get("shares_outstanding")
        price = kwargs.get("current_price")
        revenue_by_year = kwargs.get("revenue_by_year")
        limit = 8 if period == "quarterly" else 5
        return ProviderResult(
            status=ProviderStatus.SUCCESS,
            data=self._map_cashflow(data, shares, price, revenue_by_year, limit=limit),
        )

    async def fetch_earnings(self, symbol, client, **kwargs):
        data, status = await self._fetch_fmp("earnings", symbol, client)
        if status != ProviderStatus.SUCCESS:
            return ProviderResult(status=status)
        quarterly, annual = self._map_earnings(data)
        return ProviderResult(status=ProviderStatus.SUCCESS, data=(quarterly, annual))

    # -----------------------------------------------------------------------
    # Mapping functions: FMP JSON -> Pydantic models
    # -----------------------------------------------------------------------

    def _map_profile(self, data: list) -> CompanyOverview:
        p = data[0] if isinstance(data, list) and data else data
        if not p:
            return CompanyOverview(symbol="", name="Unknown")

        low, high = None, None
        range_str = p.get("range", "")
        if range_str and "-" in range_str:
            parts = range_str.split("-")
            if len(parts) == 2:
                low = safe_float(parts[0].strip())
                high = safe_float(parts[1].strip())

        mkt_cap = safe_float(p.get("mktCap"))
        price = safe_float(p.get("price"))
        shares = None
        if mkt_cap and price and price > 0:
            shares = mkt_cap / price

        return CompanyOverview(
            symbol=p.get("symbol", ""),
            name=p.get("companyName", "Unknown"),
            description=p.get("description"),
            sector=p.get("sector"),
            industry=p.get("industry"),
            exchange=p.get("exchange"),
            currency=p.get("currency"),
            current_price=price,
            shares_outstanding=shares,
            market_cap=mkt_cap,
            beta=safe_float(p.get("beta")),
            dividend_per_share=safe_float(p.get("lastDividend")),
            fifty_two_week_high=high,
            fifty_two_week_low=low,
        )

    def _map_dividends(self, data: list) -> List[DividendHistory]:
        if not data or not isinstance(data, list):
            return []
        dividends = []
        for item in data[:20]:
            amount = safe_float(item.get("dividend"))
            if amount and amount > 0:
                dividends.append(DividendHistory(
                    ex_date=item.get("date", ""),
                    amount=amount,
                    declaration_date=item.get("declarationDate"),
                    record_date=item.get("recordDate"),
                    payment_date=item.get("paymentDate"),
                ))
        return dividends

    def _map_income(self, data: list, shares_outstanding: Optional[float] = None, limit: int = 5) -> List[IncomeStatement]:
        if not data or not isinstance(data, list):
            return []
        statements = []
        items = data[:limit]
        for i, item in enumerate(items):
            total_revenue = safe_float(item.get("revenue"))
            gross_profit = safe_float(item.get("grossProfit"))
            operating_income = safe_float(item.get("operatingIncome"))
            net_income = safe_float(item.get("netIncome"))

            gross_margin = op_margin = net_margin_val = None
            if total_revenue and total_revenue > 0:
                if gross_profit is not None:
                    gross_margin = round(gross_profit / total_revenue * 100, 2)
                if operating_income is not None:
                    op_margin = round(operating_income / total_revenue * 100, 2)
                if net_income is not None:
                    net_margin_val = round(net_income / total_revenue * 100, 2)

            revenue_growth = ni_growth = None
            if i < len(items) - 1:
                prev = items[i + 1]
                prev_rev = safe_float(prev.get("revenue"))
                prev_ni = safe_float(prev.get("netIncome"))
                if prev_rev and prev_rev != 0 and total_revenue:
                    revenue_growth = round(((total_revenue - prev_rev) / abs(prev_rev)) * 100, 2)
                if prev_ni and prev_ni != 0 and net_income:
                    ni_growth = round(((net_income - prev_ni) / abs(prev_ni)) * 100, 2)

            eps_val = safe_float(item.get("epsDiluted"))
            if eps_val is None and net_income is not None and shares_outstanding and shares_outstanding > 0:
                eps_val = round(net_income / shares_outstanding, 2)

            statements.append(IncomeStatement(
                fiscal_date=item.get("date", ""),
                total_revenue=total_revenue,
                gross_profit=gross_profit,
                operating_income=operating_income,
                net_income=net_income,
                ebitda=safe_float(item.get("ebitda")),
                cost_of_revenue=safe_float(item.get("costOfRevenue")),
                research_and_development=safe_float(item.get("researchAndDevelopmentExpenses")),
                selling_general_admin=safe_float(item.get("sellingGeneralAndAdministrativeExpenses")),
                interest_expense=safe_float(item.get("interestExpense")),
                interest_income=safe_float(item.get("interestIncome")),
                gross_margin=gross_margin,
                operating_margin=op_margin,
                net_margin=net_margin_val,
                revenue_growth_yoy=revenue_growth,
                net_income_growth_yoy=ni_growth,
                eps=eps_val,
            ))
        return statements

    def _map_balance(self, data: list, limit: int = 5) -> List[BalanceSheet]:
        if not data or not isinstance(data, list):
            return []
        sheets = []
        for item in data[:limit]:
            total_assets = safe_float(item.get("totalAssets"))
            total_liabilities = safe_float(item.get("totalLiabilities"))
            total_equity = safe_float(item.get("totalStockholdersEquity"))
            total_debt = safe_float(item.get("totalDebt"))
            current_assets = safe_float(item.get("totalCurrentAssets"))
            current_liabilities = safe_float(item.get("totalCurrentLiabilities"))
            inventory = safe_float(item.get("inventory"))

            current_ratio = quick_ratio = debt_to_equity = None
            if current_assets and current_liabilities and current_liabilities > 0:
                current_ratio = round(current_assets / current_liabilities, 2)
                inv = inventory if inventory else 0
                quick_ratio = round((current_assets - inv) / current_liabilities, 2)
            if total_debt and total_equity and total_equity > 0:
                debt_to_equity = round(total_debt / total_equity, 2)

            sheets.append(BalanceSheet(
                fiscal_date=item.get("date", ""),
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                total_equity=total_equity,
                total_debt=total_debt,
                cash_and_equivalents=safe_float(item.get("cashAndCashEquivalents")),
                current_assets=current_assets,
                current_liabilities=current_liabilities,
                inventory=inventory,
                current_ratio=current_ratio,
                quick_ratio=quick_ratio,
                debt_to_equity=debt_to_equity,
            ))
        return sheets

    def _map_cashflow(
        self, data: list,
        shares: Optional[float] = None,
        price: Optional[float] = None,
        revenue_by_year: Optional[Dict[str, float]] = None,
        limit: int = 5,
    ) -> List[CashFlow]:
        if not data or not isinstance(data, list):
            return []
        flows = []
        for item in data[:limit]:
            operating = safe_float(item.get("operatingCashFlow"))
            capex = safe_float(item.get("capitalExpenditure"))
            fcf = safe_float(item.get("freeCashFlow"))
            if fcf is None and operating is not None and capex is not None:
                fcf = operating - abs(capex)

            dividend_payout = safe_float(item.get("commonDividendsPaid"))
            if dividend_payout and dividend_payout < 0:
                dividend_payout = abs(dividend_payout)

            fcf_per_share = fcf_yield_val = fcf_margin_val = None
            if fcf is not None and shares and shares > 0:
                fcf_per_share = round(fcf / shares, 2)
                if price and price > 0:
                    fcf_yield_val = round(fcf_per_share / price * 100, 2)

            fiscal_year = item.get("date", "")[:4]
            if fcf is not None and revenue_by_year:
                revenue = revenue_by_year.get(fiscal_year)
                if revenue and revenue > 0:
                    fcf_margin_val = round(fcf / revenue * 100, 2)

            flows.append(CashFlow(
                fiscal_date=item.get("date", ""),
                operating_cashflow=operating,
                capital_expenditure=capex,
                free_cashflow=fcf,
                dividend_payout=dividend_payout,
                investing_cashflow=safe_float(item.get("netCashProvidedByInvestingActivities")),
                financing_cashflow=safe_float(item.get("netCashProvidedByFinancingActivities")),
                depreciation_amortization=safe_float(item.get("depreciationAndAmortization")),
                fcf_per_share=fcf_per_share,
                fcf_yield=fcf_yield_val,
                fcf_margin=fcf_margin_val,
            ))
        return flows

    def _map_earnings(self, data: list) -> tuple[List[EarningsData], List[AnnualEarnings]]:
        if not data or not isinstance(data, list):
            return [], []

        quarterly = []
        annual_map: Dict[str, float] = {}

        for item in data[:12]:
            reported = safe_float(item.get("actualEarningResult"))
            estimated = safe_float(item.get("estimatedEarning"))
            surprise = None
            surprise_pct = None
            if reported is not None and estimated is not None:
                surprise = round(reported - estimated, 4)
                if estimated != 0:
                    surprise_pct = round(surprise / abs(estimated) * 100, 2)

            fiscal_date = item.get("fiscalDateEnding") or item.get("date", "")
            quarterly.append(EarningsData(
                fiscal_date=fiscal_date,
                reported_eps=reported,
                estimated_eps=estimated,
                surprise=surprise,
                surprise_percentage=surprise_pct,
            ))

            year = fiscal_date[:4]
            if reported is not None and year:
                annual_map[year] = annual_map.get(year, 0) + reported

        annual = [
            AnnualEarnings(fiscal_date=f"{year}-12-31", reported_eps=round(eps, 2))
            for year, eps in sorted(annual_map.items(), reverse=True)
        ][:5]

        return quarterly, annual
