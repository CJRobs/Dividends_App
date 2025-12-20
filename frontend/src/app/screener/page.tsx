'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Search,
  Building2,
  TrendingUp,
  DollarSign,
  BarChart3,
  PieChart,
  AlertTriangle,
  Info,
  Shield,
  Activity,
  Percent,
  Scale,
  Zap,
  Wallet,
} from 'lucide-react';
import { formatPercentage, formatLargeNumber } from '@/lib/constants';
import api from '@/lib/api';

// Plotly Charts
import {
  PlotlyDualAxisChart,
  PlotlyCashFlowChart,
  PlotlyGroupedBarChart,
} from '@/components/charts/plotly';
import { PlotlyLineChart } from '@/components/charts/PlotlyLineChart';

interface CompanyOverview {
  symbol: string;
  name: string;
  description?: string;
  sector?: string;
  industry?: string;
  market_cap?: number;
  pe_ratio?: number;
  dividend_yield?: number;
  dividend_per_share?: number;
  eps?: number;
  beta?: number;
  fifty_two_week_high?: number;
  fifty_two_week_low?: number;
  forward_pe?: number;
  peg_ratio?: number;
  book_value?: number;
  profit_margin?: number;
  operating_margin?: number;
  return_on_equity?: number;
  revenue_ttm?: number;
  gross_profit_ttm?: number;
  ex_dividend_date?: string;
  payout_ratio?: number;
}

interface DividendHistory {
  ex_date: string;
  amount: number;
  payment_date?: string;
}

interface IncomeStatement {
  fiscal_date: string;
  total_revenue?: number;
  gross_profit?: number;
  operating_income?: number;
  net_income?: number;
  ebitda?: number;
}

