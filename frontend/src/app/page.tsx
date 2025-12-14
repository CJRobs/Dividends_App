'use client';

/**
 * Overview page - Main dashboard view with Plotly charts.
 */

import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useOverview } from '@/hooks/usePortfolio';
import { formatCurrency, formatPercentage, CHART_COLORS } from '@/lib/constants';
import { usePortfolioStore } from '@/store/portfolioStore';
import { TrendingUp, TrendingDown, DollarSign, PieChart as PieChartIcon, Calendar, BarChart3, Activity } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

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
        <div className="flex items-center justify-center h-full">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="text-destructive">Error Loading Data</CardTitle>
              <CardDescription>
                Failed to load portfolio data. Please ensure the backend is running.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Error: {error instanceof Error ? error.message : 'Unknown error'}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Backend should be running at: http://localhost:8000
              </p>
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

  return (
    <Layout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Portfolio Overview</h1>
          <p className="text-muted-foreground">
            Track, analyze, and forecast your dividend income
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {isLoading ? (
            <>
              {[...Array(4)].map((_, i) => (
                <Card key={`skeleton-${i}`}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-4" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-8 w-32 mb-2" />
                    <Skeleton className="h-3 w-full" />
                  </CardContent>
                </Card>
              ))}
            </>
          ) : (
            <>
              {/* Total Dividends */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Dividends</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatCurrency(summary?.total_dividends || 0, currency)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {summary?.total_count || 0} payments received
                  </p>
                </CardContent>
              </Card>

              {/* YTD Dividends */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">YTD Dividends</CardTitle>
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatCurrency(summary?.total_dividends_ytd || 0, currency)}
                  </div>
                  {summary?.ytd_vs_last_year_percent !== undefined && summary?.ytd_vs_last_year_percent !== null && (
                    <p className={`text-xs flex items-center ${
                      summary.ytd_vs_last_year_percent >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {summary.ytd_vs_last_year_percent >= 0 ? (
                        <TrendingUp className="h-3 w-3 mr-1" />
                      ) : (
                        <TrendingDown className="h-3 w-3 mr-1" />
                      )}
                      {formatPercentage(Math.abs(summary.ytd_vs_last_year_percent))} vs last year
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Unique Stocks */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Unique Stocks</CardTitle>
                  <PieChartIcon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {summary?.unique_stocks || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Dividend-paying stocks
                  </p>
                </CardContent>
              </Card>

              {/* Average Dividend */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Average Dividend</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {formatCurrency(summary?.average_dividend || 0, currency)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Per dividend payment
                  </p>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        {/* Summary Statistics Card */}
        {distribution?.summary_stats && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Summary Statistics
              </CardTitle>
              <CardDescription>Key performance metrics for your portfolio</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-4">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Total Lifetime</p>
                  <p className="text-2xl font-bold">{formatCurrency(distribution.summary_stats.total_lifetime, currency)}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Monthly Average</p>
                  <p className="text-2xl font-bold">{formatCurrency(distribution.summary_stats.monthly_average, currency)}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Best Month</p>
                  <p className="text-2xl font-bold">{formatCurrency(distribution.summary_stats.best_month_value, currency)}</p>
                  <p className="text-xs text-muted-foreground">{distribution.summary_stats.best_month || 'N/A'}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">YoY Growth</p>
                  <p className={`text-2xl font-bold flex items-center ${
                    (distribution.summary_stats.yoy_growth ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {distribution.summary_stats.yoy_growth !== null ? (
                      <>
                        {distribution.summary_stats.yoy_growth >= 0 ? (
                          <TrendingUp className="h-5 w-5 mr-1" />
                        ) : (
                          <TrendingDown className="h-5 w-5 mr-1" />
                        )}
                        {formatPercentage(Math.abs(distribution.summary_stats.yoy_growth))}
                      </>
                    ) : 'N/A'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Dividend Distribution & Analysis Section */}
        <div>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <PieChartIcon className="h-5 w-5" />
            Dividend Distribution & Analysis
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {/* Portfolio Allocation Donut (Top 10 + Others) */}
            <Card>
              <CardHeader>
                <CardTitle>Portfolio Allocation (Top 10 + Others)</CardTitle>
                <CardDescription>Dividend contribution by stock</CardDescription>
              </CardHeader>
              <CardContent>
                {distLoading ? (
                  <Skeleton className="h-[400px] w-full" />
                ) : distribution?.portfolio_allocation && distribution.portfolio_allocation.length > 0 ? (
                  <PlotlyDonutChart
                    labels={distribution.portfolio_allocation.map(d => d.name)}
                    values={distribution.portfolio_allocation.map(d => d.value)}
                    height={400}
                    showLegend={true}
                    textInfo="percent+label"
                  />
                ) : (
                  <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                    No allocation data available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Dividend Payments by Month (All Years) */}
            <Card>
              <CardHeader>
                <CardTitle>Dividend Payments by Month</CardTitle>
                <CardDescription>Total dividends by calendar month (all years)</CardDescription>
              </CardHeader>
              <CardContent>
                {distLoading ? (
                  <Skeleton className="h-[400px] w-full" />
                ) : distribution?.monthly_totals && distribution.monthly_totals.length > 0 ? (
                  <PlotlyBarChart
                    labels={distribution.monthly_totals.map(d => d.month)}
                    values={distribution.monthly_totals.map(d => d.value)}
                    height={400}
                    orientation="vertical"
                    yAxisTitle={`Dividend Amount (${currency === 'GBP' ? '£' : '$'})`}
                  />
                ) : (
                  <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                    No monthly data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Growth & Performance Analysis Section */}
        <div>
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Growth & Performance Analysis
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {/* Top 10 Dividend Stocks (Horizontal Bar) */}
            <Card>
              <CardHeader>
                <CardTitle>Top 10 Dividend Stocks</CardTitle>
                <CardDescription>Highest dividend contributors</CardDescription>
              </CardHeader>
              <CardContent>
                {distLoading ? (
                  <Skeleton className="h-[500px] w-full" />
                ) : distribution?.top_stocks_horizontal && distribution.top_stocks_horizontal.length > 0 ? (
                  <PlotlyBarChart
                    labels={distribution.top_stocks_horizontal.map(d => d.ticker)}
                    values={distribution.top_stocks_horizontal.map(d => d.total)}
                    height={500}
                    orientation="horizontal"
                    xAxisTitle={`Total Dividends (${currency === 'GBP' ? '£' : '$'})`}
                  />
                ) : (
                  <div className="h-[500px] flex items-center justify-center text-muted-foreground">
                    No stock data available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Dividend Trend (Last 12 Months) */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Dividend Trend</CardTitle>
                <CardDescription>Last 12 months of dividend income</CardDescription>
              </CardHeader>
              <CardContent>
                {distLoading ? (
                  <Skeleton className="h-[500px] w-full" />
                ) : distribution?.recent_trend && distribution.recent_trend.length > 0 ? (
                  <PlotlyLineChart
                    data={{
                      x: distribution.recent_trend.map(d => d.label),
                      y: distribution.recent_trend.map(d => d.value),
                    }}
                    height={500}
                    yAxisTitle={`Dividend Amount (${currency === 'GBP' ? '£' : '$'})`}
                    showMarkers={true}
                    curveType="spline"
                  />
                ) : (
                  <div className="h-[500px] flex items-center justify-center text-muted-foreground">
                    No trend data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* YTD Charts Row */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* YTD Cumulative Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                YTD Dividend Growth
              </CardTitle>
              <CardDescription>Cumulative dividends this year</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-[300px] w-full" />
              ) : ytdChartData.length > 0 ? (
                <PlotlyLineChart
                  data={{
                    x: ytdChartData.map((d: { date: string }) => d.date),
                    y: ytdChartData.map((d: { amount: number }) => d.amount),
                  }}
                  height={300}
                  yAxisTitle="Cumulative Dividends"
                  showMarkers={true}
                  curveType="spline"
                />
              ) : (
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  No YTD data available
                </div>
              )}
            </CardContent>
          </Card>

          {/* Monthly Dividends Chart (Current Year) */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Monthly Dividends (This Year)
              </CardTitle>
              <CardDescription>Dividends by month this year</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-[300px] w-full" />
              ) : monthlyChart?.labels && monthlyChart.labels.length > 0 ? (
                <PlotlyBarChart
                  labels={monthlyChart.labels.map((m: string) => m.substring(0, 3))}
                  values={monthlyChart.values || []}
                  height={300}
                  orientation="vertical"
                  yAxisTitle={`Dividends (${currency === 'GBP' ? '£' : '$'})`}
                />
              ) : (
                <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                  No monthly data available
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Top Stocks List and Recent Dividends */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Top Dividend Stocks List */}
          <Card>
            <CardHeader>
              <CardTitle>Top Dividend Stocks</CardTitle>
              <CardDescription>Your highest dividend-paying stocks</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  {[...Array(8)].map((_, i) => (
                    <div key={`stock-skeleton-${i}`} className="flex items-center justify-between">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-4 w-20" />
                    </div>
                  ))}
                </div>
              ) : topStocks && topStocks.length > 0 ? (
                <div className="space-y-3 max-h-[300px] overflow-y-auto">
                  {topStocks.slice(0, 10).map((stock: { ticker: string; name: string; total_dividends: number; percentage_of_portfolio: number }, i: number) => (
                    <div key={stock.ticker} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
                        />
                        <div>
                          <p className="font-medium">{stock.ticker}</p>
                          <p className="text-xs text-muted-foreground truncate max-w-[150px]">
                            {stock.name}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">
                          {formatCurrency(stock.total_dividends, currency)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatPercentage(stock.percentage_of_portfolio, 1)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No stock data available</p>
              )}
            </CardContent>
          </Card>

          {/* Recent Dividends */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Dividends</CardTitle>
              <CardDescription>Latest dividend payments received</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  {[...Array(6)].map((_, i) => (
                    <div key={`recent-skeleton-${i}`} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-4 w-20" />
                    </div>
                  ))}
                </div>
              ) : recentDividends && recentDividends.length > 0 ? (
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {recentDividends.slice(0, 10).map((dividend: { ticker: string; name: string; date: string; amount: number }, idx: number) => (
                    <div key={`${dividend.ticker}-${idx}`} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                      <div>
                        <p className="font-medium">{dividend.ticker}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(dividend.date).toLocaleDateString('en-GB', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric'
                          })}
                        </p>
                      </div>
                      <p className="font-semibold text-green-400">
                        +{formatCurrency(dividend.amount, currency)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No recent dividends</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Info Card if backend not running */}
        {!isLoading && !data && (
          <Card className="border-yellow-500">
            <CardHeader>
              <CardTitle className="text-yellow-600">Backend Not Running</CardTitle>
              <CardDescription>
                Start the FastAPI backend to see your dividend data
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-sm">Run the following commands to start the backend:</p>
              <pre className="bg-muted p-3 rounded text-xs">
                cd backend{'\n'}
                source venv/bin/activate{'\n'}
                uvicorn app.main:app --reload
              </pre>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
