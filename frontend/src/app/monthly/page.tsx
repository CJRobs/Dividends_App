'use client';

/**
 * Monthly Analysis page - Wealth Observatory Design
 * Elegant monthly dividend analysis with refined visualizations
 */

import { useState, useMemo } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useMonthlyAnalysis, useMonthlyCoverage, useMonthlyByCompany } from '@/hooks/useMonthly';
import { usePortfolioStore } from '@/store/portfolioStore';
import { formatCurrency } from '@/lib/constants';
import {
  PlotlyLineChart,
  PlotlyStackedBarChart,
  PlotlyHeatmap,
} from '@/components/charts/plotly';
import { Calendar, Target, Wallet, TrendingUp, AlertCircle, CheckCircle2, Zap, BarChart3, Grid3X3 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function MonthlyAnalysisPage() {
  const { currency } = usePortfolioStore();
  const { data, isLoading, error } = useMonthlyAnalysis();

  // Filters state
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  const [selectedMonth, setSelectedMonth] = useState<string>('All Months');
  const [monthlyExpenses, setMonthlyExpenses] = useState<number>(2000);

  // Coverage data with user's expense input
  const { data: coverageData, isLoading: coverageLoading } = useMonthlyCoverage(monthlyExpenses);

  // Company breakdown data with filters
  const { data: companyData, isLoading: companyLoading } = useMonthlyByCompany(
    selectedCompanies.length > 0 ? selectedCompanies : undefined,
    selectedMonth !== 'All Months' ? selectedMonth : undefined
  );

  // Transform line chart data for Plotly (array of line series)
  const plotlyLineData = useMemo(() => {
    if (!data?.by_year) return [];

    const { months, years } = data.by_year;
    const yearKeys = Object.keys(years).sort();

    return yearKeys.map((year) => ({
      x: months,
      y: years[year] as number[],
      name: year,
    }));
  }, [data]);

  // Transform stacked bar chart data for PlotlyStackedBarChart
  const plotlyStackedData = useMemo(() => {
    if (!companyData?.data || !companyData?.periods || !companyData?.companies) {
      return { periods: [], series: [] };
    }

    // Group by period, aggregate by company
    const periodMap = new Map<string, Record<string, number>>();

    companyData.data.forEach((item) => {
      if (!periodMap.has(item.period)) {
        periodMap.set(item.period, {});
      }
      const periodData = periodMap.get(item.period)!;
      periodData[item.company] = (periodData[item.company] || 0) + item.amount;
    });

    // Build series for each company
    const series = companyData.companies.map((company) => ({
      name: company,
      values: companyData.periods.map((period) => periodMap.get(period)?.[company] || 0),
    }));

    return {
      periods: companyData.periods,
      series,
    };
  }, [companyData]);

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
                Failed to load monthly analysis data
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Page Header */}
        <div className="animate-enter">
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>Analysis</span>
          </div>
          <h1 className="text-4xl lg:text-5xl font-serif tracking-tight mb-2">
            Monthly Analysis
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Track dividend patterns across months and years to understand your income flow
          </p>
        </div>

        {/* Monthly Dividends by Year - Line Chart */}
        <div className="animate-enter" style={{ animationDelay: '75ms' }}>
          <Card className="overflow-hidden">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <TrendingUp className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle className="text-lg">Monthly Dividends by Year</CardTitle>
                  <CardDescription>Compare dividend income across different years</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-[400px] flex items-center justify-center">
                  <div className="w-full h-32 bg-gradient-to-r from-muted via-muted/50 to-muted animate-pulse rounded" />
                </div>
              ) : plotlyLineData.length > 0 ? (
                <div className="chart-reveal">
                  <PlotlyLineChart
                    data={plotlyLineData}
                    height={400}
                    xAxisTitle="Month"
                    yAxisTitle={`Dividend Amount (${currency})`}
                    showMarkers={true}
                    curveType="spline"
                  />
                </div>
              ) : (
                <div className="h-[400px] flex flex-col items-center justify-center text-muted-foreground">
                  <TrendingUp className="h-12 w-12 mb-4 opacity-20" />
                  <p>No data available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Monthly Heatmap */}
        <div className="animate-enter" style={{ animationDelay: '150ms' }}>
          <Card className="overflow-hidden">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                  <Grid3X3 className="h-5 w-5 text-amber-500" />
                </div>
                <div>
                  <CardTitle className="text-lg">Monthly Dividend Heatmap</CardTitle>
                  <CardDescription>Year x Month matrix showing dividend amounts</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-[400px] grid grid-cols-12 gap-1 p-4">
                  {[...Array(48)].map((_, i) => (
                    <div key={i} className="bg-muted rounded animate-pulse aspect-square" />
                  ))}
                </div>
              ) : data?.heatmap ? (
                <div className="chart-reveal">
                  <PlotlyHeatmap
                    data={data.heatmap.data}
                    rows={data.heatmap.rows}
                    cols={data.heatmap.cols}
                    height={400}
                    colorScale="blues"
                    showValues={true}
                    currency={currency === 'GBP' ? '£' : currency === 'USD' ? '$' : '€'}
                  />
                </div>
              ) : (
                <div className="h-[400px] flex flex-col items-center justify-center text-muted-foreground">
                  <Grid3X3 className="h-12 w-12 mb-4 opacity-20" />
                  <p>No data available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Company Breakdown Section */}
        <div className="animate-enter" style={{ animationDelay: '225ms' }}>
          <Card className="overflow-hidden">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <BarChart3 className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle className="text-lg">Dividends by Company</CardTitle>
                  <CardDescription>Filter by company or month to see detailed breakdowns</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Filters */}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Filter by Companies</Label>
                  <Select
                    value={selectedCompanies.length > 0 ? selectedCompanies[0] : 'all'}
                    onValueChange={(value) =>
                      setSelectedCompanies(value === 'all' ? [] : [value])
                    }
                  >
                    <SelectTrigger className="h-11">
                      <SelectValue placeholder="All Companies" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Companies</SelectItem>
                      {data?.companies.map((company) => (
                        <SelectItem key={company} value={company}>
                          {company}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm text-muted-foreground">Filter by Month</Label>
                  <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                    <SelectTrigger className="h-11">
                      <SelectValue placeholder="All Months" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="All Months">All Months</SelectItem>
                      {data?.months.map((month) => (
                        <SelectItem key={month} value={month}>
                          {month}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Stacked Bar Chart */}
              <div className="h-[500px]">
                {companyLoading ? (
                  <div className="h-full flex items-end justify-around gap-2 p-4">
                    {[45, 70, 30, 65, 50, 75, 40, 55, 60, 80, 35, 72].map((height, i) => (
                      <div
                        key={i}
                        className="w-full bg-muted rounded-t animate-pulse"
                        style={{ height: `${height}%` }}
                      />
                    ))}
                  </div>
                ) : plotlyStackedData.series.length > 0 ? (
                  <div className="chart-reveal">
                    <PlotlyStackedBarChart
                      data={plotlyStackedData}
                      height={500}
                      xAxisTitle="Period"
                      yAxisTitle={`Dividend Amount (${currency === 'GBP' ? '£' : currency === 'USD' ? '$' : '€'})`}
                      currency={currency === 'GBP' ? '£' : currency === 'USD' ? '$' : '€'}
                      showTextLabels={false}
                    />
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                    <BarChart3 className="h-12 w-12 mb-4 opacity-20" />
                    <p>No data available for selected filters</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Monthly Income Coverage Analysis */}
        <div className="animate-enter" style={{ animationDelay: '300ms' }}>
          <Card className="overflow-hidden">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                  <Target className="h-5 w-5 text-emerald-500" />
                </div>
                <div>
                  <CardTitle className="text-lg">Financial Independence Tracker</CardTitle>
                  <CardDescription>Track how much of your expenses are covered by dividends</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Expense Input */}
              <div className="max-w-sm space-y-2">
                <Label htmlFor="expenses" className="text-sm text-muted-foreground">Your Monthly Expenses</Label>
                <div className="relative">
                  <Wallet className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="expenses"
                    type="number"
                    value={monthlyExpenses}
                    onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                    className="pl-10 h-11"
                    min={0}
                    step={100}
                  />
                </div>
              </div>

              {/* Coverage Stats */}
              {coverageLoading ? (
                <div className="grid gap-4 md:grid-cols-4">
                  {[...Array(4)].map((_, i) => (
                    <Skeleton key={i} className="h-28 rounded-xl" />
                  ))}
                </div>
              ) : coverageData ? (
                <>
                  {/* Progress Section */}
                  <div className="p-6 rounded-2xl bg-gradient-to-br from-muted/50 to-muted/20 border border-border/50">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Coverage for</p>
                        <p className="text-xl font-serif">{coverageData.month_name}</p>
                      </div>
                      <div className={cn(
                        "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium",
                        coverageData.coverage_percent >= 100
                          ? "bg-emerald-500/10 text-emerald-500"
                          : coverageData.coverage_percent >= 50
                          ? "bg-amber-500/10 text-amber-500"
                          : "bg-red-500/10 text-red-500"
                      )}>
                        {coverageData.coverage_percent >= 100 ? (
                          <CheckCircle2 className="h-4 w-4" />
                        ) : (
                          <AlertCircle className="h-4 w-4" />
                        )}
                        {coverageData.coverage_percent.toFixed(1)}% covered
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="space-y-2">
                      <div className="progress-bar h-3 rounded-full">
                        <div
                          className={cn(
                            "h-full rounded-full transition-all duration-1000",
                            coverageData.coverage_percent >= 100
                              ? "bg-gradient-to-r from-emerald-500 to-emerald-400"
                              : coverageData.coverage_percent >= 50
                              ? "bg-gradient-to-r from-amber-500 to-amber-400"
                              : "bg-gradient-to-r from-red-500 to-red-400"
                          )}
                          style={{ width: `${Math.min(coverageData.coverage_percent, 100)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>0%</span>
                        <span>50%</span>
                        <span>100%</span>
                      </div>
                    </div>
                  </div>

                  {/* Metric Cards */}
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="p-4 rounded-xl border metric-positive bg-card">
                      <div className="flex items-center gap-3">
                        <Target className="h-4 w-4 text-muted-foreground" />
                        <div className="flex-1">
                          <p className="text-sm text-muted-foreground">Current Coverage</p>
                          <p className="text-2xl font-semibold text-gradient">
                            {coverageData.coverage_percent.toFixed(1)}%
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border metric-neutral bg-card">
                      <div className="flex items-center gap-3">
                        <Wallet className="h-4 w-4 text-muted-foreground" />
                        <div className="flex-1">
                          <p className="text-sm text-muted-foreground">Amount Received</p>
                          <p className="text-2xl font-semibold">
                            {formatCurrency(coverageData.amount_received, currency)}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border metric-neutral bg-card">
                      <div className="flex items-center gap-3">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <div className="flex-1">
                          <p className="text-sm text-muted-foreground">Monthly Average</p>
                          <p className="text-2xl font-semibold">
                            {formatCurrency(coverageData.monthly_average, currency)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {coverageData.gap_amount > 0 && (
                      <div className="p-4 rounded-xl border metric-negative bg-card">
                        <div className="flex items-center gap-3">
                          <AlertCircle className="h-4 w-4 text-muted-foreground" />
                          <div className="flex-1">
                            <p className="text-sm text-muted-foreground">Gap to 100%</p>
                            <p className="text-2xl font-semibold text-red-500">
                              {formatCurrency(coverageData.gap_amount, currency)}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="py-12 text-center text-muted-foreground">
                  <Target className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p>No coverage data available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
