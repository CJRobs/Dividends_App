'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { GrowthMetrics } from '@/types/screener';

interface GrowthMetricsCardProps {
  metrics?: GrowthMetrics;
}

function GrowthItem({ label, value }: { label: string; value?: number }) {
  if (value == null) return null;

  const isPositive = value >= 0;

  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-md bg-muted/30">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={cn('text-sm font-bold flex items-center gap-1', isPositive ? 'text-green-400' : 'text-red-400')}>
        {isPositive ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
        {value.toFixed(1)}%
      </span>
    </div>
  );
}

export function GrowthMetricsCard({ metrics }: GrowthMetricsCardProps) {
  if (!metrics) return null;

  const hasAny = [
    metrics.revenue_cagr_3y, metrics.revenue_cagr_5y,
    metrics.eps_cagr_3y, metrics.eps_cagr_5y,
    metrics.fcf_cagr_3y,
    metrics.dividend_cagr_3y, metrics.dividend_cagr_5y,
  ].some(v => v != null);

  if (!hasAny) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-green-500" />
          Growth Metrics (CAGR)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Revenue</p>
            <GrowthItem label="3-Year CAGR" value={metrics.revenue_cagr_3y} />
            <GrowthItem label="5-Year CAGR" value={metrics.revenue_cagr_5y} />
          </div>
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">EPS</p>
            <GrowthItem label="3-Year CAGR" value={metrics.eps_cagr_3y} />
            <GrowthItem label="5-Year CAGR" value={metrics.eps_cagr_5y} />
          </div>
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Free Cash Flow</p>
            <GrowthItem label="3-Year CAGR" value={metrics.fcf_cagr_3y} />
          </div>
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Dividends</p>
            <GrowthItem label="3-Year CAGR" value={metrics.dividend_cagr_3y} />
            <GrowthItem label="5-Year CAGR" value={metrics.dividend_cagr_5y} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
