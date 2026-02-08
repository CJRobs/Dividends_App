'use client';

import { useState, useEffect, Suspense } from 'react';
import { useQuery } from '@tanstack/react-query';
import dynamic from 'next/dynamic';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Search,
  Building2,
  TrendingUp,
  DollarSign,
  BarChart3,
  PieChart,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Gauge,
  Shield,
  Activity,
  Percent,
  Wallet,
  Scale,
  Droplets,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatPercentage, formatLargeNumber } from '@/lib/constants';
import api from '@/lib/api';

// Lazy load Plotly charts
const PlotlyDualAxisChart = dynamic(
  () => import('@/components/charts/plotly').then(mod => ({ default: mod.PlotlyDualAxisChart })),
  {
    loading: () => <Skeleton className="h-[400px]" />,
    ssr: false,
  }
);

const PlotlyCashFlowChart = dynamic(
  () => import('@/components/charts/plotly').then(mod => ({ default: mod.PlotlyCashFlowChart })),
  {
    loading: () => <Skeleton className="h-[400px]" />,
    ssr: false,
  }
);

const PlotlyGroupedBarChart = dynamic(
  () => import('@/components/charts/plotly').then(mod => ({ default: mod.PlotlyGroupedBarChart })),
  {
    loading: () => <Skeleton className="h-[400px]" />,
    ssr: false,
  }
);

const PlotlyLineChart = dynamic(
  () => import('@/components/charts/PlotlyLineChart').then(mod => ({ default: mod.PlotlyLineChart })),
  {
    loading: () => <Skeleton className="h-[400px]" />,
    ssr: false,
  }
);

interface CompanyOverview {
  symbol: string;
  name: string;
  description?: string;
  sector?: string;
  industry?: string;
  exchange?: string;
  currency?: string;
  market_cap?: number;
  current_price?: number;
  pe_ratio?: number;
  dividend_yield?: number;
  dividend_per_share?: number;
  eps?: number;
  fifty_two_week_high?: number;
  fifty_two_week_low?: number;
  payout_ratio?: number;
  return_on_equity?: number;
  shares_outstanding?: number;
  book_value?: number;
  ex_dividend_date?: string;
  dividend_date?: string;
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
  long_term_debt?: number;
  current_ratio?: number;
  debt_to_equity?: number;
}

interface CashFlow {
  fiscal_date: string;
  operating_cashflow?: number;
  capital_expenditure?: number;
  free_cashflow?: number;
  dividend_payout?: number;
  investing_cashflow?: number;
  financing_cashflow?: number;
}

interface ScreenerAnalysis {
  overview: CompanyOverview;
  dividends: DividendHistory[];
  income_statements: IncomeStatement[];
  balance_sheets: BalanceSheet[];
  cash_flows: CashFlow[];
}

// Metric Card Component with status indicator
interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  status?: 'good' | 'warning' | 'danger' | 'neutral';
  delay?: number;
}

