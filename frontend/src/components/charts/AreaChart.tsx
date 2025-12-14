'use client';

import {
  AreaChart as RechartsAreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { COLORS } from '@/lib/constants';

// Color palette
const CHART_COLORS = [
  COLORS.primary,
  COLORS.success,
  COLORS.warning,
  COLORS.secondary,
  COLORS.danger,
  COLORS.info,
];

interface AreaChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  yKeys: string[];
  yLabels?: string[];
  colors?: string[];
  showLegend?: boolean;
  showGrid?: boolean;
  stacked?: boolean;
  formatValue?: (value: number) => string;
  formatLabel?: (label: string) => string;
  gradient?: boolean;
}

export function AreaChart({
  data,
  xKey,
  yKeys,
  yLabels,
  colors = CHART_COLORS,
  showLegend = true,
  showGrid = true,
  stacked = false,
  formatValue = (v) => v.toLocaleString(),
  formatLabel = (l) => l,
  gradient = true,
}: AreaChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsAreaChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        {gradient && (
          <defs>
            {yKeys.map((key, index) => (
              <linearGradient key={key} id={`gradient-${key}`} x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={colors[index % colors.length]}
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor={colors[index % colors.length]}
                  stopOpacity={0.1}
                />
              </linearGradient>
            ))}
          </defs>
        )}

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
          <Area
            key={key}
            type="monotone"
            dataKey={key}
            name={yLabels?.[index] || key}
            stroke={colors[index % colors.length]}
            fill={gradient ? `url(#gradient-${key})` : colors[index % colors.length]}
            fillOpacity={gradient ? 1 : 0.3}
            stackId={stacked ? 'stack' : undefined}
          />
        ))}
      </RechartsAreaChart>
    </ResponsiveContainer>
  );
}

// Forecast chart with confidence interval and current month tracking
interface ForecastChartProps {
  data: {
    date: string;
    actual?: number;
    forecast?: number;
    lower?: number;
    upper?: number;
    tracking?: number;  // Current month partial data
  }[];
  formatValue?: (value: number) => string;
  formatLabel?: (label: string) => string;
}

export function ForecastChart({
  data,
  formatValue = (v) => v.toLocaleString(),
  formatLabel = (l) => l,
}: ForecastChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsAreaChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        <defs>
          <linearGradient id="gradient-ci" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3} />
            <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0.05} />
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="3 3" className="stroke-border" opacity={0.5} />

        <XAxis dataKey="date" tickFormatter={formatLabel} className="fill-muted-foreground" fontSize={12} tick={{ fill: 'currentColor' }} stroke="currentColor" />
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

        <Legend
          wrapperStyle={{ color: 'hsl(var(--muted-foreground))' }}
          formatter={(value) => <span className="text-muted-foreground">{value}</span>}
        />

        {/* Confidence interval area */}
        <Area
          type="monotone"
          dataKey="upper"
          stroke="transparent"
          fill="url(#gradient-ci)"
          name="Upper Bound"
        />
        <Area
          type="monotone"
          dataKey="lower"
          stroke="transparent"
          fill="hsl(var(--card))"
          name="Lower Bound"
        />

        {/* Actual values (completed months) */}
        <Area
          type="monotone"
          dataKey="actual"
          stroke={COLORS.success}
          fill="transparent"
          strokeWidth={2}
          name="Actual"
          dot={{ fill: COLORS.success, r: 3 }}
        />

        {/* Current month tracking dot (partial data) */}
        <Area
          type="monotone"
          dataKey="tracking"
          stroke="transparent"
          fill="transparent"
          strokeWidth={0}
          name="Current Month (Partial)"
          dot={{ fill: COLORS.warning, r: 6, strokeWidth: 2, stroke: '#fff' }}
          activeDot={{ fill: COLORS.warning, r: 8, strokeWidth: 3, stroke: '#fff' }}
        />

        {/* Forecast line */}
        <Area
          type="monotone"
          dataKey="forecast"
          stroke={COLORS.primary}
          fill="transparent"
          strokeWidth={2}
          strokeDasharray="5 5"
          name="Forecast"
          dot={{ fill: COLORS.primary, r: 3 }}
        />
      </RechartsAreaChart>
    </ResponsiveContainer>
  );
}
