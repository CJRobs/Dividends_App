'use client';

import dynamic from 'next/dynamic';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { GrowthMetricsCard } from './GrowthMetricsCard';
import { AnalystCard } from './AnalystCard';
import type { ScreenerAnalysis } from '@/types/screener';

const PlotlyBarChart = dynamic(
  () => import('@/components/charts/plotly').then(mod => ({ default: mod.PlotlyBarChart })),
  { loading: () => <Skeleton className="h-[400px]" />, ssr: false }
);

const PlotlyLineChart = dynamic(
  () => import('@/components/charts/PlotlyLineChart').then(mod => ({ default: mod.PlotlyLineChart })),
  { loading: () => <Skeleton className="h-[400px]" />, ssr: false }
);

interface EarningsTabProps {
  analysis: ScreenerAnalysis;
}

export function EarningsTab({ analysis }: EarningsTabProps) {
  const quarterly = analysis.quarterly_earnings ?? [];
  const annual = analysis.annual_earnings ?? [];
  const hasEarnings = quarterly.length > 0 || annual.length > 0;

  return (
    <div className="space-y-4">
      {/* Quarterly EPS Chart */}
      {quarterly.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Quarterly Earnings (EPS)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="chart-reveal" style={{ minHeight: '400px' }}>
              <PlotlyBarChart
                key={`eps-chart-${analysis.overview.symbol}`}
                labels={quarterly.slice().reverse().map(e => e.fiscal_date)}
                values={quarterly.slice().reverse().map(e => e.reported_eps ?? 0)}
                title={`Quarterly EPS - ${analysis.overview.symbol}`}
                height={400}
                yAxisTitle="EPS ($)"
                color="#4e8df5"
              />
            </div>

            {/* Quarterly EPS Table */}
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-3">Quarterly Earnings Detail</h3>
              <div className="max-h-64 overflow-y-auto rounded-lg border border-border/50">
                <table className="table-enhanced w-full text-sm">
                  <thead>
                    <tr>
                      <th className="text-left">Quarter</th>
                      <th className="text-right">Reported EPS</th>
                      <th className="text-right">Estimated EPS</th>
                      <th className="text-right">Surprise</th>
                      <th className="text-right">Surprise %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {quarterly.map((e, i) => (
                      <tr key={i}>
                        <td className="font-medium">{e.fiscal_date}</td>
                        <td className="text-right number-display">{e.reported_eps?.toFixed(2) ?? '-'}</td>
                        <td className="text-right number-display text-muted-foreground">{e.estimated_eps?.toFixed(2) ?? '-'}</td>
                        <td className={cn('text-right number-display', (e.surprise ?? 0) >= 0 ? 'text-green-400' : 'text-red-400')}>
                          {e.surprise != null ? `$${e.surprise.toFixed(2)}` : '-'}
                        </td>
                        <td className={cn('text-right number-display', (e.surprise_percentage ?? 0) >= 0 ? 'text-green-400' : 'text-red-400')}>
                          {e.surprise_percentage != null ? `${e.surprise_percentage.toFixed(1)}%` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Annual EPS Trend */}
      {annual.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Annual EPS Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="chart-reveal" style={{ minHeight: '300px' }}>
              <PlotlyLineChart
                key={`annual-eps-${analysis.overview.symbol}`}
                data={{
                  x: annual.slice().reverse().map(e => e.fiscal_date.substring(0, 4)),
                  y: annual.slice().reverse().map(e => e.reported_eps ?? 0),
                  name: 'Annual EPS',
                }}
                title={`Annual EPS - ${analysis.overview.symbol}`}
                height={300}
                yAxisTitle="EPS ($)"
                showMarkers={true}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Growth Metrics */}
      <GrowthMetricsCard metrics={analysis.growth_metrics} />

      {/* Analyst Sentiment */}
      <AnalystCard sentiment={analysis.analyst_sentiment} currentPrice={analysis.overview.current_price} />

      {!hasEarnings && !analysis.growth_metrics && !analysis.analyst_sentiment?.total_analysts && (
        <p className="text-muted-foreground text-center py-8">No earnings or growth data available</p>
      )}
    </div>
  );
}
