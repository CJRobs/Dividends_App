'use client';

import dynamic from 'next/dynamic';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp } from 'lucide-react';
import { formatPercentage } from '@/lib/constants';
import type { ScreenerAnalysis } from '@/types/screener';

const PlotlyLineChart = dynamic(
  () => import('@/components/charts/PlotlyLineChart').then(mod => ({ default: mod.PlotlyLineChart })),
  { loading: () => <Skeleton className="h-[400px]" />, ssr: false }
);

interface DividendsTabProps {
  analysis: ScreenerAnalysis;
}

export function DividendsTab({ analysis }: DividendsTabProps) {
  const overview = analysis.overview;
  const dividends = analysis.dividends;
  const payoutRatio = overview.payout_ratio ? overview.payout_ratio * 100 : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Dividend Information & Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Dividend Summary Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-sm text-muted-foreground">Current Dividend Yield</p>
              <p className="text-2xl font-bold text-green-400">
                {overview.dividend_yield ? formatPercentage(overview.dividend_yield * 100) : 'N/A'}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-sm text-muted-foreground">Dividend Per Share</p>
              <p className="text-2xl font-bold">
                ${overview.dividend_per_share?.toFixed(2) || 'N/A'}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-sm text-muted-foreground">Payout Ratio</p>
              <p className={`text-2xl font-bold ${
                payoutRatio > 80 ? 'text-red-400' : payoutRatio > 60 ? 'text-yellow-400' : ''
              }`}>
                {payoutRatio > 0 ? formatPercentage(payoutRatio) : 'N/A'}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-sm text-muted-foreground">Ex-Dividend Date</p>
              <p className="text-xl font-bold">
                {overview.ex_dividend_date || 'N/A'}
              </p>
            </CardContent>
          </Card>
        </div>

        {dividends.length > 0 ? (
          <>
            {/* Dividend History Chart */}
            <div className="chart-reveal" style={{ minHeight: '400px' }}>
              <PlotlyLineChart
                key={`dividend-chart-${overview.symbol}`}
                data={{
                  x: dividends.slice().reverse().map(d => d.ex_date),
                  y: dividends.slice().reverse().map(d => d.amount),
                  name: 'Dividend Amount',
                }}
                title={`Dividend History - ${overview.symbol}`}
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
                    {dividends.slice(0, 20).map((d, i) => (
                      <tr key={i}>
                        <td className="font-medium">{d.ex_date}</td>
                        <td className="text-right number-display value-positive">${d.amount.toFixed(4)}</td>
                        <td className="text-muted-foreground">{d.payment_date || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <p className="text-muted-foreground text-center py-8">No dividend history available</p>
        )}
      </CardContent>
    </Card>
  );
}
