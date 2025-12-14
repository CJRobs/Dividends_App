'use client';

import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { COLORS } from '@/lib/constants';

// Color palette for multiple series
const CHART_COLORS = [
  COLORS.primary,
  COLORS.success,
  COLORS.warning,
  COLORS.secondary,
  COLORS.danger,
  COLORS.info,
  '#ec4899', // pink
  '#84cc16', // lime
  '#06b6d4', // cyan
  '#f97316', // orange
];

interface LineChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  yKeys: string[];
  yLabels?: string[];
  colors?: string[];
  showLegend?: boolean;
  showGrid?: boolean;
  showDots?: boolean;
  curved?: boolean;
  formatValue?: (value: number) => string;
  formatLabel?: (label: string) => string;
}

export function LineChart({
  data,
  xKey,
  yKeys,
  yLabels,
  colors = CHART_COLORS,
  showLegend = true,
  showGrid = true,
  showDots = true,
  curved = true,
  formatValue = (v) => v.toLocaleString(),
  formatLabel = (l) => l,
}: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsLineChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-border" opacity={0.5} />}

        <XAxis dataKey={xKey} tickFormatter={formatLabel} className="fill-muted-foreground" fontSize={12} tick={{ fill: 'currentColor' }} stroke="currentColor" />
        <YAxis tickFormatter={formatValue} className="fill-muted-foreground" fontSize={12} tick={{ fill: 'currentColor' }} stroke="currentColor" />

        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
            color: 'hsl(var(--card-foreground))',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          }}
          formatter={(value: number, name: string) => [formatValue(value), name]}
          labelFormatter={formatLabel}
        />

        {showLegend && yKeys.length > 1 && (
          <Legend
            wrapperStyle={{ color: 'hsl(var(--muted-foreground))' }}
            formatter={(value) => <span className="text-muted-foreground">{value}</span>}
          />
        )}

        {yKeys.map((key, index) => (
          <Line
            key={key}
            type={curved ? 'monotone' : 'linear'}
            dataKey={key}
            name={yLabels?.[index] || key}
            stroke={colors[index % colors.length]}
            strokeWidth={2}
            dot={showDots ? { fill: colors[index % colors.length], r: 4 } : false}
            activeDot={{ r: 6 }}
          />
        ))}
      </RechartsLineChart>
    </ResponsiveContainer>
  );
}
