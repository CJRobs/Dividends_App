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
  colors?: string[] | null;
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
  predicted: number;  // Standardized to match backend ForecastPoint model
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

// Monthly Analysis Types
export interface MonthlyByYearData {
  months: string[];
  years: Record<string, (number | null)[]>;
}

export interface HeatmapCell {
  row: string;
  col: string;
  value: number;
}

export interface HeatmapData {
  rows: string[];
  cols: string[];
  data: HeatmapCell[];
}

export interface CompanyMonthlyData {
  period: string;
  company: string;
  amount: number;
}

export interface MonthlyByCompanyResponse {
  data: CompanyMonthlyData[];
  companies: string[];
  periods: string[];
}

export interface CoverageData {
  month_name: string;
  amount_received: number;
  coverage_percent: number;
  gap_amount: number;
  monthly_average: number;
}

export interface MonthlyAnalysisResponse {
  by_year: MonthlyByYearData;
  heatmap: HeatmapData;
  companies: string[];
  months: string[];
  years: number[];
}

// Stock Analysis Types
export interface PeriodData {
  period: string;
  period_key: string;
  stocks: Record<string, number>;
  total: number;
}

export interface PeriodAnalysisResponse {
  periods: string[];
  stocks: string[];
  data: PeriodData[];
  period_type: string;
}

export interface GrowthDataPoint {
  period: string;
  total: number;
  growth_percent: number | null;
}

export interface GrowthAnalysisResponse {
  data: GrowthDataPoint[];
  average_growth: number | null;
}

export interface ConcentrationData {
  top_1_percent: number;
  top_3_percent: number;
  top_5_percent: number;
  top_10_percent: number;
  top_1_risk: string;
  top_3_risk: string;
  top_5_risk: string;
  top_10_risk: string;
}

export interface StockDistribution {
  name: string;
  total: number;
  percentage: number;
}

export interface StockListItem {
  ticker: string;
  name: string;
  total_dividends: number;
  dividend_count: number;
  average_dividend: number;
  percentage_of_portfolio: number;
  last_dividend_date: string | null;
  last_dividend_amount: number;
}

export interface StockDetailInfo {
  ticker: string;
  name: string;
  isin: string;
  total_dividends: number;
  dividend_count: number;
  average_dividend: number;
  min_dividend: number;
  max_dividend: number;
  first_dividend_date: string | null;
  last_dividend_date: string | null;
  last_dividend_amount: number;
  payment_cadence: string;
  payments_per_year: number;
}

export interface PaymentHistoryItem {
  date: string;
  amount: number;
  shares: number;
}

export interface YearlyTotal {
  year: number;
  total: number;
}

export interface MonthlyGrowthItem {
  month: string;
  total: number;
  percent_change: number | null;
}

export interface StockAnalysisDetailResponse {
  detail: StockDetailInfo;
  yearly_totals: YearlyTotal[];
  payment_history: PaymentHistoryItem[];
  monthly_growth: MonthlyGrowthItem[];
}

export interface StockOverviewResponse {
  stocks: StockListItem[];
  distribution: StockDistribution[];
  concentration: ConcentrationData;
  total_stocks: number;
  total_dividends: number;
}

// Additional types to match backend models

export interface AnnualStats {
  year: number;
  total: number;
  count: number;
  average: number;
  unique_stocks: number;
  growth: number | null;
}

export interface DividendStreakInfo {
  current_streak: number;
  longest_streak: number;
  months_with_dividends: number;
  total_months_span: number;
}

export interface FICalculatorResponse {
  monthly_goal: number;
  current_monthly_avg: number;
  annual_growth_rate: number;
  years_to_goal: number | null;
  goal_reached: boolean;
}

export interface ForecastResult {
  model_name: string;
  forecast: ForecastDataPoint[];
  historical: Array<{ date: string; value: number }>;
  metrics: Record<string, unknown>;
  total_projected: number;
  monthly_average: number;
  annual_projections: Array<{ year: string; projected: number }>;
}

export interface AllForecastsResponse {
  sarimax: ForecastResult | null;
  holt_winters: ForecastResult | null;
  prophet: ForecastResult | null;
  theta: ForecastResult | null;
  simple_average: ForecastResult | null;
  ensemble: ForecastResult | null;
  available_models: string[];
  current_month_tracking: {
    date: string;
    value: number;
    is_partial: boolean;
  } | null;
}

// Calendar Types
export interface DividendEvent {
  date: string;
  ticker: string;
  company_name: string;
  amount: number;
  expected: boolean;
}

export interface CalendarMonth {
  year: number;
  month: number;
  events: DividendEvent[];
  total: number;
}

export interface UpcomingDividend {
  ticker: string;
  company_name: string;
  expected_date: string;
  estimated_amount: number;
  confidence: 'low' | 'medium' | 'high';
}

export interface UpcomingDividendLive {
  ticker: string;
  company_name: string;
  ex_date: string;
  amount?: number;
  payment_date?: string;
  record_date?: string;
  declaration_date?: string;
  source: string;
}
