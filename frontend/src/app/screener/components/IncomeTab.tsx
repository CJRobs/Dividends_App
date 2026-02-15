'use client';

import dynamic from 'next/dynamic';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { IncomeStatement } from '@/types/screener';

const PlotlyDualAxisChart = dynamic(
  () => import('@/components/charts/plotly').then(mod => ({ default: mod.PlotlyDualAxisChart })),
  { loading: () => <Skeleton className="h-[400px]" />, ssr: false }
);

const PlotlyLineChart = dynamic(
  () => import('@/components/charts/PlotlyLineChart').then(mod => ({ default: mod.PlotlyLineChart })),
  { loading: () => <Skeleton className="h-[400px]" />, ssr: false }
);

function formatPeriodLabel(fiscalDate: string, period: string): string {
  if (period === 'annual') return fiscalDate.substring(0, 4);
  const d = new Date(fiscalDate);
  const q = Math.ceil((d.getMonth() + 1) / 3);
  return `Q${q} ${d.getFullYear()}`;
}

interface IncomeTabProps {
  incomeStatements: IncomeStatement[];
  symbol: string;
  period?: string;
}

export function IncomeTab({ incomeStatements, symbol, period = 'annual' }: IncomeTabProps) {
  if (incomeStatements.length === 0) {
    return <p className="text-muted-foreground text-center py-8">No income statement data available</p>;
  }

  const reversed = incomeStatements.slice().reverse();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Income Statement Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Revenue and Profitability Chart */}
        <div className="chart-reveal" style={{ minHeight: '500px' }}>
          <PlotlyDualAxisChart
            key={`income-chart-${symbol}`}
            bars={[{
              x: reversed.map(is => formatPeriodLabel(is.fiscal_date, period)),
              y: reversed.map(is => (is.total_revenue || 0) / 1e9),
              name: 'Total Revenue',
              color: '#4e8df5',
              yaxis: 'y',
            }]}
            lines={[
              {
                x: reversed.map(is => formatPeriodLabel(is.fiscal_date, period)),
                y: reversed.map(is => (is.gross_profit || 0) / 1e9),
                name: 'Gross Profit',
                color: '#22c55e',
                yaxis: 'y2',
              },
              {
                x: reversed.map(is => formatPeriodLabel(is.fiscal_date, period)),
                y: reversed.map(is => (is.net_income || 0) / 1e9),
                name: 'Net Income',
                color: '#f59e0b',
                yaxis: 'y2',
              },
            ]}
            title={`Revenue and Profitability - ${symbol}`}
            height={500}
            yAxisTitle="Revenue ($ Billions)"
            y2AxisTitle="Profit ($ Billions)"
          />
        </div>

        {/* Margins Trend Chart */}
        {reversed.some(s => s.gross_margin != null) && (
          <div className="mt-6 chart-reveal" style={{ minHeight: '400px' }}>
            <PlotlyLineChart
              key={`margins-chart-${symbol}`}
              data={[
                {
                  x: reversed.map(s => formatPeriodLabel(s.fiscal_date, period)),
                  y: reversed.map(s => s.gross_margin ?? 0),
                  name: 'Gross Margin %',
                },
                {
                  x: reversed.map(s => formatPeriodLabel(s.fiscal_date, period)),
                  y: reversed.map(s => s.operating_margin ?? 0),
                  name: 'Operating Margin %',
                },
                {
                  x: reversed.map(s => formatPeriodLabel(s.fiscal_date, period)),
                  y: reversed.map(s => s.net_margin ?? 0),
                  name: 'Net Margin %',
                },
              ]}
              title={`Margin Trends - ${symbol}`}
              height={400}
              yAxisTitle="Margin (%)"
              showMarkers={true}
            />
          </div>
        )}

        {/* Income Statement Table */}
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-3">Income Statement Summary</h3>
          <div className="overflow-x-auto rounded-lg border border-border/50">
            <table className="table-enhanced w-full text-sm">
              <thead>
                <tr>
                  <th className="text-left">Period</th>
                  <th className="text-right">Revenue ($B)</th>
                  <th className="text-right">Rev Growth</th>
                  <th className="text-right">Gross Margin</th>
                  <th className="text-right">Op Margin</th>
                  <th className="text-right">Net Income ($B)</th>
                  <th className="text-right">Net Margin</th>
                  <th className="text-right">EBITDA ($B)</th>
                </tr>
              </thead>
              <tbody>
                {reversed.map((is, i) => (
                  <tr key={i}>
                    <td className="font-medium">{formatPeriodLabel(is.fiscal_date, period)}</td>
                    <td className="text-right number-display">{((is.total_revenue || 0) / 1e9).toFixed(2)}</td>
                    <td className={cn('text-right number-display', (is.revenue_growth_yoy ?? 0) >= 0 ? 'value-positive' : 'value-negative')}>
                      {is.revenue_growth_yoy != null ? `${is.revenue_growth_yoy.toFixed(1)}%` : '-'}
                    </td>
                    <td className="text-right number-display">{is.gross_margin != null ? `${is.gross_margin.toFixed(1)}%` : '-'}</td>
                    <td className="text-right number-display">{is.operating_margin != null ? `${is.operating_margin.toFixed(1)}%` : '-'}</td>
                    <td className="text-right number-display">{((is.net_income || 0) / 1e9).toFixed(2)}</td>
                    <td className="text-right number-display">{is.net_margin != null ? `${is.net_margin.toFixed(1)}%` : '-'}</td>
                    <td className="text-right number-display">{((is.ebitda || 0) / 1e9).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
