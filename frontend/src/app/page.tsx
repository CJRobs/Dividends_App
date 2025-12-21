'use client';

/**
 * Overview page - Wealth Observatory Dashboard
 * A stunning, refined dashboard with elegant data visualization
 */

import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useOverview } from '@/hooks/usePortfolio';
import { formatCurrency, formatPercentage, CHART_COLORS } from '@/lib/constants';
import { usePortfolioStore } from '@/store/portfolioStore';
import {
  TrendingUp,
  Wallet,
  PieChart as PieChartIcon,
  Calendar,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  Target,
  Zap,
  ExternalLink
} from 'lucide-react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { cn } from '@/lib/utils';
import { useCountUp, formatCountUp } from '@/hooks/useCountUp';

// Plotly Charts
import { PlotlyBarChart } from '@/components/charts/PlotlyBarChart';
import { PlotlyLineChart } from '@/components/charts/PlotlyLineChart';
import { PlotlyDonutChart } from '@/components/charts/PlotlyPieChart';

interface DistributionData {
  portfolio_allocation: { name: string; value: number; fullName: string }[];
  monthly_totals: { month: string; monthFull: string; value: number }[];
  top_stocks_horizontal: { ticker: string; name: string; total: number }[];
  recent_trend: { date: string; label: string; value: number }[];
  summary_stats: {
    total_lifetime: number;
    monthly_average: number;
    best_month: string | null;
    best_month_value: number;
    yoy_growth: number | null;
  };
  projected_income?: {
    ytd_total: number;
    projected_annual: number;
    last_year_total: number;
    projected_vs_last_year: number | null;
    months_elapsed: number;
  };
  concentration_risk?: {
    top_3_percentage: number;
    top_3_stocks: string[];
    hhi_index: number;
    concentration_level: 'Low' | 'Medium' | 'High';
    warning: string | null;
    unique_stocks: number;
  };
  dividend_streak?: {
    current_streak: number;
    longest_streak: number;
    months_with_dividends: number;
    consistency_rate: number;
  };
}

// Animated number component
function AnimatedNumber({
  value,
  prefix = '',
  suffix = '',
  decimals = 0,
  delay = 0,
}: {
  value: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  delay?: number;
}) {
  const animatedValue = useCountUp(value, { duration: 1500, delay, decimals });
  return (
    <span className="number-display">
      {formatCountUp(animatedValue, { prefix, decimals })}
      {suffix}
    </span>
  );
}

