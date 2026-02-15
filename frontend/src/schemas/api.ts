/**
 * Zod schemas for API response validation.
 *
 * Provides runtime type safety by validating API responses match expected types.
 */

import { z } from 'zod';

// ============================================================================
// Overview & Portfolio Schemas
// ============================================================================

export const PortfolioSummarySchema = z.object({
  total_dividends: z.number(),
  total_dividends_ytd: z.number(),
  total_count: z.number(),
  unique_stocks: z.number(),
  average_dividend: z.number(),
  highest_dividend: z.number(),
  lowest_dividend: z.number(),
  first_dividend_date: z.string().optional(),
  last_dividend_date: z.string().optional(),
  ytd_vs_last_year_change: z.number().optional(),
  ytd_vs_last_year_percent: z.number().optional(),
});

export const TimeSeriesDataSchema = z.object({
  dates: z.array(z.string()),
  values: z.array(z.number()),
  label: z.string(),
});

export const ChartDataSchema = z.object({
  labels: z.array(z.string()),
  values: z.array(z.number()),
  colors: z.array(z.string()).nullable(),
});

export const StockSummarySchema = z.object({
  ticker: z.string(),
  name: z.string(),
  isin: z.string(),
  total_dividends: z.number(),
  dividend_count: z.number(),
  average_dividend: z.number(),
  last_dividend_date: z.string().optional(),
  last_dividend_amount: z.number(),
  percentage_of_portfolio: z.number(),
});

export const RecentDividendSchema = z.object({
  ticker: z.string(),
  name: z.string(),
  amount: z.number(),
  date: z.string(),
  shares: z.number(),
});

export const OverviewResponseSchema = z.object({
  summary: PortfolioSummarySchema,
  ytd_chart: TimeSeriesDataSchema,
  monthly_chart: ChartDataSchema,
  top_stocks: z.array(StockSummarySchema),
  recent_dividends: z.array(RecentDividendSchema),
});

export type OverviewResponse = z.infer<typeof OverviewResponseSchema>;

// ============================================================================
// Stock Schemas
// ============================================================================

export const StockListItemSchema = z.object({
  ticker: z.string(),
  name: z.string(),
  total_dividends: z.number(),
  dividend_count: z.number(),
  average_dividend: z.number(),
  percentage_of_portfolio: z.number(),
  last_dividend_date: z.string().nullable(),
  last_dividend_amount: z.number(),
});

export const StockDistributionSchema = z.object({
  name: z.string(),
  total: z.number(),
  percentage: z.number(),
});

export const ConcentrationDataSchema = z.object({
  top_1_percent: z.number(),
  top_3_percent: z.number(),
  top_5_percent: z.number(),
  top_10_percent: z.number(),
  top_1_risk: z.string(),
  top_3_risk: z.string(),
  top_5_risk: z.string(),
  top_10_risk: z.string(),
});

export const StockOverviewResponseSchema = z.object({
  stocks: z.array(StockListItemSchema),
  distribution: z.array(StockDistributionSchema),
  concentration: ConcentrationDataSchema,
  total_stocks: z.number(),
  total_dividends: z.number(),
});

export type StockOverviewResponse = z.infer<typeof StockOverviewResponseSchema>;

export const StockDetailInfoSchema = z.object({
  ticker: z.string(),
  name: z.string(),
  isin: z.string(),
  total_dividends: z.number(),
  dividend_count: z.number(),
  average_dividend: z.number(),
  min_dividend: z.number(),
  max_dividend: z.number(),
  first_dividend_date: z.string().nullable(),
  last_dividend_date: z.string().nullable(),
  last_dividend_amount: z.number(),
  payment_cadence: z.string(),
  payments_per_year: z.number(),
});

export const YearlyTotalSchema = z.object({
  year: z.number(),
  total: z.number(),
});

export const PaymentHistoryItemSchema = z.object({
  date: z.string(),
  amount: z.number(),
  shares: z.number(),
});

export const MonthlyGrowthItemSchema = z.object({
  month: z.string(),
  total: z.number(),
  percent_change: z.number().nullable(),
});

export const StockDetailResponseSchema = z.object({
  detail: StockDetailInfoSchema,
  yearly_totals: z.array(YearlyTotalSchema),
  payment_history: z.array(PaymentHistoryItemSchema),
  monthly_growth: z.array(MonthlyGrowthItemSchema),
});

