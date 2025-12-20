'use client';

import { useState, useMemo } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useStocksOverview,
  useStocksByPeriod,
  useStocksGrowth,
  useStockDetails,
} from '@/hooks/useStocks';
import { usePortfolioStore } from '@/store/portfolioStore';
import { formatCurrency, formatPercentage } from '@/lib/constants';
import {
  PlotlyStackedBarChart,
  PlotlyDonutChart,
  PlotlyBarChart,
  PlotlyScatterWithMA,
} from '@/components/charts/plotly';
import {
  Building2,
  TrendingUp,
  AlertTriangle,
  Calendar,
  DollarSign,
} from 'lucide-react';

type PeriodType = 'Monthly' | 'Quarterly' | 'Yearly';

function getRiskBadgeVariant(risk: string): 'destructive' | 'secondary' | 'default' {
  switch (risk) {
    case 'High':
      return 'destructive';
    case 'Medium':
      return 'secondary';
    default:
      return 'default';
  }
}

export default function StocksPage() {
  const { currency } = usePortfolioStore();
  const [periodType, setPeriodType] = useState<PeriodType>('Quarterly');
  const [selectedStock, setSelectedStock] = useState<string>('');

  // Data fetching
  const { data: overview, isLoading: overviewLoading, error } = useStocksOverview();
  const { data: periodData, isLoading: periodLoading } = useStocksByPeriod(periodType);
  const { data: growthData, isLoading: growthLoading } = useStocksGrowth(periodType);
  const { data: stockDetail, isLoading: stockDetailLoading } = useStockDetails(selectedStock);

  // Transform period data for Plotly stacked bar chart
  const stackedBarData = useMemo(() => {
    if (!periodData?.data || !periodData.stocks) return { periods: [], series: [] };

    const periods = periodData.data.map((item) => item.period);
    const series = periodData.stocks.map((stock) => ({
      name: stock,
      values: periodData.data.map((item) => item.stocks[stock] || 0),
    }));

    return { periods, series };
  }, [periodData]);

  // Transform growth data for Plotly bar chart with conditional colors
  const growthChartData = useMemo(() => {
    if (!growthData?.data) return { labels: [], values: [] };

    return {
      labels: growthData.data.map((item) => item.period),
      values: growthData.data.map((item) => item.growth_percent || 0),
    };
  }, [growthData]);

  // Transform distribution for Plotly donut chart
  const pieChartData = useMemo(() => {
    if (!overview?.distribution) return { labels: [], values: [] };

    const top10 = overview.distribution.slice(0, 10);
    return {
      labels: top10.map((item) => item.name),
      values: top10.map((item) => item.total),
    };
  }, [overview]);

  // Yearly totals for individual stock - for bar chart
  const yearlyChartData = useMemo(() => {
    if (!stockDetail?.yearly_totals) return { labels: [], values: [] };

    return {
      labels: stockDetail.yearly_totals.map((item) => String(item.year)),
      values: stockDetail.yearly_totals.map((item) => item.total),
    };
  }, [stockDetail]);

  // Payment history for scatter + MA chart
  const paymentScatterData = useMemo(() => {
    if (!stockDetail?.payment_history) return { x: [], y: [] };

    const sorted = [...stockDetail.payment_history].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );
    return {
      x: sorted.map((item) => item.date),
      y: sorted.map((item) => item.amount),
    };
  }, [stockDetail]);

  // Monthly growth for individual stock
  const monthlyGrowthData = useMemo(() => {
    if (!stockDetail?.monthly_growth) return { labels: [], values: [] };

    return {
      labels: stockDetail.monthly_growth.map((item) => item.month),
      values: stockDetail.monthly_growth.map((item) => item.percent_change || 0),
    };
  }, [stockDetail]);

  if (error) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-full">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="text-destructive">Error Loading Data</CardTitle>
              <CardDescription>Failed to load stock analysis data.</CardDescription>
            </CardHeader>
          </Card>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Stock Analysis</h1>
          <p className="text-muted-foreground">
            Analyze dividend performance by stock and time period
          </p>
        </div>

        {/* Main Tabs */}
        <Tabs defaultValue="period" className="space-y-6">
          <TabsList>
            <TabsTrigger value="period">Time Period Analysis</TabsTrigger>
            <TabsTrigger value="individual">Individual Company</TabsTrigger>
          </TabsList>

          {/* Time Period Analysis Tab */}
          <TabsContent value="period" className="space-y-6">
            {/* Period Selector */}
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium">Time Period:</span>
              <div className="flex gap-2">
                {(['Monthly', 'Quarterly', 'Yearly'] as PeriodType[]).map((type) => (
                  <button
                    key={type}
                    onClick={() => setPeriodType(type)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      periodType === type
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            {/* Stacked Bar Chart */}
            <Card>
              <CardHeader>
                <CardTitle>{periodType} Dividend Income by Stock</CardTitle>
                <CardDescription>Dividend amounts by stock for each time period</CardDescription>
              </CardHeader>
              <CardContent>
                {periodLoading ? (
                  <Skeleton className="h-[600px]" />
                ) : stackedBarData.series.length > 0 ? (
                  <PlotlyStackedBarChart
                    key={`stacked-bar-${periodType}`}
                    data={stackedBarData}
                    title=""
                    xAxisTitle="Time Period"
                    yAxisTitle={`Dividend Amount (${currency})`}
                    height={600}
                    currency={currency}
                    showTextLabels={true}
                  />
                ) : (
                  <div className="h-[600px] flex items-center justify-center text-muted-foreground">
                    No data available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Distribution and Growth Row */}
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Portfolio Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>Portfolio Distribution</CardTitle>
                  <CardDescription>Top 10 stocks by dividend income</CardDescription>
                </CardHeader>
                <CardContent>
                  {overviewLoading ? (
                    <Skeleton className="h-[400px]" />
                  ) : pieChartData.labels.length > 0 ? (
                    <PlotlyDonutChart
                      labels={pieChartData.labels}
                      values={pieChartData.values}
                      height={400}
                      showLegend={true}
                      textInfo="percent"
                      centerText="Total Dividends"
                      centerValue={formatCurrency(overview?.total_dividends || 0, currency)}
                    />
                  ) : (
                    <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                      No data available
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Growth Analysis */}
              <Card>
                <CardHeader>
                  <CardTitle>{periodType} Growth Analysis</CardTitle>
                  <CardDescription>Period-over-period growth rate (green = positive, red = negative)</CardDescription>
                </CardHeader>
                <CardContent>
                  {growthLoading ? (
                    <Skeleton className="h-[400px]" />
                  ) : growthChartData.labels.length > 0 ? (
                    <PlotlyBarChart
                      key={`growth-chart-${periodType}`}
                      labels={growthChartData.labels}
                      values={growthChartData.values}
                      height={400}
                      orientation="vertical"
                      conditionalColors={true}
                      valueFormat=".1f"
                      valueSuffix="%"
                      yAxisTitle="Growth Rate (%)"
                      showValues={true}
                      textPosition="outside"
                    />
                  ) : (
                    <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                      No data available
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Summary Stats */}
            <div className="grid gap-4 md:grid-cols-4">
              {overviewLoading ? (
                [...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)
              ) : (
                <>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Total Stocks</span>
                      </div>
                      <div className="text-2xl font-bold mt-2">{overview?.total_stocks || 0}</div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Total Dividends</span>
                      </div>
                      <div className="text-2xl font-bold mt-2">
                        {formatCurrency(overview?.total_dividends || 0, currency)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Avg Growth</span>
                      </div>
                      <div className="text-2xl font-bold mt-2">
                        {growthData?.average_growth !== null
                          ? `${growthData?.average_growth?.toFixed(1)}%`
                          : 'N/A'}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Top 5 Concentration</span>
                      </div>
                      <div className="text-2xl font-bold mt-2">
                        {formatPercentage(overview?.concentration.top_5_percent || 0, 1)}
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </div>

            {/* Concentration Risk Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  Concentration Risk Analysis
                </CardTitle>
                <CardDescription>
                  Portfolio concentration across top holdings
                </CardDescription>
              </CardHeader>
              <CardContent>
                {overviewLoading ? (
                  <div className="grid gap-4 md:grid-cols-4">
                    {[...Array(4)].map((_, i) => (
                      <Skeleton key={i} className="h-24" />
                    ))}
                  </div>
                ) : overview?.concentration ? (
                  <div className="grid gap-4 md:grid-cols-4">
                    <Card>
                      <CardContent className="pt-6">
                        <div className="text-sm text-muted-foreground">Top Stock</div>
                        <div className="text-2xl font-bold">
                          {formatPercentage(overview.concentration.top_1_percent, 1)}
                        </div>
                        <Badge variant={getRiskBadgeVariant(overview.concentration.top_1_risk)}>
                          {overview.concentration.top_1_risk} Risk
                        </Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-6">
                        <div className="text-sm text-muted-foreground">Top 3 Stocks</div>
                        <div className="text-2xl font-bold">
                          {formatPercentage(overview.concentration.top_3_percent, 1)}
                        </div>
                        <Badge variant={getRiskBadgeVariant(overview.concentration.top_3_risk)}>
                          {overview.concentration.top_3_risk} Risk
                        </Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-6">
                        <div className="text-sm text-muted-foreground">Top 5 Stocks</div>
                        <div className="text-2xl font-bold">
                          {formatPercentage(overview.concentration.top_5_percent, 1)}
                        </div>
                        <Badge variant={getRiskBadgeVariant(overview.concentration.top_5_risk)}>
                          {overview.concentration.top_5_risk} Risk
                        </Badge>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-6">
                        <div className="text-sm text-muted-foreground">Top 10 Stocks</div>
                        <div className="text-2xl font-bold">
                          {formatPercentage(overview.concentration.top_10_percent, 1)}
                        </div>
                        <Badge variant={getRiskBadgeVariant(overview.concentration.top_10_risk)}>
                          {overview.concentration.top_10_risk} Risk
                        </Badge>
                      </CardContent>
                    </Card>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Individual Company Tab */}
          <TabsContent value="individual" className="space-y-6">
            {/* Company Selector */}
            <Card>
              <CardHeader>
                <CardTitle>Select Company</CardTitle>
                <CardDescription>Choose a company to view detailed analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <Select value={selectedStock} onValueChange={setSelectedStock}>
                  <SelectTrigger className="w-full max-w-md">
                    <SelectValue placeholder="Select a company..." />
                  </SelectTrigger>
                  <SelectContent>
                    {overview?.stocks.map((stock) => (
                      <SelectItem key={stock.ticker} value={stock.name}>
                        {stock.name} ({stock.ticker})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            {selectedStock && (
              <>
                {/* Stock Metrics */}
                {stockDetailLoading ? (
                  <div className="grid gap-4 md:grid-cols-3">
                    {[...Array(3)].map((_, i) => (
                      <Skeleton key={i} className="h-24" />
                    ))}
                  </div>
                ) : stockDetail?.detail ? (
                  <div className="grid gap-4 md:grid-cols-3">
                    <Card>
                      <CardContent className="pt-6">
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">Total Dividends</span>
                        </div>
                        <div className="text-2xl font-bold mt-2">
                          {formatCurrency(stockDetail.detail.total_dividends, currency)}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {stockDetail.detail.dividend_count} payments
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-6">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">Latest Payment</span>
                        </div>
                        <div className="text-2xl font-bold mt-2">
                          {formatCurrency(stockDetail.detail.last_dividend_amount, currency)}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {stockDetail.detail.last_dividend_date
                            ? new Date(stockDetail.detail.last_dividend_date).toLocaleDateString()
                            : 'N/A'}
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-6">
                        <div className="flex items-center gap-2">
                          <TrendingUp className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">Payment Pattern</span>
                        </div>
                        <div className="text-2xl font-bold mt-2">
                          {stockDetail.detail.payment_cadence}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {stockDetail.detail.payments_per_year.toFixed(1)} payments/year
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                ) : null}

                {/* Yearly Bar Chart and Payment Scatter Row */}
                <div className="grid gap-6 lg:grid-cols-2">
                  {/* Yearly Totals */}
                  <Card>
                    <CardHeader>
                      <CardTitle>{selectedStock} Annual Dividend Totals</CardTitle>
                      <CardDescription>Total dividends received each year</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {stockDetailLoading ? (
                        <Skeleton className="h-[400px]" />
                      ) : yearlyChartData.labels.length > 0 ? (
                        <PlotlyBarChart
                          labels={yearlyChartData.labels}
                          values={yearlyChartData.values}
                          height={400}
                          orientation="vertical"
                          color="#3b82f6"
                          showValues={true}
                          valueFormat=",.2f"
                          valuePrefix={currency}
                          yAxisTitle={`Dividend Amount (${currency})`}
                          xAxisTitle="Year"
                        />
                      ) : (
                        <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                          No data available
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Payment History Scatter with Moving Average */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Payment History Trend</CardTitle>
                      <CardDescription>Individual payments with 3-point moving average</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {stockDetailLoading ? (
                        <Skeleton className="h-[400px]" />
                      ) : paymentScatterData.x.length > 0 ? (
                        <PlotlyScatterWithMA
                          x={paymentScatterData.x}
                          y={paymentScatterData.y}
                          height={400}
                          xAxisTitle="Date"
                          yAxisTitle={`Amount (${currency})`}
                          maWindow={3}
                        />
                      ) : (
                        <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                          No payment history available
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Month-to-Month Growth Rate Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle>Payment Growth Analysis</CardTitle>
                    <CardDescription>Month-to-month dividend change percentage</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {stockDetailLoading ? (
                      <Skeleton className="h-[350px]" />
                    ) : monthlyGrowthData.labels.length > 0 ? (
                      <PlotlyBarChart
                        labels={monthlyGrowthData.labels}
                        values={monthlyGrowthData.values}
                        height={350}
                        orientation="vertical"
                        conditionalColors={true}
                        valueFormat=".1f"
                        valueSuffix="%"
                        yAxisTitle="Growth Rate (%)"
                        showValues={true}
                        textPosition="outside"
                      />
                    ) : (
                      <div className="h-[350px] flex items-center justify-center text-muted-foreground">
                        No growth data available
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Payment History Table */}
                <Card>
                  <CardHeader>
                    <CardTitle>Payment History</CardTitle>
                    <CardDescription>All dividend payments received</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {stockDetailLoading ? (
                      <Skeleton className="h-64" />
                    ) : stockDetail?.payment_history ? (
                      <div className="max-h-[400px] overflow-auto">
                        <table className="w-full">
                          <thead className="sticky top-0 bg-background">
                            <tr className="border-b">
                              <th className="text-left py-2 px-4 font-medium">Date</th>
                              <th className="text-right py-2 px-4 font-medium">Amount</th>
                              <th className="text-right py-2 px-4 font-medium">Shares</th>
                            </tr>
                          </thead>
                          <tbody>
                            {stockDetail.payment_history.map((payment, idx) => (
                              <tr key={idx} className="border-b last:border-0">
                                <td className="py-2 px-4">
                                  {new Date(payment.date).toLocaleDateString()}
                                </td>
                                <td className="py-2 px-4 text-right font-medium">
                                  {formatCurrency(payment.amount, currency)}
                                </td>
                                <td className="py-2 px-4 text-right text-muted-foreground">
                                  {payment.shares.toFixed(2)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-muted-foreground">No payment history available</p>
                    )}
                  </CardContent>
                </Card>
              </>
            )}

            {!selectedStock && (
              <Card>
                <CardContent className="py-12 text-center text-muted-foreground">
                  <Building2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Select a company above to view detailed analysis</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