// Hero stat component for large display numbers
function HeroStat({
  value,
  numericValue,
  label,
  trend,
  trendValue,
  icon: Icon,
  delay = 0,
  variant = 'default',
  prefix = '',
}: {
  value: string;
  numericValue?: number;
  label: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon: React.ElementType;
  delay?: number;
  variant?: 'default' | 'primary' | 'accent';
  prefix?: string;
}) {
  return (
    <div
      className={cn(
        "animate-enter group",
        `delay-${delay}`
      )}
      style={{ animationDelay: `${delay * 75}ms` }}
    >
      <Card className="card-premium overflow-hidden h-full">
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className={cn(
              "w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 group-hover:scale-110 group-hover:rotate-3",
              variant === 'primary' && "bg-primary/10 text-primary shadow-lg shadow-primary/10",
              variant === 'accent' && "bg-amber-500/10 text-amber-500 shadow-lg shadow-amber-500/10",
              variant === 'default' && "bg-muted text-muted-foreground"
            )}>
              <Icon className="h-6 w-6 transition-transform duration-300 group-hover:scale-110" />
            </div>
            {trend && trendValue && (
              <div className={cn(
                "flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium transition-all duration-300",
                trend === 'up' && "bg-emerald-500/10 text-emerald-500",
                trend === 'down' && "bg-red-500/10 text-red-500",
                trend === 'neutral' && "bg-muted text-muted-foreground"
              )}>
                {trend === 'up' && <ArrowUpRight className="h-3 w-3" />}
                {trend === 'down' && <ArrowDownRight className="h-3 w-3" />}
                {trendValue}
              </div>
            )}
          </div>

          <div className="space-y-1">
            <p className={cn(
              "text-3xl lg:text-4xl font-serif tracking-tight transition-all duration-300",
              variant === 'primary' && "text-gradient",
              variant === 'accent' && "text-gradient-gold"
            )}>
              {numericValue !== undefined ? (
                <AnimatedNumber
                  value={numericValue}
                  prefix={prefix}
                  decimals={2}
                  delay={delay * 75 + 300}
                />
              ) : (
                value
              )}
            </p>
            <p className="text-sm text-muted-foreground">{label}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Section header component
function SectionHeader({
  title,
  description,
  icon: Icon,
  delay = 0
}: {
  title: string;
  description?: string;
  icon: React.ElementType;
  delay?: number;
}) {
  return (
    <div
      className="animate-enter flex items-center gap-4 mb-6"
      style={{ animationDelay: `${delay * 75}ms` }}
    >
      <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
        <Icon className="h-5 w-5 text-primary" />
      </div>
      <div>
        <h2 className="text-xl font-serif">{title}</h2>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
    </div>
  );
}

export default function OverviewPage() {
  const { data, isLoading, error } = useOverview();
  const { currency } = usePortfolioStore();

  // Fetch distribution data
  const { data: distribution, isLoading: distLoading } = useQuery<DistributionData>({
    queryKey: ['overview-distribution'],
    queryFn: () => api.get('/api/overview/distribution').then(res => res.data),
  });

  // Extract data from the complete overview response
  const summary = data?.summary;
  const topStocks = data?.top_stocks;
  const recentDividends = data?.recent_dividends;
  const ytdChart = data?.ytd_chart;
  const monthlyChart = data?.monthly_chart;

  if (error) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <Card className="w-full max-w-md border-destructive/50">
            <CardHeader>
              <div className="w-12 h-12 rounded-2xl bg-destructive/10 flex items-center justify-center mb-4">
                <Zap className="h-6 w-6 text-destructive" />
              </div>
              <CardTitle className="text-destructive">Connection Error</CardTitle>
              <CardDescription>
                Unable to connect to the portfolio server
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {error instanceof Error ? error.message : 'Unknown error occurred'}
              </p>
              <div className="p-4 rounded-lg bg-muted font-mono text-xs">
                <p className="text-muted-foreground mb-2">Start the backend:</p>
                <code>cd backend && uvicorn app.main:app --reload</code>
              </div>
            </CardContent>
          </Card>
        </div>
      </Layout>
    );
  }

  // Prepare chart data for YTD
  const ytdChartData = ytdChart?.dates?.map((date: string, i: number) => ({
    date: new Date(date).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' }),
    amount: ytdChart.values?.[i] || 0,
  })) || [];

  const ytdGrowth = summary?.ytd_vs_last_year_percent;

  return (
    <Layout>
      <div className="space-y-8">
        {/* Page Header */}
        <div className="animate-enter">
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>Dashboard</span>
          </div>
          <h1 className="text-4xl lg:text-5xl font-serif tracking-tight mb-2">
            Portfolio Overview
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Track your dividend income, analyze performance, and forecast future returns
          </p>
        </div>

        {/* Hero Stats Grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {isLoading ? (
            <>
              {[...Array(3)].map((_, i) => (
                <Card key={`skeleton-${i}`} className="overflow-hidden">
                  <CardContent className="p-6">
                    <Skeleton className="h-12 w-12 rounded-2xl mb-4" />
                    <Skeleton className="h-10 w-32 mb-2" />
                    <Skeleton className="h-4 w-24" />
                  </CardContent>
                </Card>
              ))}
            </>
          ) : (
            <>
              <HeroStat
                value={formatCurrency(summary?.total_dividends || 0, currency)}
                numericValue={summary?.total_dividends || 0}
                prefix={currency === 'GBP' ? '£' : currency === 'EUR' ? '€' : '$'}
                label="Total Dividends Earned"
                icon={Wallet}
                variant="primary"
                delay={1}
              />
              <HeroStat
                value={formatCurrency(summary?.total_dividends_ytd || 0, currency)}
                numericValue={summary?.total_dividends_ytd || 0}
                prefix={currency === 'GBP' ? '£' : currency === 'EUR' ? '€' : '$'}
                label="Year to Date"
                icon={Calendar}
                trend={ytdGrowth !== undefined && ytdGrowth !== null ? (ytdGrowth >= 0 ? 'up' : 'down') : undefined}
                trendValue={ytdGrowth !== undefined && ytdGrowth !== null ? formatPercentage(Math.abs(ytdGrowth)) : undefined}
                variant="accent"
                delay={2}
              />
              <HeroStat
                value={formatCurrency(summary?.average_dividend || 0, currency)}
                numericValue={summary?.average_dividend || 0}
                prefix={currency === 'GBP' ? '£' : currency === 'EUR' ? '€' : '$'}
                label="Average Payment"
                icon={Target}
                delay={3}
              />
            </>
          )}
        </div>



        {/* Distribution Charts Section */}
        <div>
          <SectionHeader
            title="Dividend Distribution"
            description="Allocation and monthly breakdown"
            icon={PieChartIcon}
            delay={10}
          />

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Portfolio Allocation Donut */}
            <div className="animate-enter" style={{ animationDelay: '825ms' }}>
              <Card className="overflow-hidden h-full">
                <CardHeader>
                  <CardTitle className="text-base">Portfolio Allocation</CardTitle>
                  <CardDescription>Top 10 positions by dividend contribution</CardDescription>
                </CardHeader>
                <CardContent>
                  {distLoading ? (
                    <div className="h-[380px] flex items-center justify-center">
                      <div className="w-48 h-48 rounded-full border-4 border-muted animate-pulse" />
                    </div>
                  ) : distribution?.portfolio_allocation && distribution.portfolio_allocation.length > 0 ? (
                    <div className="chart-reveal" style={{ animationDelay: '900ms' }}>
                      <PlotlyDonutChart
                        labels={distribution.portfolio_allocation.map(d => d.name)}
                        values={distribution.portfolio_allocation.map(d => d.value)}
                        height={380}
                        showLegend={true}
                        textInfo="percent+label"
                      />
                    </div>
                  ) : (
                    <div className="h-[380px] flex flex-col items-center justify-center text-muted-foreground">
                      <PieChartIcon className="h-12 w-12 mb-4 opacity-20" />
                      <p>No allocation data available</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Monthly Totals Bar Chart */}
            <div className="animate-enter" style={{ animationDelay: '900ms' }}>
              <Card className="overflow-hidden h-full">
                <CardHeader>
                  <CardTitle className="text-base">Monthly Distribution</CardTitle>
                  <CardDescription>Dividends by calendar month (all years)</CardDescription>
                </CardHeader>
                <CardContent>
                  {distLoading ? (
                    <div className="h-[380px] flex items-end justify-around gap-2 p-4">
                      {[40, 65, 35, 70, 55, 80, 45, 60, 50, 75, 38, 68].map((height, i) => (
                        <div
                          key={i}
                          className="w-full bg-muted rounded-t animate-pulse"
                          style={{ height: `${height}%` }}
                        />
                      ))}
                    </div>
                  ) : distribution?.monthly_totals && distribution.monthly_totals.length > 0 ? (
                    <div className="chart-reveal" style={{ animationDelay: '975ms' }}>
                      <PlotlyBarChart
                        labels={distribution.monthly_totals.map(d => d.month)}
                        values={distribution.monthly_totals.map(d => d.value)}
                        height={380}
                        orientation="vertical"
                        yAxisTitle={`Dividends (${currency === 'GBP' ? '£' : '$'})`}
                      />
                    </div>
                  ) : (
                    <div className="h-[380px] flex flex-col items-center justify-center text-muted-foreground">
                      <BarChart3 className="h-12 w-12 mb-4 opacity-20" />
                      <p>No monthly data available</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

        {/* Growth Analysis Section */}
        <div>
          <SectionHeader
            title="Growth & Performance"
            description="Track your dividend income growth"
            icon={TrendingUp}
            delay={14}
          />

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Top Stocks Horizontal Bar */}
            <div className="animate-enter" style={{ animationDelay: '1125ms' }}>
              <Card className="overflow-hidden h-full">
                <CardHeader>
                  <CardTitle className="text-base">Top Contributors</CardTitle>
                  <CardDescription>Your highest dividend-paying stocks</CardDescription>
                </CardHeader>
                <CardContent>
                  {distLoading ? (
                    <div className="h-[450px] space-y-4 p-4">
                      {[...Array(10)].map((_, i) => (
                        <div key={i} className="flex items-center gap-3">
                          <Skeleton className="w-16 h-4" />
                          <Skeleton className="flex-1 h-6 rounded" style={{ width: `${100 - i * 8}%` }} />
                        </div>
                      ))}
                    </div>
                  ) : distribution?.top_stocks_horizontal && distribution.top_stocks_horizontal.length > 0 ? (
                    <div className="chart-reveal" style={{ animationDelay: '1200ms' }}>
                      <PlotlyBarChart
                        labels={distribution.top_stocks_horizontal.map(d => d.ticker)}
                        values={distribution.top_stocks_horizontal.map(d => d.total)}
                        height={450}
                        orientation="horizontal"
                        xAxisTitle={`Total Dividends (${currency === 'GBP' ? '£' : '$'})`}
                      />
                    </div>
                  ) : (
                    <div className="h-[450px] flex flex-col items-center justify-center text-muted-foreground">
                      <BarChart3 className="h-12 w-12 mb-4 opacity-20" />
                      <p>No stock data available</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Recent Trend Line Chart */}
            <div className="animate-enter" style={{ animationDelay: '1200ms' }}>
              <Card className="overflow-hidden h-full">
                <CardHeader>
                  <CardTitle className="text-base">Recent Trend</CardTitle>
                  <CardDescription>Last 12 months of dividend income</CardDescription>
                </CardHeader>
                <CardContent>
                  {distLoading ? (
                    <div className="h-[450px] flex items-center justify-center">
                      <div className="w-full h-32 relative">
                        <div className="absolute inset-0 bg-gradient-to-r from-muted via-muted/50 to-muted animate-pulse rounded" />
                      </div>
                    </div>
                  ) : distribution?.recent_trend && distribution.recent_trend.length > 0 ? (
                    <div className="chart-reveal" style={{ animationDelay: '1275ms' }}>
                      <PlotlyLineChart
                        data={{
                          x: distribution.recent_trend.map(d => d.label),
                          y: distribution.recent_trend.map(d => d.value),
                        }}
                        height={450}
                        yAxisTitle={`Dividends (${currency === 'GBP' ? '£' : '$'})`}
                        showMarkers={true}
                        curveType="spline"
                      />
                    </div>
                  ) : (
                    <div className="h-[450px] flex flex-col items-center justify-center text-muted-foreground">
                      <TrendingUp className="h-12 w-12 mb-4 opacity-20" />
                      <p>No trend data available</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

        {/* YTD Progress Section */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* YTD Cumulative Chart */}
          <div className="animate-enter" style={{ animationDelay: '1350ms' }}>
            <Card className="overflow-hidden">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                    <BarChart3 className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-base">YTD Cumulative Growth</CardTitle>
                    <CardDescription>Running total this year</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <Skeleton className="h-[280px] w-full rounded-lg" />
                ) : ytdChartData.length > 0 ? (
                  <div className="chart-reveal" style={{ animationDelay: '1425ms' }}>
                    <PlotlyLineChart
                      data={{
                        x: ytdChartData.map((d: { date: string }) => d.date),
                        y: ytdChartData.map((d: { amount: number }) => d.amount),
                      }}
                      height={280}
                      yAxisTitle="Cumulative Dividends"
                      showMarkers={true}
                      curveType="spline"
                    />
                  </div>
                ) : (
                  <div className="h-[280px] flex flex-col items-center justify-center text-muted-foreground">
                    <TrendingUp className="h-10 w-10 mb-3 opacity-20" />
                    <p className="text-sm">No YTD data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Monthly Dividends Current Year */}
          <div className="animate-enter" style={{ animationDelay: '1425ms' }}>
            <Card className="overflow-hidden">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                    <Calendar className="h-4 w-4 text-amber-500" />
                  </div>
                  <div>
                    <CardTitle className="text-base">Monthly Breakdown</CardTitle>
                    <CardDescription>Dividends by month this year</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <Skeleton className="h-[280px] w-full rounded-lg" />
                ) : monthlyChart?.labels && monthlyChart.labels.length > 0 ? (
                  <div className="chart-reveal" style={{ animationDelay: '1500ms' }}>
                    <PlotlyBarChart
                      labels={monthlyChart.labels.map((m: string) => m.substring(0, 3))}
                      values={monthlyChart.values || []}
                      height={280}
                      orientation="vertical"
                      yAxisTitle={`Dividends (${currency === 'GBP' ? '£' : '$'})`}
                    />
                  </div>
                ) : (
                  <div className="h-[280px] flex flex-col items-center justify-center text-muted-foreground">
                    <BarChart3 className="h-10 w-10 mb-3 opacity-20" />
                    <p className="text-sm">No monthly data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Top Stocks & Recent Dividends Lists */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Top Dividend Stocks List */}
          <div className="animate-enter" style={{ animationDelay: '1500ms' }}>
            <Card className="overflow-hidden">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Sparkles className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-base">Top Performers</CardTitle>
                    <CardDescription>Highest dividend-paying positions</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="space-y-3">
                    {[...Array(6)].map((_, i) => (
                      <div key={`stock-skeleton-${i}`} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                        <div className="flex items-center gap-3">
                          <Skeleton className="w-8 h-8 rounded-lg" />
                          <div>
                            <Skeleton className="h-4 w-16 mb-1" />
                            <Skeleton className="h-3 w-24" />
                          </div>
                        </div>
                        <Skeleton className="h-5 w-20" />
                      </div>
                    ))}
                  </div>
                ) : topStocks && topStocks.length > 0 ? (
                  <div className="space-y-2 max-h-[360px] overflow-y-auto pr-2">
                    {topStocks.slice(0, 10).map((stock: { ticker: string; name: string; total_dividends: number; percentage_of_portfolio: number }, i: number) => (
                      <Link
                        href={`/stocks?ticker=${encodeURIComponent(stock.ticker)}`}
                        key={stock.ticker}
                        className="flex items-center justify-between p-3 rounded-xl bg-muted/30 hover:bg-muted/50 transition-colors duration-200 group cursor-pointer"
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className="w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold text-white transition-transform duration-200 group-hover:scale-105"
                            style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
                          >
                            {stock.ticker.substring(0, 2)}
                          </div>
                          <div>
                            <p className="font-medium text-sm">{stock.ticker}</p>
                            <p className="text-xs text-muted-foreground truncate max-w-[140px]">
                              {stock.name}
                            </p>
                          </div>
                        </div>
                        <div className="text-right flex items-center gap-2">
                          <div>
                            <p className="font-semibold text-sm">
                              {formatCurrency(stock.total_dividends, currency)}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {formatPercentage(stock.percentage_of_portfolio, 1)}
                            </p>
                          </div>
                          <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 text-center text-muted-foreground">
                    <Sparkles className="h-10 w-10 mx-auto mb-3 opacity-20" />
                    <p className="text-sm">No stock data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Dividends List */}
          <div className="animate-enter" style={{ animationDelay: '1575ms' }}>
            <Card className="overflow-hidden">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <Wallet className="h-4 w-4 text-emerald-500" />
                  </div>
                  <div>
                    <CardTitle className="text-base">Recent Payments</CardTitle>
                    <CardDescription>Latest dividend receipts</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="space-y-3">
                    {[...Array(6)].map((_, i) => (
                      <div key={`recent-skeleton-${i}`} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                        <div>
                          <Skeleton className="h-4 w-16 mb-1" />
                          <Skeleton className="h-3 w-24" />
                        </div>
                        <Skeleton className="h-5 w-16" />
                      </div>
                    ))}
                  </div>
                ) : recentDividends && recentDividends.length > 0 ? (
                  <div className="space-y-2 max-h-[360px] overflow-y-auto pr-2">
                    {recentDividends.slice(0, 10).map((dividend: { ticker: string; name: string; date: string; amount: number }, idx: number) => (
                      <div
                        key={`${dividend.ticker}-${idx}`}
                        className="flex items-center justify-between p-3 rounded-xl bg-muted/30 hover:bg-muted/50 transition-colors duration-200 group"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                            <ArrowUpRight className="h-4 w-4 text-emerald-500" />
                          </div>
                          <div>
                            <p className="font-medium text-sm">{dividend.ticker}</p>
                            <p className="text-xs text-muted-foreground">
                              {new Date(dividend.date).toLocaleDateString('en-GB', {
                                day: 'numeric',
                                month: 'short',
                                year: 'numeric'
                              })}
                            </p>
                          </div>
                        </div>
                        <p className="font-semibold text-emerald-500 text-sm">
                          +{formatCurrency(dividend.amount, currency)}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 text-center text-muted-foreground">
                    <Wallet className="h-10 w-10 mx-auto mb-3 opacity-20" />
                    <p className="text-sm">No recent dividends</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Backend Not Running Notice */}
        {!isLoading && !data && (
          <Card className="border-amber-500/50 bg-amber-500/5 animate-enter" style={{ animationDelay: '300ms' }}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
                  <Zap className="h-5 w-5 text-amber-500" />
                </div>
                <div>
                  <CardTitle className="text-amber-600 dark:text-amber-400">Backend Not Running</CardTitle>
                  <CardDescription>
                    Start the FastAPI server to see your dividend data
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="p-4 rounded-xl bg-muted/50 font-mono text-sm">
                <p className="text-muted-foreground mb-2">Run these commands:</p>
                <code className="block text-xs leading-relaxed">
                  cd backend<br />
                  source venv/bin/activate<br />
                  uvicorn app.main:app --reload
                </code>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