export type StockDetailResponse = z.infer<typeof StockDetailResponseSchema>;

// ============================================================================
// Calendar Schemas
// ============================================================================

export const DividendEventSchema = z.object({
  date: z.string(),
  ticker: z.string(),
  company_name: z.string(),
  amount: z.number(),
  expected: z.boolean(),
});

export const CalendarMonthSchema = z.object({
  year: z.number(),
  month: z.number(),
  events: z.array(DividendEventSchema),
  total: z.number(),
});

export const UpcomingDividendSchema = z.object({
  ticker: z.string(),
  company_name: z.string(),
  expected_date: z.string(),
  estimated_amount: z.number(),
  confidence: z.enum(['low', 'medium', 'high']),
});

export const UpcomingDividendLiveSchema = z.object({
  ticker: z.string(),
  company_name: z.string(),
  ex_date: z.string(),
  amount: z.number().nullable().optional(),
  payment_date: z.string().nullable().optional(),
  record_date: z.string().nullable().optional(),
  declaration_date: z.string().nullable().optional(),
  source: z.string(),
});

export type CalendarMonth = z.infer<typeof CalendarMonthSchema>;
export type DividendEvent = z.infer<typeof DividendEventSchema>;
export type UpcomingDividend = z.infer<typeof UpcomingDividendSchema>;
export type UpcomingDividendLive = z.infer<typeof UpcomingDividendLiveSchema>;

// ============================================================================
// Monthly Analysis Schemas
// ============================================================================

export const MonthlyByYearDataSchema = z.object({
  months: z.array(z.string()),
  years: z.record(z.string(), z.array(z.number().nullable())),
});

export const HeatmapCellSchema = z.object({
  row: z.string(),
  col: z.string(),
  value: z.number(),
});

export const HeatmapDataSchema = z.object({
  rows: z.array(z.string()),
  cols: z.array(z.string()),
  data: z.array(HeatmapCellSchema),
});

export const MonthlyAnalysisResponseSchema = z.object({
  by_year: MonthlyByYearDataSchema,
  heatmap: HeatmapDataSchema,
  companies: z.array(z.string()),
  months: z.array(z.string()),
  years: z.array(z.number()),
});

export type MonthlyAnalysisResponse = z.infer<typeof MonthlyAnalysisResponseSchema>;

// ============================================================================
// Forecast Schemas
// ============================================================================

export const ForecastDataPointSchema = z.object({
  date: z.string(),
  predicted: z.number(),
  lower_bound: z.number().optional(),
  upper_bound: z.number().optional(),
});

export const ForecastResultSchema = z.object({
  model_name: z.string(),
  forecast: z.array(ForecastDataPointSchema),
  historical: z.array(z.object({
    date: z.string(),
    value: z.number(),
  })),
  metrics: z.record(z.string(), z.unknown()),
  total_projected: z.number(),
  monthly_average: z.number(),
  annual_projections: z.array(z.object({
    year: z.string(),
    projected: z.number(),
  })),
});

export const AllForecastsResponseSchema = z.object({
  sarimax: ForecastResultSchema.nullable(),
  holt_winters: ForecastResultSchema.nullable(),
  prophet: ForecastResultSchema.nullable(),
  theta: ForecastResultSchema.nullable(),
  simple_average: ForecastResultSchema.nullable(),
  ensemble: ForecastResultSchema.nullable(),
  available_models: z.array(z.string()),
  current_month_tracking: z.object({
    date: z.string(),
    value: z.number(),
    is_partial: z.boolean(),
  }).nullable(),
});

export type AllForecastsResponse = z.infer<typeof AllForecastsResponseSchema>;

// ============================================================================
// Helper function to safely parse API responses
// ============================================================================

export function safeParseApiResponse<T>(
  schema: z.ZodSchema<T>,
  data: unknown,
  fallback?: T
): T {
  const result = schema.safeParse(data);

  if (result.success) {
    return result.data;
  }

  console.error('API response validation failed:', result.error);

  if (fallback !== undefined) {
    return fallback;
  }

  throw new Error(`API response validation failed: ${result.error.message}`);
}
