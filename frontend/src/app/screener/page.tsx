'use client';

import { useState, useRef, useCallback, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search, AlertTriangle, RefreshCw, Clock } from 'lucide-react';
import api from '@/lib/api';
import type { ScreenerAnalysis } from '@/types/screener';

// Sub-components
import { CompanyProfile } from './components/CompanyProfile';
import { IncomeTab } from './components/IncomeTab';
import { BalanceTab } from './components/BalanceTab';
import { CashFlowTab } from './components/CashFlowTab';
import { DividendsTab } from './components/DividendsTab';
import { EarningsTab } from './components/EarningsTab';
import { RiskSummary } from './components/RiskSummary';

function formatRelativeTime(isoString: string): string {
  const now = new Date();
  const then = new Date(isoString);
  const diffMs = now.getTime() - then.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

export default function ScreenerPage() {
  const [symbol, setSymbol] = useState('');
  const [searchSymbol, setSearchSymbol] = useState('');
  const [timePeriod, setTimePeriod] = useState('5');
  const [period, setPeriod] = useState<'annual' | 'quarterly'>('annual');
  const forceRefreshRef = useRef(false);
  const queryClient = useQueryClient();

  const { data: analysis, isLoading, error, isFetching } = useQuery<ScreenerAnalysis>({
    queryKey: ['screener-analysis', searchSymbol, period],
    queryFn: () => {
      const refresh = forceRefreshRef.current;
      forceRefreshRef.current = false;
      const params = new URLSearchParams();
      params.set('period', period);
      if (refresh) params.set('refresh', 'true');
      return api.get(`/api/screener/analysis/${searchSymbol}?${params}`).then(res => res.data);
    },
    enabled: !!searchSymbol,
    retry: false,
  });

  const handleSearch = () => {
    if (symbol.trim()) {
      setSearchSymbol(symbol.trim().toUpperCase());
    }
  };

  const handleRefresh = useCallback(() => {
    if (!searchSymbol || isFetching) return;
    forceRefreshRef.current = true;
    queryClient.invalidateQueries({ queryKey: ['screener-analysis', searchSymbol] });
  }, [searchSymbol, isFetching, queryClient]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  // Compute freshness info from analysis data
  const freshnessInfo = useMemo(() => {
    if (!analysis?.data_freshness) return null;
    const entries = Object.values(analysis.data_freshness);
    const cachedEntries = entries.filter(e => e.cached_at);
    if (cachedEntries.length === 0) return { label: 'Freshly fetched', isStale: false };

    // Find the oldest cached_at across all data types
    const oldest = cachedEntries.reduce((oldest, e) =>
      !oldest || (e.cached_at && e.cached_at < oldest) ? e.cached_at! : oldest,
      '' as string,
    );
    if (!oldest) return { label: 'Freshly fetched', isStale: false };

    const label = `Updated ${formatRelativeTime(oldest)}`;
    const diffHours = (Date.now() - new Date(oldest).getTime()) / 3600000;
    return { label, isStale: diffHours > 20 };
  }, [analysis]);

  // Filter financial data by time period
  const cutoffYear = new Date().getFullYear() - parseInt(timePeriod);
  const filterByYear = <T extends { fiscal_date: string }>(data: T[]): T[] => {
    if (timePeriod === 'all') return data;
    return data.filter(item => parseInt(item.fiscal_date.substring(0, 4)) >= cutoffYear);
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dividend Stock Analyzer</h1>
          <p className="text-muted-foreground">
            Comprehensive dividend analysis with financial metrics, earnings data, and risk assessment
          </p>
        </div>

        {/* Search Bar */}
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
                  Frequency
                </label>
                <Select value={period} onValueChange={(v) => setPeriod(v as 'annual' | 'quarterly')}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="annual">Annual</SelectItem>
                    <SelectItem value="quarterly">Quarterly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="w-40">
                <label className="text-sm text-muted-foreground mb-2 block">
                  History
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
              {analysis && (
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleRefresh}
                  disabled={isFetching}
                  title="Refresh data from providers"
                >
                  <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
                </Button>
              )}
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
            {/* Freshness indicator */}
            {freshnessInfo && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className={`h-3.5 w-3.5 ${freshnessInfo.isStale ? 'text-amber-500' : ''}`} />
                <span className={freshnessInfo.isStale ? 'text-amber-500' : ''}>
                  {freshnessInfo.label}
                </span>
                {freshnessInfo.isStale && (
                  <button
                    onClick={handleRefresh}
                    className="text-amber-500 underline underline-offset-2 hover:text-amber-400 text-sm"
                    disabled={isFetching}
                  >
                    Refresh now
                  </button>
                )}
              </div>
            )}

            <CompanyProfile analysis={analysis} />

            {/* Analysis Tabs - 5 tabs */}
            <Tabs defaultValue="income" className="space-y-4">
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="income">Income Statement</TabsTrigger>
                <TabsTrigger value="balance">Balance Sheet</TabsTrigger>
                <TabsTrigger value="cashflow">Cash Flow</TabsTrigger>
                <TabsTrigger value="dividends">Dividend Info</TabsTrigger>
                <TabsTrigger value="earnings">Earnings & Growth</TabsTrigger>
              </TabsList>

              <TabsContent value="income" className="space-y-4">
                <IncomeTab
                  incomeStatements={filterByYear(analysis.income_statements)}
                  symbol={analysis.overview.symbol}
                  period={period}
                />
              </TabsContent>

              <TabsContent value="balance" className="space-y-4">
                <BalanceTab
                  balanceSheets={filterByYear(analysis.balance_sheets)}
                  symbol={analysis.overview.symbol}
                  period={period}
                />
              </TabsContent>

              <TabsContent value="cashflow" className="space-y-4">
                <CashFlowTab
                  cashFlows={filterByYear(analysis.cash_flows)}
                  symbol={analysis.overview.symbol}
                  period={period}
                />
              </TabsContent>

              <TabsContent value="dividends" className="space-y-4">
                <DividendsTab analysis={analysis} />
              </TabsContent>

              <TabsContent value="earnings" className="space-y-4">
                <EarningsTab analysis={analysis} />
              </TabsContent>
            </Tabs>

            <RiskSummary analysis={analysis} />
          </>
        )}

        {/* Initial State */}
        {!searchSymbol && !isLoading && (
          <Card className="border-dashed">
            <CardContent className="py-12 text-center">
              <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
              <h3 className="text-lg font-semibold mb-2">Enter a Stock Symbol</h3>
              <p className="text-muted-foreground max-w-md mx-auto">
                Search for any stock to view detailed financial analysis including
                income statements, balance sheets, cash flows, earnings, and dividend history.
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