interface BalanceSheet {
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

interface CashFlow {
  fiscal_date: string;
  operating_cashflow?: number;
  capital_expenditure?: number;
  free_cashflow?: number;
  dividend_payout?: number;
}

interface DividendMetrics {
  dividend_growth_rate?: number;
  fcf_coverage_ratio?: number;
  consecutive_growth_years?: number;
  dividend_consistency?: string;
  avg_dividend_amount?: number;
  total_dividends_paid?: number;
}

interface RiskFactors {
  yield_risk?: number;
  payout_risk?: number;
  valuation_risk?: number;
  leverage_risk?: number;
  volatility_risk?: number;
  coverage_risk?: number;
}

interface ScreenerAnalysis {
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
}

export default function ScreenerPage() {
  const [symbol, setSymbol] = useState('');
  const [searchSymbol, setSearchSymbol] = useState('');

  const { data: analysis, isLoading, error } = useQuery<ScreenerAnalysis>({
    queryKey: ['screener-analysis', searchSymbol],
    queryFn: () => api.get(`/api/screener/analysis/${searchSymbol}`).then(res => res.data),
    enabled: !!searchSymbol,
    retry: false,
  });

  const handleSearch = () => {
    if (symbol.trim()) {
      setSearchSymbol(symbol.trim().toUpperCase());
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const getRiskColor = (level?: string) => {
    switch (level) {
      case 'Low': return 'text-green-400';
      case 'Medium': return 'text-yellow-400';
      case 'High': return 'text-red-400';
      default: return 'text-muted-foreground';
    }
  };

  const getRiskBadgeVariant = (level?: string): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (level) {
      case 'Low': return 'default';
      case 'Medium': return 'secondary';
      case 'High': return 'destructive';
      default: return 'outline';
    }
  };

  const getGradeColor = (grade?: string) => {
    switch (grade) {
      case 'A': return 'text-green-400 bg-green-400/10';
      case 'B': return 'text-blue-400 bg-blue-400/10';
      case 'C': return 'text-yellow-400 bg-yellow-400/10';
      case 'D': return 'text-orange-400 bg-orange-400/10';
      case 'F': return 'text-red-400 bg-red-400/10';
      default: return 'text-muted-foreground bg-muted';
    }
  };

  const getRiskFactorColor = (score?: number) => {
    if (score === undefined) return 'bg-muted';
    if (score <= 30) return 'bg-green-500';
    if (score <= 50) return 'bg-yellow-500';
    if (score <= 70) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getRatioColor = (value?: number, goodThreshold: number = 1.5, badThreshold: number = 1.0) => {
    if (value === undefined) return 'text-muted-foreground';
    if (value >= goodThreshold) return 'text-green-400';
    if (value >= badThreshold) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dividend Screener</h1>
          <p className="text-muted-foreground">
            Research and analyze individual stocks using Alpha Vantage data
          </p>
        </div>

        {/* Search Bar */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Search Stock</CardTitle>
            <CardDescription>
              Enter a stock ticker symbol to analyze (e.g., AAPL, MSFT, JNJ)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Input
                placeholder="Enter ticker symbol..."
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                onKeyPress={handleKeyPress}
                className="max-w-xs"
              />
              <Button onClick={handleSearch} disabled={!symbol.trim() || isLoading}>
                <Search className="h-4 w-4 mr-2" />
                {isLoading ? 'Analyzing...' : 'Analyze'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Error State */}
        {error && (
          <Card className="border-destructive">
            <CardContent className="py-6">
              <div className="flex items-center gap-3 text-destructive">
                <AlertTriangle className="h-5 w-5" />
                <span>
                  {error instanceof Error
                    ? error.message.includes('404')
                      ? `No data found for symbol: ${searchSymbol}`
                      : error.message
                    : 'Failed to fetch stock data'}
                </span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-4">
            <Skeleton className="h-[200px] w-full" />
            <Skeleton className="h-[400px] w-full" />
          </div>
        )}

        {/* Analysis Results */}
        {analysis && (
          <>
            {/* Company Profile */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Building2 className="h-5 w-5" />
                      {analysis.overview.name}
                      <Badge variant="outline">{analysis.overview.symbol}</Badge>
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {analysis.overview.sector} • {analysis.overview.industry}
                    </CardDescription>
                  </div>
                  {analysis.risk_level && (
                    <Badge variant={getRiskBadgeVariant(analysis.risk_level)}>
                      {analysis.risk_level} Risk
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {/* Key Metrics Grid - Expanded to 12 metrics */}
                <div className="grid gap-4 grid-cols-2 md:grid-cols-4 lg:grid-cols-6">
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Market Cap</p>
                    <p className="text-lg font-semibold">
                      {analysis.overview.market_cap
                        ? formatLargeNumber(analysis.overview.market_cap)
                        : 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">P/E Ratio</p>
                    <p className="text-lg font-semibold">
                      {analysis.overview.pe_ratio?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Dividend Yield</p>
                    <p className="text-lg font-semibold text-green-400">
                      {analysis.overview.dividend_yield
                        ? formatPercentage(analysis.overview.dividend_yield * 100)
                        : 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">EPS</p>
                    <p className="text-lg font-semibold">
                      ${analysis.overview.eps?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">52W High</p>
                    <p className="text-lg font-semibold">
                      ${analysis.overview.fifty_two_week_high?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">52W Low</p>
                    <p className="text-lg font-semibold">
                      ${analysis.overview.fifty_two_week_low?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                  {/* New metrics row */}
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Beta</p>
                    <p className={`text-lg font-semibold ${
                      analysis.overview.beta && analysis.overview.beta > 1.5
                        ? 'text-red-400'
                        : analysis.overview.beta && analysis.overview.beta < 0.8
                        ? 'text-green-400'
                        : ''
                    }`}>
                      {analysis.overview.beta?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Forward P/E</p>
                    <p className="text-lg font-semibold">
                      {analysis.overview.forward_pe?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">PEG Ratio</p>
                    <p className={`text-lg font-semibold ${
                      analysis.overview.peg_ratio && analysis.overview.peg_ratio < 1
                        ? 'text-green-400'
                        : analysis.overview.peg_ratio && analysis.overview.peg_ratio > 2
                        ? 'text-red-400'
                        : ''
                    }`}>
                      {analysis.overview.peg_ratio?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Book Value</p>
                    <p className="text-lg font-semibold">
                      ${analysis.overview.book_value?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Payout Ratio</p>
                    <p className={`text-lg font-semibold ${
                      analysis.overview.payout_ratio && analysis.overview.payout_ratio > 0.9
                        ? 'text-red-400'
                        : analysis.overview.payout_ratio && analysis.overview.payout_ratio < 0.6
                        ? 'text-green-400'
                        : 'text-yellow-400'
                    }`}>
                      {analysis.overview.payout_ratio
                        ? formatPercentage(analysis.overview.payout_ratio * 100)
                        : 'N/A'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Ex-Dividend</p>
                    <p className="text-lg font-semibold">
                      {analysis.overview.ex_dividend_date || 'N/A'}
                    </p>
                  </div>
                </div>

                {/* Company Description */}
                {analysis.overview.description && (
                  <div className="mt-6 pt-4 border-t">
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {analysis.overview.description}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Key Ratios Section */}
            <div className="grid gap-4 md:grid-cols-2">
              {/* Liquidity Ratios */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Scale className="h-4 w-4" />
                    Liquidity Ratios
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Current Ratio</p>
                      <p className={`text-xl font-semibold ${getRatioColor(analysis.balance_sheets[0]?.current_ratio, 2.0, 1.0)}`}>
                        {analysis.balance_sheets[0]?.current_ratio?.toFixed(2) || 'N/A'}
                      </p>
                      <p className="text-xs text-muted-foreground">Target: &gt;1.5</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Quick Ratio</p>
                      <p className={`text-xl font-semibold ${getRatioColor(analysis.balance_sheets[0]?.quick_ratio, 1.5, 1.0)}`}>
                        {analysis.balance_sheets[0]?.quick_ratio?.toFixed(2) || 'N/A'}
                      </p>
                      <p className="text-xs text-muted-foreground">Target: &gt;1.0</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Debt/Equity</p>
                      <p className={`text-xl font-semibold ${
                        analysis.balance_sheets[0]?.debt_to_equity !== undefined
                          ? analysis.balance_sheets[0].debt_to_equity < 0.5
                            ? 'text-green-400'
                            : analysis.balance_sheets[0].debt_to_equity < 1.5
                            ? 'text-yellow-400'
                            : 'text-red-400'
                          : 'text-muted-foreground'
                      }`}>
                        {analysis.balance_sheets[0]?.debt_to_equity?.toFixed(2) || 'N/A'}
                      </p>
                      <p className="text-xs text-muted-foreground">Target: &lt;1.0</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Dividend Health */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Wallet className="h-4 w-4" />
                    Dividend Health
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">FCF Coverage</p>
                      <p className={`text-xl font-semibold ${getRatioColor(analysis.dividend_metrics?.fcf_coverage_ratio, 2.0, 1.2)}`}>
                        {analysis.dividend_metrics?.fcf_coverage_ratio?.toFixed(2) || 'N/A'}x
                      </p>
                      <p className="text-xs text-muted-foreground">Target: &gt;1.5x</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Div Growth</p>
                      <p className={`text-xl font-semibold ${
                        analysis.dividend_metrics?.dividend_growth_rate != null
                          ? analysis.dividend_metrics.dividend_growth_rate > 5
                            ? 'text-green-400'
                            : analysis.dividend_metrics.dividend_growth_rate > 0
                            ? 'text-yellow-400'
                            : 'text-red-400'
                          : 'text-muted-foreground'
                      }`}>
                        {analysis.dividend_metrics?.dividend_growth_rate != null
                          ? `${analysis.dividend_metrics.dividend_growth_rate > 0 ? '+' : ''}${analysis.dividend_metrics.dividend_growth_rate.toFixed(1)}%`
                          : 'N/A'}
                      </p>
                      <p className="text-xs text-muted-foreground">Avg annual</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Consistency</p>
                      <p className={`text-xl font-semibold ${
                        analysis.dividend_metrics?.dividend_consistency === 'Excellent'
                          ? 'text-green-400'
                          : analysis.dividend_metrics?.dividend_consistency === 'Good'
                          ? 'text-blue-400'
                          : analysis.dividend_metrics?.dividend_consistency === 'Fair'
                          ? 'text-yellow-400'
                          : 'text-muted-foreground'
                      }`}>
                        {analysis.dividend_metrics?.dividend_consistency || 'N/A'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {analysis.dividend_metrics?.consecutive_growth_years !== undefined
                          ? `${analysis.dividend_metrics.consecutive_growth_years} yr streak`
                          : ''}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Analysis Tabs */}
            <Tabs defaultValue="income" className="space-y-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="income">Income Statement</TabsTrigger>
                <TabsTrigger value="balance">Balance Sheet</TabsTrigger>
                <TabsTrigger value="cashflow">Cash Flow</TabsTrigger>
                <TabsTrigger value="dividends">Dividends</TabsTrigger>
              </TabsList>

              {/* Income Statement Tab */}
              <TabsContent value="income" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5" />
                      Revenue & Profitability
                    </CardTitle>
                    <CardDescription>
                      Revenue bars with Gross Profit and Net Income trend lines
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {analysis.income_statements.length > 0 ? (
                      <>
                        <PlotlyDualAxisChart
                          bars={[{
                            x: analysis.income_statements.slice().reverse().map(is => is.fiscal_date.substring(0, 4)),
                            y: analysis.income_statements.slice().reverse().map(is => (is.total_revenue || 0) / 1e9),
                            name: 'Total Revenue',
                            color: '#4e8df5',
                            yaxis: 'y',
                          }]}
                          lines={[
                            {
                              x: analysis.income_statements.slice().reverse().map(is => is.fiscal_date.substring(0, 4)),
                              y: analysis.income_statements.slice().reverse().map(is => (is.gross_profit || 0) / 1e9),
                              name: 'Gross Profit',
                              color: '#22c55e',
                              yaxis: 'y2',
                            },
                            {
                              x: analysis.income_statements.slice().reverse().map(is => is.fiscal_date.substring(0, 4)),
                              y: analysis.income_statements.slice().reverse().map(is => (is.net_income || 0) / 1e9),
                              name: 'Net Income',
                              color: '#f59e0b',
                              yaxis: 'y2',
                            },
                          ]}
                          height={400}
                          yAxisTitle="Revenue ($B)"
                          y2AxisTitle="Profit ($B)"
                        />
                        <div className="mt-4 grid gap-4 md:grid-cols-3">
                          <div className="p-4 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">Profit Margin</p>
                            <p className="text-xl font-semibold">
                              {analysis.overview.profit_margin
                                ? formatPercentage(analysis.overview.profit_margin * 100)
                                : 'N/A'}
                            </p>
                          </div>
                          <div className="p-4 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">Operating Margin</p>
                            <p className="text-xl font-semibold">
                              {analysis.overview.operating_margin
                                ? formatPercentage(analysis.overview.operating_margin * 100)
                                : 'N/A'}
                            </p>
                          </div>
                          <div className="p-4 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">Return on Equity</p>
                            <p className="text-xl font-semibold">
                              {analysis.overview.return_on_equity
                                ? formatPercentage(analysis.overview.return_on_equity * 100)
                                : 'N/A'}
                            </p>
                          </div>
                        </div>
                      </>
                    ) : (
                      <p className="text-muted-foreground text-center py-8">
                        No income statement data available
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Balance Sheet Tab */}
              <TabsContent value="balance" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <PieChart className="h-5 w-5" />
                      Balance Sheet Overview
                    </CardTitle>
                    <CardDescription>
                      Assets, Liabilities, and Shareholders Equity comparison
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {analysis.balance_sheets.length > 0 ? (
                      <>
                        <PlotlyGroupedBarChart
                          data={{
                            categories: analysis.balance_sheets.slice().reverse().map(bs => bs.fiscal_date.substring(0, 4)),
                            series: [
                              {
                                name: 'Total Assets',
                                values: analysis.balance_sheets.slice().reverse().map(bs => (bs.total_assets || 0) / 1e9),
                                color: '#3b82f6',
                              },
                              {
                                name: 'Total Liabilities',
                                values: analysis.balance_sheets.slice().reverse().map(bs => (bs.total_liabilities || 0) / 1e9),
                                color: '#ef4444',
                              },
                              {
                                name: 'Shareholders Equity',
                                values: analysis.balance_sheets.slice().reverse().map(bs => (bs.total_equity || 0) / 1e9),
                                color: '#22c55e',
                              },
                            ],
                          }}
                          height={400}
                          yAxisTitle="Amount ($ Billions)"
                        />
                        <div className="mt-4 grid gap-4 md:grid-cols-3">
                          {analysis.balance_sheets[0] && (
                            <>
                              <div className="p-4 bg-muted rounded-lg">
                                <p className="text-xs text-muted-foreground">Total Equity</p>
                                <p className="text-xl font-semibold">
                                  {analysis.balance_sheets[0].total_equity
                                    ? formatLargeNumber(analysis.balance_sheets[0].total_equity)
                                    : 'N/A'}
                                </p>
                              </div>
                              <div className="p-4 bg-muted rounded-lg">
                                <p className="text-xs text-muted-foreground">Total Debt</p>
                                <p className="text-xl font-semibold">
                                  {analysis.balance_sheets[0].total_debt
                                    ? formatLargeNumber(analysis.balance_sheets[0].total_debt)
                                    : 'N/A'}
                                </p>
                              </div>
                              <div className="p-4 bg-muted rounded-lg">
                                <p className="text-xs text-muted-foreground">Cash & Equivalents</p>
                                <p className="text-xl font-semibold">
                                  {analysis.balance_sheets[0].cash_and_equivalents
                                    ? formatLargeNumber(analysis.balance_sheets[0].cash_and_equivalents)
                                    : 'N/A'}
                                </p>
                              </div>
                            </>
                          )}
                        </div>
                      </>
                    ) : (
                      <p className="text-muted-foreground text-center py-8">
                        No balance sheet data available
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Cash Flow Tab */}
              <TabsContent value="cashflow" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5" />
                      Free Cash Flow vs Dividends vs CapEx
                    </CardTitle>
                    <CardDescription>
                      Shows how free cash flow compares to dividend payouts and capital expenditures
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {analysis.cash_flows.length > 0 ? (
                      <>
                        <PlotlyCashFlowChart
                          years={analysis.cash_flows.slice().reverse().map(cf => cf.fiscal_date.substring(0, 4))}
                          fcf={analysis.cash_flows.slice().reverse().map(cf => (cf.free_cashflow || 0) / 1e9)}
                          dividends={analysis.cash_flows.slice().reverse().map(cf => Math.abs(cf.dividend_payout || 0) / 1e9)}
                          capex={analysis.cash_flows.slice().reverse().map(cf => Math.abs(cf.capital_expenditure || 0) / 1e9)}
                          height={400}
                        />
                        <div className="mt-4 grid gap-4 md:grid-cols-3">
                          {analysis.cash_flows[0] && (
                            <>
                              <div className="p-4 bg-muted rounded-lg">
                                <p className="text-xs text-muted-foreground">Free Cash Flow</p>
                                <p className="text-xl font-semibold text-blue-400">
                                  {analysis.cash_flows[0].free_cashflow
                                    ? formatLargeNumber(analysis.cash_flows[0].free_cashflow)
                                    : 'N/A'}
                                </p>
                              </div>
                              <div className="p-4 bg-muted rounded-lg">
                                <p className="text-xs text-muted-foreground">Dividend Payout</p>
                                <p className="text-xl font-semibold text-green-400">
                                  {analysis.cash_flows[0].dividend_payout
                                    ? formatLargeNumber(Math.abs(analysis.cash_flows[0].dividend_payout))
                                    : 'N/A'}
                                </p>
                              </div>
                              <div className="p-4 bg-muted rounded-lg">
                                <p className="text-xs text-muted-foreground">Capital Expenditure</p>
                                <p className="text-xl font-semibold text-red-400">
                                  {analysis.cash_flows[0].capital_expenditure
                                    ? formatLargeNumber(Math.abs(analysis.cash_flows[0].capital_expenditure))
                                    : 'N/A'}
                                </p>
                              </div>
                            </>
                          )}
                        </div>
                      </>
                    ) : (
                      <p className="text-muted-foreground text-center py-8">
                        No cash flow data available
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Dividends Tab */}
              <TabsContent value="dividends" className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardDescription>Dividend Yield</CardDescription>
                      <CardTitle className="text-2xl text-green-400">
                        {analysis.overview.dividend_yield
                          ? formatPercentage(analysis.overview.dividend_yield * 100)
                          : 'N/A'}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardDescription>Dividend Per Share</CardDescription>
                      <CardTitle className="text-2xl">
                        ${analysis.overview.dividend_per_share?.toFixed(2) || 'N/A'}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardDescription>Payout Ratio</CardDescription>
                      <CardTitle className="text-2xl">
                        {analysis.overview.payout_ratio
                          ? formatPercentage(analysis.overview.payout_ratio * 100)
                          : 'N/A'}
                      </CardTitle>
                    </CardHeader>
                  </Card>
                </div>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      Dividend History
                    </CardTitle>
                    {analysis.overview.ex_dividend_date && (
                      <CardDescription>
                        Ex-Dividend Date: {analysis.overview.ex_dividend_date}
                      </CardDescription>
                    )}
                  </CardHeader>
                  <CardContent>
                    {analysis.dividends.length > 0 ? (
                      <>
                        <PlotlyLineChart
                          data={{
                            x: analysis.dividends.slice().reverse().map(d => d.ex_date),
                            y: analysis.dividends.slice().reverse().map(d => d.amount),
                            name: 'Dividend Amount',
                          }}
                          height={300}
                          yAxisTitle="Amount ($)"
                          showMarkers={true}
                          curveType="spline"
                        />
                        <div className="mt-4 max-h-48 overflow-y-auto">
                          <table className="w-full text-sm">
                            <thead className="sticky top-0 bg-card">
                              <tr className="border-b">
                                <th className="text-left py-2">Ex-Date</th>
                                <th className="text-right py-2">Amount</th>
                                <th className="text-left py-2">Payment Date</th>
                              </tr>
                            </thead>
                            <tbody>
                              {analysis.dividends.map((d, i) => (
                                <tr key={i} className="border-b border-muted">
                                  <td className="py-2">{d.ex_date}</td>
                                  <td className="text-right py-2">${d.amount.toFixed(4)}</td>
                                  <td className="py-2 text-muted-foreground">
                                    {d.payment_date || '-'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </>
                    ) : (
                      <p className="text-muted-foreground text-center py-8">
                        No dividend history available
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>

            {/* Enhanced Risk Assessment */}
            {analysis.risk_score !== undefined && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Shield className="h-5 w-5" />
                      Risk Assessment
                    </CardTitle>
                    {/* Risk Grade Badge */}
                    {analysis.risk_grade && (
                      <div className={`text-3xl font-bold px-4 py-2 rounded-lg ${getGradeColor(analysis.risk_grade)}`}>
                        {analysis.risk_grade}
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Overall Score Bar */}
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium">Overall Risk Score</span>
                        <span className={`font-semibold ${getRiskColor(analysis.risk_level)}`}>
                          {analysis.risk_score.toFixed(0)}/100
                        </span>
                      </div>
                      <div className="h-3 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all ${
                            analysis.risk_level === 'Low'
                              ? 'bg-green-500'
                              : analysis.risk_level === 'Medium'
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`}
                          style={{ width: `${analysis.risk_score}%` }}
                        />
                      </div>
                    </div>
                    <Badge
                      variant={getRiskBadgeVariant(analysis.risk_level)}
                      className="text-sm px-3 py-1"
                    >
                      {analysis.risk_level} Risk
                    </Badge>
                  </div>

                  {/* Risk Factor Breakdown */}
                  {analysis.risk_factors && (
                    <div className="space-y-3">
                      <p className="text-sm font-medium text-muted-foreground">Risk Factor Breakdown</p>
                      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                        {/* Yield Risk */}
                        <div className="p-3 bg-muted/50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Percent className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">Yield Risk</span>
                            </div>
                            <span className="text-sm font-medium">{analysis.risk_factors.yield_risk?.toFixed(0) || 'N/A'}</span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full ${getRiskFactorColor(analysis.risk_factors.yield_risk)}`}
                              style={{ width: `${analysis.risk_factors.yield_risk || 0}%` }}
                            />
                          </div>
                        </div>

                        {/* Payout Risk */}
                        <div className="p-3 bg-muted/50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <DollarSign className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">Payout Risk</span>
                            </div>
                            <span className="text-sm font-medium">{analysis.risk_factors.payout_risk?.toFixed(0) || 'N/A'}</span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full ${getRiskFactorColor(analysis.risk_factors.payout_risk)}`}
                              style={{ width: `${analysis.risk_factors.payout_risk || 0}%` }}
                            />
                          </div>
                        </div>

                        {/* Valuation Risk */}
                        <div className="p-3 bg-muted/50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <BarChart3 className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">Valuation Risk</span>
                            </div>
                            <span className="text-sm font-medium">{analysis.risk_factors.valuation_risk?.toFixed(0) || 'N/A'}</span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full ${getRiskFactorColor(analysis.risk_factors.valuation_risk)}`}
                              style={{ width: `${analysis.risk_factors.valuation_risk || 0}%` }}
                            />
                          </div>
                        </div>

                        {/* Leverage Risk */}
                        <div className="p-3 bg-muted/50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Scale className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">Leverage Risk</span>
                            </div>
                            <span className="text-sm font-medium">{analysis.risk_factors.leverage_risk?.toFixed(0) || 'N/A'}</span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full ${getRiskFactorColor(analysis.risk_factors.leverage_risk)}`}
                              style={{ width: `${analysis.risk_factors.leverage_risk || 0}%` }}
                            />
                          </div>
                        </div>

                        {/* Volatility Risk */}
                        <div className="p-3 bg-muted/50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Activity className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">Volatility Risk</span>
                            </div>
                            <span className="text-sm font-medium">{analysis.risk_factors.volatility_risk?.toFixed(0) || 'N/A'}</span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full ${getRiskFactorColor(analysis.risk_factors.volatility_risk)}`}
                              style={{ width: `${analysis.risk_factors.volatility_risk || 0}%` }}
                            />
                          </div>
                        </div>

                        {/* Coverage Risk */}
                        <div className="p-3 bg-muted/50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Zap className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">Coverage Risk</span>
                            </div>
                            <span className="text-sm font-medium">{analysis.risk_factors.coverage_risk?.toFixed(0) || 'N/A'}</span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full ${getRiskFactorColor(analysis.risk_factors.coverage_risk)}`}
                              style={{ width: `${analysis.risk_factors.coverage_risk || 0}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Investment Summary */}
                  {analysis.investment_summary && (
                    <div className="p-4 bg-muted rounded-lg">
                      <div className="flex items-start gap-2">
                        <Info className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
                        <p className="text-sm">{analysis.investment_summary}</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* Initial State - Show instructions */}
        {!searchSymbol && !isLoading && (
          <Card className="border-dashed">
            <CardContent className="py-12 text-center">
              <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
              <h3 className="text-lg font-semibold mb-2">Enter a Stock Symbol</h3>
              <p className="text-muted-foreground max-w-md mx-auto">
                Search for any stock to view detailed financial analysis including
                income statements, balance sheets, cash flows, and dividend history.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {['AAPL', 'MSFT', 'JNJ', 'PG', 'KO'].map((ticker) => (
                  <Button
                    key={ticker}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSymbol(ticker);
                      setSearchSymbol(ticker);
                    }}
                  >
                    {ticker}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