function MetricCard({ label, value, icon, status = 'neutral', delay = 0 }: MetricCardProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const statusColors = {
    good: 'border-l-green-500 bg-green-500/5',
    warning: 'border-l-yellow-500 bg-yellow-500/5',
    danger: 'border-l-red-500 bg-red-500/5',
    neutral: 'border-l-primary/50 bg-primary/5',
  };

  const valueColors = {
    good: 'text-green-400',
    warning: 'text-yellow-400',
    danger: 'text-red-400',
    neutral: 'text-foreground',
  };

  return (
    <Card className={cn(
      'border-l-4 transition-all duration-500 hover:scale-[1.02] hover:shadow-lg',
      statusColors[status],
      isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
    )}>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm text-muted-foreground flex items-center gap-1.5">
              {icon}
              {label}
            </p>
            <p className={cn('text-2xl font-bold mt-1 number-display', valueColors[status])}>
              {value}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Visual Risk Meter Component
interface RiskMeterProps {
  score: number;
  level: string;
  animated?: boolean;
}

function RiskMeter({ score, level, animated = true }: RiskMeterProps) {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    if (!animated) {
      setDisplayScore(score);
      return;
    }

    const duration = 1000;
    const steps = 60;
    const increment = score / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= score) {
        setDisplayScore(score);
        clearInterval(timer);
      } else {
        setDisplayScore(Math.round(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [score, animated]);

  // Calculate rotation for gauge needle (-90 to 90 degrees)
  const rotation = -90 + (displayScore / 100) * 180;

  const getColor = () => {
    if (score <= 20) return '#22c55e';
    if (score <= 40) return '#84cc16';
    if (score <= 60) return '#eab308';
    if (score <= 80) return '#f97316';
    return '#ef4444';
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-40 h-24 overflow-hidden">
        {/* Gauge background arc */}
        <svg className="w-full h-full" viewBox="0 0 100 50">
          {/* Background arc segments */}
          <path
            d="M 10 50 A 40 40 0 0 1 30 14.2"
            fill="none"
            stroke="#22c55e"
            strokeWidth="8"
            strokeLinecap="round"
            opacity="0.3"
          />
          <path
            d="M 30 14.2 A 40 40 0 0 1 50 10"
            fill="none"
            stroke="#84cc16"
            strokeWidth="8"
            strokeLinecap="round"
            opacity="0.3"
          />
          <path
            d="M 50 10 A 40 40 0 0 1 70 14.2"
            fill="none"
            stroke="#eab308"
            strokeWidth="8"
            strokeLinecap="round"
            opacity="0.3"
          />
          <path
            d="M 70 14.2 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="#ef4444"
            strokeWidth="8"
            strokeLinecap="round"
            opacity="0.3"
          />
          {/* Active arc */}
          <path
            d={`M 10 50 A 40 40 0 ${displayScore > 50 ? 1 : 0} 1 ${
              50 + 40 * Math.sin((displayScore / 100) * Math.PI)
            } ${50 - 40 * Math.cos((displayScore / 100) * Math.PI)}`}
            fill="none"
            stroke={getColor()}
            strokeWidth="8"
            strokeLinecap="round"
            style={{
              transition: 'stroke 0.3s ease',
            }}
          />
          {/* Needle */}
          <g
            style={{
              transform: `rotate(${rotation}deg)`,
              transformOrigin: '50px 50px',
              transition: animated ? 'transform 1s cubic-bezier(0.34, 1.56, 0.64, 1)' : 'none',
            }}
          >
            <line
              x1="50"
              y1="50"
              x2="50"
              y2="18"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <circle cx="50" cy="50" r="4" fill="currentColor" />
          </g>
        </svg>
      </div>
      <div className="text-center mt-2">
        <span className="text-3xl font-bold number-display" style={{ color: getColor() }}>
          {displayScore}
        </span>
        <span className="text-lg text-muted-foreground">/100</span>
      </div>
      <Badge
        variant={level === 'Low' ? 'default' : level === 'Moderate' ? 'secondary' : 'destructive'}
        className="mt-2"
      >
        {level} Risk
      </Badge>
    </div>
  );
}

export default function ScreenerPage() {
  const [symbol, setSymbol] = useState('');
  const [searchSymbol, setSearchSymbol] = useState('');
  const [timePeriod, setTimePeriod] = useState('5');
  const [showDetails, setShowDetails] = useState(false);

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

  // Filter data based on time period
  const cutoffYear = new Date().getFullYear() - parseInt(timePeriod);

  const filterByYear = <T extends { fiscal_date: string }>(data: T[]): T[] => {
    if (timePeriod === 'all') return data;
    return data.filter(item => {
      const year = parseInt(item.fiscal_date.substring(0, 4));
      return year >= cutoffYear;
    });
  };

  // Calculate metrics from overview data
  const getPayoutRatio = () => {
    if (!analysis?.overview) return 0;
    const eps = analysis.overview.eps || 0;
    const dps = analysis.overview.dividend_per_share || 0;
    if (eps > 0 && dps > 0) {
      return (dps / eps) * 100;
    }
    return (analysis.overview.payout_ratio || 0) * 100;
  };

  // Calculate current ratio from balance sheet
  const getCurrentRatio = () => {
    if (!analysis?.balance_sheets?.[0]) return 0;
    const bs = analysis.balance_sheets[0];
    if (bs.current_ratio) return bs.current_ratio;
    if (bs.current_assets && bs.current_liabilities && bs.current_liabilities > 0) {
      return bs.current_assets / bs.current_liabilities;
    }
    return 0;
  };

  // Calculate debt to equity from balance sheet
  const getDebtToEquity = () => {
    if (!analysis?.balance_sheets?.[0]) return 0;
    const bs = analysis.balance_sheets[0];
    if (bs.debt_to_equity) return bs.debt_to_equity;
    if (bs.total_debt && bs.total_equity && bs.total_equity > 0) {
      return bs.total_debt / bs.total_equity;
    }
    return 0;
  };

  // Risk calculation
  const calculateRiskAssessment = () => {
    if (!analysis) return { score: 0, level: 'Unknown', factors: [] };

    let riskScore = 0;
    const riskFactors: string[] = [];

    const payoutRatio = getPayoutRatio();
    const debtToEquity = getDebtToEquity();
    const currentRatio = getCurrentRatio();
    const peRatio = analysis.overview.pe_ratio || 0;

    if (payoutRatio > 80) {
      riskScore += 20;
      riskFactors.push('High payout ratio (>80%)');
    } else if (payoutRatio > 60) {
      riskScore += 10;
      riskFactors.push('Moderate payout ratio (60-80%)');
    }

    if (debtToEquity > 1.5) {
      riskScore += 20;
      riskFactors.push('High debt-to-equity ratio');
    } else if (debtToEquity > 1.0) {
      riskScore += 10;
      riskFactors.push('Moderate debt levels');
    }

    if (currentRatio < 1.0 && currentRatio > 0) {
      riskScore += 15;
      riskFactors.push('Poor liquidity (current ratio < 1.0)');
    } else if (currentRatio < 1.2 && currentRatio > 0) {
      riskScore += 8;
      riskFactors.push('Tight liquidity');
    }

    if (peRatio > 30) {
      riskScore += 10;
      riskFactors.push('High valuation (P/E > 30)');
    }

    let level = 'Low';
    if (riskScore > 40) level = 'High';
    else if (riskScore > 20) level = 'Moderate';

    return { score: riskScore, level, factors: riskFactors };
  };

  // Investment summary calculation
  const calculateInvestmentSummary = () => {
    if (!analysis) return { score: 0, recommendation: 'Unknown', strengths: [], considerations: [] };

    const risk = calculateRiskAssessment();
    let investmentScore = 100 - risk.score;
    const strengths: string[] = [];
    const considerations: string[] = [];

    const dividendYield = (analysis.overview.dividend_yield || 0) * 100;
    const payoutRatio = getPayoutRatio();
    const roe = (analysis.overview.return_on_equity || 0) * 100;
    const currentRatio = getCurrentRatio();
    const peRatio = analysis.overview.pe_ratio || 0;
    const debtToEquity = getDebtToEquity();

    // Adjust based on dividend attractiveness
    if (dividendYield >= 4) {
      investmentScore += 10;
      strengths.push('High dividend yield');
    } else if (dividendYield >= 2) {
      investmentScore += 5;
    }

    // Adjust based on profitability
    if (roe >= 15) {
      investmentScore += 10;
      strengths.push('Strong profitability');
    } else if (roe >= 10) {
      investmentScore += 5;
    }

    // Conservative payout
    if (payoutRatio <= 60 && payoutRatio > 0) {
      strengths.push('Conservative payout ratio');
    }

    // Strong liquidity
    if (currentRatio >= 1.5) {
      strengths.push('Strong liquidity');
    }

    // Considerations
    if (peRatio > 25) {
      considerations.push('High valuation');
    }
    if (dividendYield < 2) {
      considerations.push('Low dividend yield');
    }
    if (debtToEquity > 1) {
      considerations.push('High debt levels');
    }

    investmentScore = Math.min(investmentScore, 100);

    let recommendation = 'Avoid';
    if (investmentScore >= 80) recommendation = 'Strong Buy';
    else if (investmentScore >= 70) recommendation = 'Buy';
    else if (investmentScore >= 60) recommendation = 'Hold';
    else if (investmentScore >= 50) recommendation = 'Weak Hold';

    return { score: investmentScore, recommendation, strengths, considerations };
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dividend Stock Analyzer</h1>
          <p className="text-muted-foreground">
            Comprehensive dividend analysis using Alpha Vantage data with detailed financial metrics and visualizations
          </p>
        </div>

        {/* Search Bar - Matches original layout */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex gap-4 items-end">
              <div className="flex-1 max-w-xs">
                <label className="text-sm text-muted-foreground mb-2 block">
                  Enter stock symbol for analysis
                </label>
                <Input
                  placeholder="e.g., AAPL, MSFT, JNJ, KO"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                  onKeyPress={handleKeyPress}
                />
              </div>
              <div className="w-40">
                <label className="text-sm text-muted-foreground mb-2 block">
                  Analysis Period
                </label>
                <Select value={timePeriod} onValueChange={setTimePeriod}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="5">5 Years</SelectItem>
                    <SelectItem value="3">3 Years</SelectItem>
                    <SelectItem value="all">All Available</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={handleSearch} disabled={!symbol.trim() || isLoading}>
                <Search className="h-4 w-4 mr-2" />
                {isLoading ? 'Analyzing...' : 'Analyze Stock'}
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
                      ? `Could not fetch data for symbol: ${searchSymbol}`
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
            {/* Company Profile Section - Enhanced with MetricCards */}
            <div>
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" />
                Company Profile: {analysis.overview.name} ({analysis.overview.symbol})
                {analysis.overview.sector && (
                  <Badge variant="outline" className="ml-2 font-normal">
                    {analysis.overview.sector}
                  </Badge>
                )}
              </h2>

              <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
                {/* Row 1 - Core Metrics */}
                <MetricCard
                  label="Market Cap"
                  value={analysis.overview.market_cap ? formatLargeNumber(analysis.overview.market_cap) : 'N/A'}
                  icon={<Wallet className="h-3.5 w-3.5" />}
                  status="neutral"
                  delay={0}
                />
                <MetricCard
                  label="Current Price"
                  value={analysis.overview.current_price ? `$${analysis.overview.current_price.toFixed(2)}` : 'N/A'}
                  icon={<DollarSign className="h-3.5 w-3.5" />}
                  status="neutral"
                  delay={50}
                />
                <MetricCard
                  label="Dividend Yield"
                  value={analysis.overview.dividend_yield ? formatPercentage(analysis.overview.dividend_yield * 100) : 'N/A'}
                  icon={<Percent className="h-3.5 w-3.5" />}
                  status={
                    !analysis.overview.dividend_yield ? 'neutral' :
                    analysis.overview.dividend_yield * 100 >= 4 ? 'good' :
                    analysis.overview.dividend_yield * 100 >= 2 ? 'neutral' : 'warning'
                  }
                  delay={100}
                />
                <MetricCard
                  label="P/E Ratio"
                  value={analysis.overview.pe_ratio?.toFixed(2) || 'N/A'}
                  icon={<Activity className="h-3.5 w-3.5" />}
                  status={
                    !analysis.overview.pe_ratio ? 'neutral' :
                    analysis.overview.pe_ratio <= 15 ? 'good' :
                    analysis.overview.pe_ratio <= 25 ? 'neutral' :
                    analysis.overview.pe_ratio <= 35 ? 'warning' : 'danger'
                  }
                  delay={150}
                />

                {/* Row 2 - Financial Health */}
                <MetricCard
                  label="Payout Ratio"
                  value={getPayoutRatio() > 0 ? formatPercentage(getPayoutRatio()) : 'N/A'}
                  icon={<TrendingUp className="h-3.5 w-3.5" />}
                  status={
                    getPayoutRatio() <= 0 ? 'neutral' :
                    getPayoutRatio() <= 50 ? 'good' :
                    getPayoutRatio() <= 70 ? 'neutral' :
                    getPayoutRatio() <= 85 ? 'warning' : 'danger'
                  }
                  delay={200}
                />
                <MetricCard
                  label="ROE"
                  value={analysis.overview.return_on_equity ? formatPercentage(analysis.overview.return_on_equity * 100) : 'N/A'}
                  icon={<BarChart3 className="h-3.5 w-3.5" />}
                  status={
                    !analysis.overview.return_on_equity ? 'neutral' :
                    analysis.overview.return_on_equity * 100 >= 15 ? 'good' :
                    analysis.overview.return_on_equity * 100 >= 10 ? 'neutral' : 'warning'
                  }
                  delay={250}
                />
                <MetricCard
                  label="Debt/Equity"
                  value={getDebtToEquity() > 0 ? getDebtToEquity().toFixed(2) : 'N/A'}
                  icon={<Scale className="h-3.5 w-3.5" />}
                  status={
                    getDebtToEquity() <= 0 ? 'neutral' :
                    getDebtToEquity() <= 0.5 ? 'good' :
                    getDebtToEquity() <= 1.0 ? 'neutral' :
                    getDebtToEquity() <= 1.5 ? 'warning' : 'danger'
                  }
                  delay={300}
                />
                <MetricCard
                  label="Current Ratio"
                  value={getCurrentRatio() > 0 ? getCurrentRatio().toFixed(2) : 'N/A'}
                  icon={<Droplets className="h-3.5 w-3.5" />}
                  status={
                    getCurrentRatio() <= 0 ? 'neutral' :
                    getCurrentRatio() >= 1.5 ? 'good' :
                    getCurrentRatio() >= 1.0 ? 'warning' : 'danger'
                  }
                  delay={350}
                />
              </div>
            </div>

            {/* Expandable Detailed Company Information */}
            <Card>
              <CardHeader
                className="cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => setShowDetails(!showDetails)}
              >
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Detailed Company Information
                  </CardTitle>
                  {showDetails ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                </div>
              </CardHeader>
              {showDetails && (
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <p><span className="font-medium">Sector:</span> {analysis.overview.sector || 'N/A'}</p>
                      <p><span className="font-medium">Industry:</span> {analysis.overview.industry || 'N/A'}</p>
                      <p><span className="font-medium">Exchange:</span> {analysis.overview.exchange || 'N/A'}</p>
                      <p><span className="font-medium">Currency:</span> {analysis.overview.currency || 'USD'}</p>
                      <p>
                        <span className="font-medium">Shares Outstanding:</span>{' '}
                        {analysis.overview.shares_outstanding
                          ? analysis.overview.shares_outstanding.toLocaleString()
                          : 'N/A'}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <p>
                        <span className="font-medium">52 Week High:</span>{' '}
                        ${analysis.overview.fifty_two_week_high?.toFixed(2) || 'N/A'}
                      </p>
                      <p>
                        <span className="font-medium">52 Week Low:</span>{' '}
                        ${analysis.overview.fifty_two_week_low?.toFixed(2) || 'N/A'}
                      </p>
                      <p><span className="font-medium">Ex-Dividend Date:</span> {analysis.overview.ex_dividend_date || 'N/A'}</p>
                      <p><span className="font-medium">Dividend Date:</span> {analysis.overview.dividend_date || 'N/A'}</p>
                      <p>
                        <span className="font-medium">Book Value:</span>{' '}
                        ${analysis.overview.book_value?.toFixed(2) || 'N/A'}
                      </p>
                    </div>
                  </div>
                  {analysis.overview.description && (
                    <div className="mt-4 pt-4 border-t">
                      <p className="font-medium mb-2">Company Description:</p>
                      <p className="text-sm text-muted-foreground">
                        {analysis.overview.description.length > 500
                          ? analysis.overview.description.substring(0, 500) + '...'
                          : analysis.overview.description}
                      </p>
                    </div>
                  )}
                </CardContent>
              )}
            </Card>

            {/* Analysis Tabs - Matches original 4 tabs */}
            <Tabs defaultValue="income" className="space-y-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="income">Income Statement</TabsTrigger>
                <TabsTrigger value="balance">Balance Sheet</TabsTrigger>
                <TabsTrigger value="cashflow">Cash Flow</TabsTrigger>
                <TabsTrigger value="dividends">Dividend Info</TabsTrigger>
              </TabsList>

              {/* Debug: Show data counts */}
              {process.env.NODE_ENV === 'development' && (
                <div className="text-xs text-muted-foreground flex gap-4 pl-1">
                  <span>Income Statements: {analysis.income_statements.length}</span>
                  <span>Cash Flows: {analysis.cash_flows.length}</span>
                  <span>Balance Sheets: {analysis.balance_sheets.length}</span>
                </div>
              )}

              {/* Income Statement Tab */}
              <TabsContent value="income" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5" />
                      Income Statement Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {analysis.income_statements.length > 0 ? (
                      <>
                        {/* Revenue and Profitability Chart */}
                        <div className="chart-reveal" style={{ minHeight: '500px' }}>
                          <PlotlyDualAxisChart
                            key={`income-chart-${analysis.overview.symbol}-${timePeriod}`}
                            bars={[{
                              x: filterByYear(analysis.income_statements).slice().reverse().map(is => is.fiscal_date.substring(0, 4)),
                              y: filterByYear(analysis.income_statements).slice().reverse().map(is => (is.total_revenue || 0) / 1e9),
                              name: 'Total Revenue',
                              color: '#4e8df5',
                              yaxis: 'y',
                            }]}
                            lines={[
                              {
                                x: filterByYear(analysis.income_statements).slice().reverse().map(is => is.fiscal_date.substring(0, 4)),
                                y: filterByYear(analysis.income_statements).slice().reverse().map(is => (is.gross_profit || 0) / 1e9),
                                name: 'Gross Profit',
                                color: '#22c55e',
                                yaxis: 'y2',
                              },
                              {
                                x: filterByYear(analysis.income_statements).slice().reverse().map(is => is.fiscal_date.substring(0, 4)),
                                y: filterByYear(analysis.income_statements).slice().reverse().map(is => (is.net_income || 0) / 1e9),
                                name: 'Net Income',
                                color: '#f59e0b',
                                yaxis: 'y2',
                              },
                            ]}
                            title={`Revenue and Profitability - ${analysis.overview.symbol}`}
                            height={500}
                            yAxisTitle="Revenue ($ Billions)"
                            y2AxisTitle="Profit ($ Billions)"
                          />
                        </div>

                        {/* Income Statement Table */}
                        <div className="mt-6">
                          <h3 className="text-lg font-semibold mb-3">Income Statement Summary</h3>
                          <div className="overflow-x-auto rounded-lg border border-border/50">
                            <table className="table-enhanced w-full text-sm">
                              <thead>
                                <tr>
                                  <th className="text-left">Year</th>
                                  <th className="text-right">Revenue ($B)</th>
                                  <th className="text-right">Gross Profit ($B)</th>
                                  <th className="text-right">Operating Income ($B)</th>
                                  <th className="text-right">Net Income ($B)</th>
                                  <th className="text-right">EBITDA ($B)</th>
                                </tr>
                              </thead>
                              <tbody>
                                {filterByYear(analysis.income_statements).slice().reverse().map((is, i) => (
                                  <tr key={i}>
                                    <td className="font-medium">{is.fiscal_date.substring(0, 4)}</td>
                                    <td className="text-right number-display">{((is.total_revenue || 0) / 1e9).toFixed(2)}</td>
                                    <td className="text-right number-display">{((is.gross_profit || 0) / 1e9).toFixed(2)}</td>
                                    <td className="text-right number-display">{((is.operating_income || 0) / 1e9).toFixed(2)}</td>
                                    <td className="text-right number-display">{((is.net_income || 0) / 1e9).toFixed(2)}</td>
                                    <td className="text-right number-display">{((is.ebitda || 0) / 1e9).toFixed(2)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
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
                      Balance Sheet Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {analysis.balance_sheets.length > 0 ? (
                      <>
                        {/* Assets vs Liabilities Chart */}
                        <div className="chart-reveal" style={{ minHeight: '500px' }}>
                          <PlotlyGroupedBarChart
                            key={`balance-chart-${analysis.overview.symbol}-${timePeriod}`}
                            data={{
                              categories: filterByYear(analysis.balance_sheets).slice().reverse().map(bs => bs.fiscal_date.substring(0, 4)),
                              series: [
                                {
                                  name: 'Total Assets',
                                  values: filterByYear(analysis.balance_sheets).slice().reverse().map(bs => (bs.total_assets || 0) / 1e9),
                                  color: '#3b82f6',
                                },
                                {
                                  name: 'Total Liabilities',
                                  values: filterByYear(analysis.balance_sheets).slice().reverse().map(bs => (bs.total_liabilities || 0) / 1e9),
                                  color: '#ef4444',
                                },
                                {
                                  name: 'Shareholders Equity',
                                  values: filterByYear(analysis.balance_sheets).slice().reverse().map(bs => (bs.total_equity || 0) / 1e9),
                                  color: '#22c55e',
                                },
                              ],
                            }}
                            title={`Balance Sheet Overview - ${analysis.overview.symbol}`}
                            height={500}
                            yAxisTitle="Amount ($ Billions)"
                          />
                        </div>

                        {/* Debt Analysis Chart */}
                        <div className="mt-6 chart-reveal" style={{ minHeight: '400px' }}>
                          <PlotlyLineChart
                            key={`debt-chart-${analysis.overview.symbol}-${timePeriod}`}
                            data={[
                              {
                                x: filterByYear(analysis.balance_sheets).slice().reverse().map(bs => bs.fiscal_date.substring(0, 4)),
                                y: filterByYear(analysis.balance_sheets).slice().reverse().map(bs => (bs.long_term_debt || bs.total_debt || 0) / 1e9),
                                name: 'Long-term Debt',
                              },
                              {
                                x: filterByYear(analysis.balance_sheets).slice().reverse().map(bs => bs.fiscal_date.substring(0, 4)),
                                y: filterByYear(analysis.balance_sheets).slice().reverse().map(bs => (bs.cash_and_equivalents || 0) / 1e9),
                                name: 'Cash & Equivalents',
                              },
                            ]}
                            title={`Debt Analysis - ${analysis.overview.symbol}`}
                            height={400}
                            yAxisTitle="Amount ($ Billions)"
                            showMarkers={true}
                          />
                        </div>

                        {/* Balance Sheet Table */}
                        <div className="mt-6">
                          <h3 className="text-lg font-semibold mb-3">Balance Sheet Summary</h3>
                          <div className="overflow-x-auto rounded-lg border border-border/50">
                            <table className="table-enhanced w-full text-sm">
                              <thead>
                                <tr>
                                  <th className="text-left">Year</th>
                                  <th className="text-right">Total Assets ($B)</th>
                                  <th className="text-right">Total Liabilities ($B)</th>
                                  <th className="text-right">Equity ($B)</th>
                                  <th className="text-right">Long-term Debt ($B)</th>
                                  <th className="text-right">Cash ($B)</th>
                                </tr>
                              </thead>
                              <tbody>
                                {filterByYear(analysis.balance_sheets).slice().reverse().map((bs, i) => (
                                  <tr key={i}>
                                    <td className="font-medium">{bs.fiscal_date.substring(0, 4)}</td>
                                    <td className="text-right number-display">{((bs.total_assets || 0) / 1e9).toFixed(2)}</td>
                                    <td className="text-right number-display">{((bs.total_liabilities || 0) / 1e9).toFixed(2)}</td>
                                    <td className="text-right number-display value-positive">{((bs.total_equity || 0) / 1e9).toFixed(2)}</td>
                                    <td className="text-right number-display text-red-400">{((bs.long_term_debt || bs.total_debt || 0) / 1e9).toFixed(2)}</td>
                                    <td className="text-right number-display text-blue-400">{((bs.cash_and_equivalents || 0) / 1e9).toFixed(2)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
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
                      Cash Flow Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {analysis.cash_flows.length > 0 ? (
                      <>
                        {/* Free Cash Flow vs Dividends vs CapEx */}
                        <div className="chart-reveal" style={{ minHeight: '500px' }}>
                          <PlotlyCashFlowChart
                            key={`cashflow-chart-${analysis.overview.symbol}-${timePeriod}`}
                            years={filterByYear(analysis.cash_flows).slice().reverse().map(cf => cf.fiscal_date.substring(0, 4))}
                            fcf={filterByYear(analysis.cash_flows).slice().reverse().map(cf => (cf.free_cashflow || 0) / 1e9)}
                            dividends={filterByYear(analysis.cash_flows).slice().reverse().map(cf => Math.abs(cf.dividend_payout || 0) / 1e9)}
                            capex={filterByYear(analysis.cash_flows).slice().reverse().map(cf => Math.abs(cf.capital_expenditure || 0) / 1e9)}
                            title={`Free Cash Flow vs Dividends & CapEx - ${analysis.overview.symbol}`}
                            height={500}
                          />
                        </div>

                        {/* Cash Flow Coverage Analysis */}
                        {analysis.cash_flows[0] && (
                          <div className="mt-6">
                            <h3 className="text-lg font-semibold mb-3">Cash Flow Coverage Analysis</h3>
                            <div className="grid grid-cols-3 gap-4">
                              <Card>
                                <CardContent className="pt-4 pb-4">
                                  <p className="text-sm text-muted-foreground">Dividend Coverage Ratio</p>
                                  <p className="text-2xl font-bold">
                                    {analysis.cash_flows[0].free_cashflow && analysis.cash_flows[0].dividend_payout
                                      ? `${(Math.abs(analysis.cash_flows[0].free_cashflow) / Math.abs(analysis.cash_flows[0].dividend_payout)).toFixed(2)}x`
                                      : 'N/A'}
                                  </p>
                                </CardContent>
                              </Card>
                              <Card>
                                <CardContent className="pt-4 pb-4">
                                  <p className="text-sm text-muted-foreground">Free Cash Flow</p>
                                  <p className="text-2xl font-bold text-blue-400">
                                    {analysis.cash_flows[0].free_cashflow
                                      ? formatLargeNumber(analysis.cash_flows[0].free_cashflow)
                                      : 'N/A'}
                                  </p>
                                </CardContent>
                              </Card>
                              <Card>
                                <CardContent className="pt-4 pb-4">
                                  <p className="text-sm text-muted-foreground">Dividends Paid</p>
                                  <p className="text-2xl font-bold text-green-400">
                                    {analysis.cash_flows[0].dividend_payout
                                      ? formatLargeNumber(Math.abs(analysis.cash_flows[0].dividend_payout))
                                      : 'N/A'}
                                  </p>
                                </CardContent>
                              </Card>
                            </div>
                          </div>
                        )}

                        {/* Cash Flow Table */}
                        <div className="mt-6">
                          <h3 className="text-lg font-semibold mb-3">Cash Flow Summary</h3>
                          <div className="overflow-x-auto rounded-lg border border-border/50">
                            <table className="table-enhanced w-full text-sm">
                              <thead>
                                <tr>
                                  <th className="text-left">Year</th>
                                  <th className="text-right">Operating CF ($B)</th>
                                  <th className="text-right">Investing CF ($B)</th>
                                  <th className="text-right">Financing CF ($B)</th>
                                  <th className="text-right">Free CF ($B)</th>
                                  <th className="text-right">Dividends Paid ($B)</th>
                                </tr>
                              </thead>
                              <tbody>
                                {filterByYear(analysis.cash_flows).slice().reverse().map((cf, i) => (
                                  <tr key={i}>
                                    <td className="font-medium">{cf.fiscal_date.substring(0, 4)}</td>
                                    <td className={cn('text-right number-display', (cf.operating_cashflow || 0) >= 0 ? 'value-positive' : 'value-negative')}>
                                      {((cf.operating_cashflow || 0) / 1e9).toFixed(2)}
                                    </td>
                                    <td className={cn('text-right number-display', (cf.investing_cashflow || 0) >= 0 ? 'value-positive' : 'value-negative')}>
                                      {((cf.investing_cashflow || 0) / 1e9).toFixed(2)}
                                    </td>
                                    <td className={cn('text-right number-display', (cf.financing_cashflow || 0) >= 0 ? 'value-positive' : 'value-negative')}>
                                      {((cf.financing_cashflow || 0) / 1e9).toFixed(2)}
                                    </td>
                                    <td className={cn('text-right number-display font-semibold', (cf.free_cashflow || 0) >= 0 ? 'value-positive' : 'value-negative')}>
                                      {((cf.free_cashflow || 0) / 1e9).toFixed(2)}
                                    </td>
                                    <td className="text-right number-display text-green-400">
                                      {(Math.abs(cf.dividend_payout || 0) / 1e9).toFixed(2)}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
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
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      Dividend Information & Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {/* Dividend Summary Metrics - 4 column grid like original */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <Card>
                        <CardContent className="pt-4 pb-4">
                          <p className="text-sm text-muted-foreground">Current Dividend Yield</p>
                          <p className="text-2xl font-bold text-green-400">
                            {analysis.overview.dividend_yield
                              ? formatPercentage(analysis.overview.dividend_yield * 100)
                              : 'N/A'}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4 pb-4">
                          <p className="text-sm text-muted-foreground">Dividend Per Share</p>
                          <p className="text-2xl font-bold">
                            ${analysis.overview.dividend_per_share?.toFixed(2) || 'N/A'}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4 pb-4">
                          <p className="text-sm text-muted-foreground">Payout Ratio</p>
                          <p className={`text-2xl font-bold ${
                            getPayoutRatio() > 80 ? 'text-red-400' :
                            getPayoutRatio() > 60 ? 'text-yellow-400' : ''
                          }`}>
                            {getPayoutRatio() > 0 ? formatPercentage(getPayoutRatio()) : 'N/A'}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4 pb-4">
                          <p className="text-sm text-muted-foreground">Ex-Dividend Date</p>
                          <p className="text-xl font-bold">
                            {analysis.overview.ex_dividend_date || 'N/A'}
                          </p>
                        </CardContent>
                      </Card>
                    </div>

                    {analysis.dividends.length > 0 ? (
                      <>
                        {/* Dividend History Chart */}
                        <div className="chart-reveal" style={{ minHeight: '400px' }}>
                          <PlotlyLineChart
                            key={`dividend-chart-${analysis.overview.symbol}`}
                            data={{
                              x: analysis.dividends.slice().reverse().map(d => d.ex_date),
                              y: analysis.dividends.slice().reverse().map(d => d.amount),
                              name: 'Dividend Amount',
                            }}
                            title={`Dividend History - ${analysis.overview.symbol}`}
                            height={400}
                            yAxisTitle="Amount ($)"
                            showMarkers={true}
                            curveType="spline"
                          />
                        </div>

                        {/* Dividend History Table */}
                        <div className="mt-6">
                          <h3 className="text-lg font-semibold mb-3">Recent Dividend Payments</h3>
                          <div className="max-h-64 overflow-y-auto rounded-lg border border-border/50">
                            <table className="table-enhanced w-full text-sm">
                              <thead>
                                <tr>
                                  <th className="text-left">Ex-Date</th>
                                  <th className="text-right">Amount</th>
                                  <th className="text-left">Payment Date</th>
                                </tr>
                              </thead>
                              <tbody>
                                {analysis.dividends.slice(0, 20).map((d, i) => (
                                  <tr key={i}>
                                    <td className="font-medium">{d.ex_date}</td>
                                    <td className="text-right number-display value-positive">${d.amount.toFixed(4)}</td>
                                    <td className="text-muted-foreground">
                                      {d.payment_date || '-'}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
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

            {/* Risk Assessment & Investment Summary - Enhanced with visual meters */}
            <Card className="card-premium">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-primary" />
                  Risk Assessment & Investment Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                {(() => {
                  const risk = calculateRiskAssessment();
                  const investment = calculateInvestmentSummary();

                  return (
                    <div className="space-y-8">
                      {/* Risk & Investment Meters */}
                      <div className="grid md:grid-cols-2 gap-8">
                        {/* Risk Meter Section */}
                        <div className="flex flex-col items-center p-6 rounded-lg bg-card/50 border border-border/50">
                          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Gauge className="h-5 w-5 text-yellow-500" />
                            Risk Assessment
                          </h3>
                          <RiskMeter score={risk.score} level={risk.level} />

                          {/* Risk Factors */}
                          <div className="mt-6 w-full">
                            {risk.factors.length > 0 ? (
                              <div className="space-y-2">
                                <p className="text-sm font-medium text-muted-foreground text-center mb-3">Risk Factors:</p>
                                {risk.factors.map((factor, i) => (
                                  <div
                                    key={i}
                                    className="flex items-center gap-2 text-sm px-3 py-2 rounded-md bg-red-500/10 border border-red-500/20"
                                  >
                                    <AlertTriangle className="h-3.5 w-3.5 text-red-400 flex-shrink-0" />
                                    <span className="text-red-300">{factor}</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="flex items-center justify-center gap-2 text-sm px-3 py-2 rounded-md bg-green-500/10 border border-green-500/20">
                                <Shield className="h-4 w-4 text-green-400" />
                                <span className="text-green-400">No significant risk factors</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Investment Score Section */}
                        <div className="flex flex-col items-center p-6 rounded-lg bg-card/50 border border-border/50">
                          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-green-500" />
                            Investment Summary
                          </h3>

                          {/* Investment Score Display */}
                          <div className="flex flex-col items-center mb-4">
                            <div className="relative">
                              <svg className="w-32 h-32" viewBox="0 0 100 100">
                                {/* Background circle */}
                                <circle
                                  cx="50"
                                  cy="50"
                                  r="40"
                                  fill="none"
                                  stroke="currentColor"
                                  strokeWidth="8"
                                  opacity="0.1"
                                />
                                {/* Progress circle */}
                                <circle
                                  cx="50"
                                  cy="50"
                                  r="40"
                                  fill="none"
                                  stroke={
                                    investment.score >= 70 ? '#22c55e' :
                                    investment.score >= 50 ? '#eab308' : '#ef4444'
                                  }
                                  strokeWidth="8"
                                  strokeLinecap="round"
                                  strokeDasharray={`${investment.score * 2.51} 251`}
                                  transform="rotate(-90 50 50)"
                                  style={{ transition: 'stroke-dasharray 1s ease-out' }}
                                />
                              </svg>
                              <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-3xl font-bold number-display">{investment.score}</span>
                                <span className="text-xs text-muted-foreground">/100</span>
                              </div>
                            </div>
                            <Badge
                              variant={
                                investment.recommendation.includes('Buy') ? 'default' :
                                investment.recommendation.includes('Hold') ? 'secondary' : 'destructive'
                              }
                              className="mt-3 text-sm px-4 py-1"
                            >
                              {investment.recommendation}
                            </Badge>
                          </div>

                          {/* Strengths & Considerations */}
                          <div className="w-full space-y-4 mt-2">
                            {/* Strengths */}
                            {investment.strengths.length > 0 && (
                              <div className="space-y-2">
                                <p className="text-sm font-medium text-muted-foreground">Key Strengths:</p>
                                {investment.strengths.slice(0, 3).map((s, i) => (
                                  <div
                                    key={i}
                                    className="flex items-center gap-2 text-sm px-3 py-2 rounded-md bg-green-500/10 border border-green-500/20"
                                  >
                                    <TrendingUp className="h-3.5 w-3.5 text-green-400 flex-shrink-0" />
                                    <span className="text-green-300">{s}</span>
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* Considerations */}
                            {investment.considerations.length > 0 && (
                              <div className="space-y-2">
                                <p className="text-sm font-medium text-muted-foreground">Considerations:</p>
                                {investment.considerations.slice(0, 3).map((c, i) => (
                                  <div
                                    key={i}
                                    className="flex items-center gap-2 text-sm px-3 py-2 rounded-md bg-yellow-500/10 border border-yellow-500/20"
                                  >
                                    <AlertTriangle className="h-3.5 w-3.5 text-yellow-400 flex-shrink-0" />
                                    <span className="text-yellow-300">{c}</span>
                                  </div>
                                ))}
                              </div>
                            )}

                            {investment.considerations.length === 0 && (
                              <div className="flex items-center justify-center gap-2 text-sm px-3 py-2 rounded-md bg-green-500/10 border border-green-500/20">
                                <Shield className="h-4 w-4 text-green-400" />
                                <span className="text-green-400">No major concerns identified</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </CardContent>
            </Card>
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
