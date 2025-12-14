'use client';

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
import { Calendar, Target, DollarSign } from 'lucide-react';

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
        <div className="flex items-center justify-center h-full">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="text-destructive">Error Loading Data</CardTitle>
              <CardDescription>
                Failed to load monthly analysis data.
              </CardDescription>
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
          <h1 className="text-3xl font-bold tracking-tight">Monthly Analysis</h1>
          <p className="text-muted-foreground">
            Analyze dividend income patterns across months and years
          </p>
        </div>

        {/* Monthly Dividends by Year - Line Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Monthly Dividends by Year</CardTitle>
            <CardDescription>Compare dividend income across different years</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[400px] w-full" />
            ) : plotlyLineData.length > 0 ? (
              <PlotlyLineChart
                data={plotlyLineData}
                height={400}
                xAxisTitle="Month"
                yAxisTitle={`Dividend Amount (${currency})`}
                showMarkers={true}
                curveType="spline"
              />
            ) : (
              <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                No data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Monthly Heatmap */}
        <Card>
          <CardHeader>
            <CardTitle>Monthly Dividend Heatmap</CardTitle>
            <CardDescription>Year x Month matrix showing dividend amounts</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[400px] w-full" />
            ) : data?.heatmap ? (
              <PlotlyHeatmap
                data={data.heatmap.data}
                rows={data.heatmap.rows}
                cols={data.heatmap.cols}
                height={400}
                colorScale="blues"
                showValues={true}
                currency={currency === 'GBP' ? '£' : currency === 'USD' ? '$' : '€'}
              />
            ) : (
              <div className="h-[400px] flex items-center justify-center text-muted-foreground">
                No data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Company Breakdown Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Dividends by Company
            </CardTitle>
            <CardDescription>
              Filter by company or month to see detailed breakdowns
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Filters */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Filter by Companies</Label>
                <Select
                  value={selectedCompanies.length > 0 ? selectedCompanies[0] : 'all'}
                  onValueChange={(value) =>
                    setSelectedCompanies(value === 'all' ? [] : [value])
                  }
                >
                  <SelectTrigger>
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
                <Label>Filter by Month</Label>
                <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                  <SelectTrigger>
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
                <div className="flex items-center justify-center h-full">
                  <Skeleton className="h-full w-full" />
                </div>
              ) : plotlyStackedData.series.length > 0 ? (
                <PlotlyStackedBarChart
                  data={plotlyStackedData}
                  height={500}
                  xAxisTitle="Period"
                  yAxisTitle={`Dividend Amount (${currency === 'GBP' ? '£' : currency === 'USD' ? '$' : '€'})`}
                  currency={currency === 'GBP' ? '£' : currency === 'USD' ? '$' : '€'}
                  showTextLabels={false}
                />
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  No data available for selected filters
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Monthly Income Coverage Analysis */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Monthly Income Coverage Analysis
            </CardTitle>
            <CardDescription>
              See how much of your monthly expenses are covered by dividends
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Expense Input */}
            <div className="max-w-xs space-y-2">
              <Label htmlFor="expenses">Your Monthly Expenses</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="expenses"
                  type="number"
                  value={monthlyExpenses}
                  onChange={(e) => setMonthlyExpenses(Number(e.target.value))}
                  className="pl-10"
                  min={0}
                  step={100}
                />
              </div>
            </div>

            {/* Coverage Stats */}
            {coverageLoading ? (
              <div className="grid gap-4 md:grid-cols-4">
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-24" />
                ))}
              </div>
            ) : coverageData ? (
              <>
                {/* Coverage Period */}
                <div className="text-lg font-medium">
                  Coverage for: <span className="text-primary">{coverageData.month_name}</span>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress to 100% coverage</span>
                    <span className="font-medium">{coverageData.coverage_percent.toFixed(1)}%</span>
                  </div>
                  <div className="h-4 w-full bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-500"
                      style={{ width: `${Math.min(coverageData.coverage_percent, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Metric Cards */}
                <div className="grid gap-4 md:grid-cols-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold text-primary">
                        {coverageData.coverage_percent.toFixed(1)}%
                      </div>
                      <p className="text-sm text-muted-foreground">Current Coverage</p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold">
                        {formatCurrency(coverageData.amount_received, currency)}
                      </div>
                      <p className="text-sm text-muted-foreground">Amount Received</p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold">
                        {formatCurrency(coverageData.monthly_average, currency)}
                      </div>
                      <p className="text-sm text-muted-foreground">Monthly Average</p>
                    </CardContent>
                  </Card>

                  {coverageData.gap_amount > 0 && (
                    <Card>
                      <CardContent className="pt-6">
                        <div className="text-2xl font-bold text-destructive">
                          {formatCurrency(coverageData.gap_amount, currency)}
                        </div>
                        <p className="text-sm text-muted-foreground">Gap to 100%</p>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </>
            ) : (
              <p className="text-muted-foreground">No coverage data available</p>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
