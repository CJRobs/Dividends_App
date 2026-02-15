/**
 * TypeScript interfaces for the Dividend Screener.
 * Matches the backend Pydantic models in backend/app/models/screener.py.
 */

export interface CompanyOverview {
  symbol: string;
  name: string;
  description?: string;
  sector?: string;
  industry?: string;
  exchange?: string;
  currency?: string;
  current_price?: number;
  shares_outstanding?: number;
  market_cap?: number;
  pe_ratio?: number;
  forward_pe?: number;
  trailing_pe?: number;
  peg_ratio?: number;
  dividend_yield?: number;
  dividend_per_share?: number;
  dividend_date?: string;
  eps?: number;
  beta?: number;
  fifty_two_week_high?: number;
  fifty_two_week_low?: number;
  book_value?: number;
  profit_margin?: number;
  operating_margin?: number;
  return_on_equity?: number;
  revenue_ttm?: number;
  gross_profit_ttm?: number;
  ex_dividend_date?: string;
  payout_ratio?: number;
  price_to_sales_ratio?: number;
  price_to_book_ratio?: number;
  ev_to_revenue?: number;
  ev_to_ebitda?: number;
  analyst_target_price?: number;
  analyst_rating_strong_buy?: number;
  analyst_rating_buy?: number;
  analyst_rating_hold?: number;
  analyst_rating_sell?: number;
  analyst_rating_strong_sell?: number;
  quarterly_earnings_growth_yoy?: number;
  quarterly_revenue_growth_yoy?: number;
}

export interface DividendHistory {
  ex_date: string;
  amount: number;
  declaration_date?: string;
  record_date?: string;
  payment_date?: string;
}

export interface IncomeStatement {
  fiscal_date: string;
  total_revenue?: number;
  gross_profit?: number;
  operating_income?: number;
  net_income?: number;
  ebitda?: number;
  cost_of_revenue?: number;
  research_and_development?: number;
  selling_general_admin?: number;
  interest_expense?: number;
  interest_income?: number;
  gross_margin?: number;
  operating_margin?: number;
  net_margin?: number;
  revenue_growth_yoy?: number;
  net_income_growth_yoy?: number;
  eps?: number;
}

export interface BalanceSheet {
  fiscal_date: string;
  total_assets?: number;
  total_liabilities?: number;
  total_equity?: number;
  total_debt?: number;
  cash_and_equivalents?: number;
  current_assets?: number;
  current_liabilities?: number;
  inventory?: number;
  current_ratio?: number;
  quick_ratio?: number;
  debt_to_equity?: number;
}

export interface CashFlow {
  fiscal_date: string;
  operating_cashflow?: number;
  capital_expenditure?: number;
  free_cashflow?: number;
  dividend_payout?: number;
  investing_cashflow?: number;
  financing_cashflow?: number;
  depreciation_amortization?: number;
  fcf_per_share?: number;
  fcf_yield?: number;
  fcf_margin?: number;
}

export interface EarningsData {
  fiscal_date: string;
  reported_eps?: number;
  estimated_eps?: number;
  surprise?: number;
  surprise_percentage?: number;
}

export interface AnnualEarnings {
  fiscal_date: string;
  reported_eps?: number;
}

export interface DividendMetrics {
  dividend_growth_rate?: number;
  fcf_coverage_ratio?: number;
  consecutive_growth_years?: number;
  dividend_consistency?: string;
  avg_dividend_amount?: number;
  total_dividends_paid?: number;
}

export interface RiskFactors {
  yield_risk?: number;
  payout_risk?: number;
  valuation_risk?: number;
  leverage_risk?: number;
  volatility_risk?: number;
  coverage_risk?: number;
}

export interface GrowthMetrics {
  revenue_cagr_3y?: number;
  revenue_cagr_5y?: number;
  eps_cagr_3y?: number;
  eps_cagr_5y?: number;
  fcf_cagr_3y?: number;
  dividend_cagr_3y?: number;
  dividend_cagr_5y?: number;
}

export interface AnalystSentiment {
  target_price?: number;
  strong_buy?: number;
  buy?: number;
  hold?: number;
  sell?: number;
  strong_sell?: number;
  total_analysts?: number;
  consensus?: string;
}

export interface DataFreshnessEntry {
  cached_at?: string;
  expires_at?: string;
  source: string;
}

export interface ScreenerAnalysis {
  overview: CompanyOverview;
  dividends: DividendHistory[];
  income_statements: IncomeStatement[];
  balance_sheets: BalanceSheet[];
  cash_flows: CashFlow[];
  dividend_metrics?: DividendMetrics;
  risk_factors?: RiskFactors;
  risk_score?: number;
  risk_level?: string;
  risk_grade?: string;
  investment_summary?: string;
  quarterly_earnings?: EarningsData[];
  annual_earnings?: AnnualEarnings[];
  growth_metrics?: GrowthMetrics;
  analyst_sentiment?: AnalystSentiment;
  data_freshness?: Record<string, DataFreshnessEntry>;
}
