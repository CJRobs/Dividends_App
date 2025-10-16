'use client';

/**
 * Overview page - Main dashboard view.
 */

import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useOverview } from '@/hooks/usePortfolio';
import { formatCurrency, formatPercentage } from '@/lib/constants';
import { usePortfolioStore } from '@/store/portfolioStore';
import { TrendingUp, TrendingDown, DollarSign, PieChart, Calendar } from 'lucide-react';

export default function OverviewPage() {
  const { data, isLoading, error } = useOverview();
  const { currency } = usePortfolioStore();

  // Extract data from the complete overview response
  const summary = data?.summary;
  const topStocks = data?.top_stocks;
  const recentDividends = data?.recent_dividends;

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
                <Card key={i}>
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
                    All time dividend income
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
                  {summary?.ytd_vs_last_year_percent !== undefined && (
                    <p className={`text-xs flex items-center ${
                      data.ytd_vs_last_year_percent >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {data.ytd_vs_last_year_percent >= 0 ? (
                        <TrendingUp className="h-3 w-3 mr-1" />
                      ) : (
                        <TrendingDown className="h-3 w-3 mr-1" />
                      )}
                      {formatPercentage(Math.abs(data.ytd_vs_last_year_percent))} vs last year
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Unique Stocks */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Unique Stocks</CardTitle>
                  <PieChart className="h-4 w-4 text-muted-foreground" />
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

        {/* Top Stocks and Recent Dividends Row */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Top Dividend Stocks */}
          <Card>
            <CardHeader>
              <CardTitle>Top Dividend Stocks</CardTitle>
              <CardDescription>Your highest dividend-paying stocks</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-4 w-20" />
                    </div>
                  ))}
                </div>
              ) : topStocks && topStocks.length > 0 ? (
                <div className="space-y-3">
                  {topStocks.slice(0, 5).map((stock) => (
                    <div key={stock.ticker} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{stock.ticker}</p>
                        <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {stock.name}
                        </p>
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
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <Skeleton className="h-4 w-32" />
                      <Skeleton className="h-4 w-20" />
                    </div>
                  ))}
                </div>
              ) : recentDividends && recentDividends.length > 0 ? (
                <div className="space-y-3">
                  {recentDividends.slice(0, 5).map((dividend, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{dividend.ticker}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(dividend.date).toLocaleDateString()}
                        </p>
                      </div>
                      <p className="font-semibold">
                        {formatCurrency(dividend.amount, currency)}
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
