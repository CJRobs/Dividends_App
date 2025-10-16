/**
 * TypeScript types for the Dividend Portfolio Dashboard.
 * These match the Pydantic models from the backend.
 */

export interface DividendRecord {
  action: string;
  time: string;
  isin: string;
  ticker: string;
  name: string;
  no_of_shares: number;
  price_per_share: number;
  currency_price: string;
  exchange_rate?: string;
  total: number;
  currency_total: string;
  withholding_tax: number;
  currency_tax: string;
}

export interface MonthlyData {
  year: number;
  month: number;
  month_name: string;
  total: number;
  count: number;
  stocks: string[];
}

export interface YearlyData {
  year: number;
  total: number;
  count: number;
  average_per_month: number;
  monthly_breakdown: MonthlyData[];
}

export interface PortfolioSummary {
  total_dividends: number;
  total_dividends_ytd: number;
  total_count: number;
  unique_stocks: number;
  average_dividend: number;
  highest_dividend: number;
  lowest_dividend: number;
  first_dividend_date?: string;
  last_dividend_date?: string;
  ytd_vs_last_year_change?: number;
  ytd_vs_last_year_percent?: number;
}

export interface StockSummary {
  ticker: string;
  name: string;
  isin: string;
  total_dividends: number;
  dividend_count: number;
  average_dividend: number;
  last_dividend_date?: string;
  last_dividend_amount: number;
  percentage_of_portfolio: number;
}

export interface RecentDividend {
  ticker: string;
  name: string;
  amount: number;
  date: string;
  shares: number;
}

export interface ChartData {
  labels: string[];
  values: number[];
  colors?: string[];
}

export interface TimeSeriesData {
  dates: string[];
  values: number[];
  label: string;
}

export interface OverviewResponse {
  summary: PortfolioSummary;
  ytd_chart: TimeSeriesData;
  monthly_chart: ChartData;
  top_stocks: StockSummary[];
  recent_dividends: RecentDividend[];
}

export interface StockInfo {
  ticker: string;
  name: string;
  isin: string;
  total_dividends: number;
  dividend_count: number;
  average_dividend: number;
  min_dividend: number;
  max_dividend: number;
  first_dividend_date?: string;
  last_dividend_date?: string;
  dividend_frequency?: string;
  yield_estimate?: number;
}

export interface MonthlyComparison {
  period: string;
  current_value: number;
  previous_value?: number;
  change?: number;
  change_percent?: number;
}

export type ScreenerFilterOperator = "gt" | "lt" | "eq" | "gte" | "lte" | "between";

export interface ScreenerFilter {
  field: string;
  operator: ScreenerFilterOperator;
  value: number;
  value2?: number;
}

export interface ScreenerCriteria {
  filters: ScreenerFilter[];
  sort_by?: string;
  sort_order: "asc" | "desc";
  limit?: number;
}

export interface ScreenerResult {
  stocks: StockInfo[];
  total_count: number;
  criteria: ScreenerCriteria;
}

export type ForecastMethod = "linear" | "moving_average" | "exponential" | "prophet";
export type ForecastScenario = "conservative" | "moderate" | "optimistic";

export interface ForecastRequest {
  months: number;
  method: ForecastMethod;
  scenario?: ForecastScenario;
  include_confidence_interval: boolean;
}

export interface ForecastDataPoint {
  date: string;
  value: number;
  lower_bound?: number;
  upper_bound?: number;
}

export interface ForecastResponse {
  historical: ForecastDataPoint[];
  forecast: ForecastDataPoint[];
  total_forecast: number;
  method: ForecastMethod;
  scenario?: ForecastScenario;
  confidence_level?: number;
}

export type ReportTemplate = "summary" | "detailed" | "monthly" | "stock_analysis" | "yearly";

export interface ReportRequest {
  template: ReportTemplate;
  year?: number;
  month?: number;
  ticker?: string;
  include_charts: boolean;
  include_tables: boolean;
}

export interface ReportResponse {
  report_id: string;
  filename: string;
  download_url: string;
  created_at: string;
}
