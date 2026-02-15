'use client';

import dynamic from 'next/dynamic';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { DollarSign } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatLargeNumber, formatPercentage } from '@/lib/constants';
import type { CashFlow } from '@/types/screener';

const PlotlyCashFlowChart = dynamic(
  () => import('@/components/charts/plotly').then(mod => ({ default: mod.PlotlyCashFlowChart })),
  { loading: () => <Skeleton className="h-[400px]" />, ssr: false }
);

function formatPeriodLabel(fiscalDate: string, period: string): string {
  if (period === 'annual') return fiscalDate.substring(0, 4);
  const d = new Date(fiscalDate);
  const q = Math.ceil((d.getMonth() + 1) / 3);
  return `Q${q} ${d.getFullYear()}`;
}

interface CashFlowTabProps {
  cashFlows: CashFlow[];
  symbol: string;
  period?: string;
}

export function CashFlowTab({ cashFlows, symbol, period = 'annual' }: CashFlowTabProps) {
  if (cashFlows.length === 0) {
    return <p className="text-muted-foreground text-center py-8">No cash flow data available</p>;
  }

  const reversed = cashFlows.slice().reverse();
  const latest = cashFlows[0];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <DollarSign className="h-5 w-5" />
          Cash Flow Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* FCF vs Dividends vs CapEx Chart */}
        <div className="chart-reveal" style={{ minHeight: '500px' }}>
          <PlotlyCashFlowChart
            key={`cashflow-chart-${symbol}`}
            years={reversed.map(cf => formatPeriodLabel(cf.fiscal_date, period))}
            fcf={reversed.map(cf => (cf.free_cashflow || 0) / 1e9)}
            dividends={reversed.map(cf => Math.abs(cf.dividend_payout || 0) / 1e9)}
            capex={reversed.map(cf => Math.abs(cf.capital_expenditure || 0) / 1e9)}
            title={`Free Cash Flow vs Dividends & CapEx - ${symbol}`}
            height={500}
          />
        </div>

        {/* Cash Flow Coverage & FCF Metrics */}
        {latest && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-3">Cash Flow Metrics</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <Card>
                <CardContent className="pt-4 pb-4">
                  <p className="text-sm text-muted-foreground">Dividend Coverage</p>
                  <p className="text-2xl font-bold">
                    {latest.free_cashflow && latest.dividend_payout
                      ? `${(Math.abs(latest.free_cashflow) / Math.abs(latest.dividend_payout)).toFixed(2)}x`
                      : 'N/A'}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 pb-4">
                  <p className="text-sm text-muted-foreground">Free Cash Flow</p>
                  <p className="text-2xl font-bold text-blue-400">
                    {latest.free_cashflow ? formatLargeNumber(latest.free_cashflow) : 'N/A'}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 pb-4">
                  <p className="text-sm text-muted-foreground">Dividends Paid</p>
                  <p className="text-2xl font-bold text-green-400">
                    {latest.dividend_payout ? formatLargeNumber(Math.abs(latest.dividend_payout)) : 'N/A'}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 pb-4">
                  <p className="text-sm text-muted-foreground">FCF Per Share</p>
                  <p className="text-2xl font-bold">
                    {latest.fcf_per_share != null ? `$${latest.fcf_per_share.toFixed(2)}` : 'N/A'}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 pb-4">
                  <p className="text-sm text-muted-foreground">FCF Yield</p>
                  <p className={cn('text-2xl font-bold', (latest.fcf_yield ?? 0) >= 5 ? 'text-green-400' : '')}>
                    {latest.fcf_yield != null ? formatPercentage(latest.fcf_yield) : 'N/A'}
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 pb-4">
                  <p className="text-sm text-muted-foreground">FCF Margin</p>
                  <p className={cn('text-2xl font-bold', (latest.fcf_margin ?? 0) >= 15 ? 'text-green-400' : '')}>
                    {latest.fcf_margin != null ? formatPercentage(latest.fcf_margin) : 'N/A'}
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
                  <th className="text-left">Period</th>
                  <th className="text-right">Operating CF ($B)</th>
                  <th className="text-right">Investing CF ($B)</th>
                  <th className="text-right">Financing CF ($B)</th>
                  <th className="text-right">Free CF ($B)</th>
                  <th className="text-right">Dividends Paid ($B)</th>
                </tr>
              </thead>
              <tbody>
                {reversed.map((cf, i) => (
                  <tr key={i}>
                    <td className="font-medium">{formatPeriodLabel(cf.fiscal_date, period)}</td>
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
      </CardContent>
    </Card>
  );
}
