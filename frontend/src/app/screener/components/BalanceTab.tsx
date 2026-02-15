'use client';

import dynamic from 'next/dynamic';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { PieChart } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { BalanceSheet } from '@/types/screener';

const PlotlyGroupedBarChart = dynamic(
  () => import('@/components/charts/plotly').then(mod => ({ default: mod.PlotlyGroupedBarChart })),
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

interface BalanceTabProps {
  balanceSheets: BalanceSheet[];
  symbol: string;
  period?: string;
}

export function BalanceTab({ balanceSheets, symbol, period = 'annual' }: BalanceTabProps) {
  if (balanceSheets.length === 0) {
    return <p className="text-muted-foreground text-center py-8">No balance sheet data available</p>;
  }

  const reversed = balanceSheets.slice().reverse();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PieChart className="h-5 w-5" />
          Balance Sheet Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Assets vs Liabilities Chart */}
        <div className="chart-reveal" style={{ minHeight: '500px' }}>
          <PlotlyGroupedBarChart
            key={`balance-chart-${symbol}`}
            data={{
              categories: reversed.map(bs => formatPeriodLabel(bs.fiscal_date, period)),
              series: [
                { name: 'Total Assets', values: reversed.map(bs => (bs.total_assets || 0) / 1e9), color: '#3b82f6' },
                { name: 'Total Liabilities', values: reversed.map(bs => (bs.total_liabilities || 0) / 1e9), color: '#ef4444' },
                { name: 'Shareholders Equity', values: reversed.map(bs => (bs.total_equity || 0) / 1e9), color: '#22c55e' },
              ],
            }}
            title={`Balance Sheet Overview - ${symbol}`}
            height={500}
            yAxisTitle="Amount ($ Billions)"
          />
        </div>

        {/* Debt Analysis Chart */}
        <div className="mt-6 chart-reveal" style={{ minHeight: '400px' }}>
          <PlotlyLineChart
            key={`debt-chart-${symbol}`}
            data={[
              {
                x: reversed.map(bs => formatPeriodLabel(bs.fiscal_date, period)),
                y: reversed.map(bs => (bs.total_debt || 0) / 1e9),
                name: 'Long-term Debt',
              },
              {
                x: reversed.map(bs => formatPeriodLabel(bs.fiscal_date, period)),
                y: reversed.map(bs => (bs.cash_and_equivalents || 0) / 1e9),
                name: 'Cash & Equivalents',
              },
            ]}
            title={`Debt Analysis - ${symbol}`}
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
                  <th className="text-left">Period</th>
                  <th className="text-right">Total Assets ($B)</th>
                  <th className="text-right">Total Liabilities ($B)</th>
                  <th className="text-right">Equity ($B)</th>
                  <th className="text-right">Long-term Debt ($B)</th>
                  <th className="text-right">Cash ($B)</th>
                </tr>
              </thead>
              <tbody>
                {reversed.map((bs, i) => (
                  <tr key={i}>
                    <td className="font-medium">{formatPeriodLabel(bs.fiscal_date, period)}</td>
                    <td className="text-right number-display">{((bs.total_assets || 0) / 1e9).toFixed(2)}</td>
                    <td className="text-right number-display">{((bs.total_liabilities || 0) / 1e9).toFixed(2)}</td>
                    <td className="text-right number-display value-positive">{((bs.total_equity || 0) / 1e9).toFixed(2)}</td>
                    <td className="text-right number-display text-red-400">{((bs.total_debt || 0) / 1e9).toFixed(2)}</td>
                    <td className="text-right number-display text-blue-400">{((bs.cash_and_equivalents || 0) / 1e9).toFixed(2)}</td>
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
