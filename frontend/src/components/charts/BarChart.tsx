'use client';

import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
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

interface BarChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  yKeys: string[];
  yLabels?: string[];
  colors?: string[];
  stacked?: boolean;
  horizontal?: boolean;
  showLegend?: boolean;
  legendPosition?: 'top' | 'bottom';
  showGrid?: boolean;
  formatValue?: (value: number) => string;
  formatLabel?: (label: string) => string;
}

export function BarChart({
  data,
  xKey,
  yKeys,
  yLabels,
  colors = CHART_COLORS,
  stacked = false,
  horizontal = false,
  showLegend = true,
  legendPosition = 'bottom',
  showGrid = true,
  formatValue = (v) => v.toLocaleString(),
  formatLabel = (l) => l,
}: BarChartProps) {
  const layout = horizontal ? 'vertical' : 'horizontal';

  // Custom legend renderer for better formatting with many series
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const renderLegend = (props: any) => {
    const { payload } = props;
    if (!payload) return null;

    // For many items, use a scrollable container
    const isLarge = payload.length > 8;

    return (
      <div className={`flex flex-wrap justify-center gap-x-3 gap-y-1.5 px-2 ${legendPosition === 'top' ? 'mb-4' : 'mt-4'} ${isLarge ? 'max-h-[60px] overflow-y-auto' : ''}`}>
        {payload.map((entry: { value: string; color: string }, index: number) => (
          <div key={`legend-${index}`} className="flex items-center gap-1.5">
            <div
              className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-xs text-muted-foreground truncate max-w-[80px]">
              {entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsBarChart
        data={data}
        layout={layout}
        margin={{ top: 20, right: 20, left: 10, bottom: showLegend && yKeys.length > 1 ? 10 : 5 }}
      >
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-border" opacity={0.5} />}

        {horizontal ? (
          <>
            <XAxis type="number" tickFormatter={formatValue} className="fill-muted-foreground" fontSize={11} tick={{ fill: 'currentColor' }} stroke="currentColor" />
            <YAxis
              type="category"
              dataKey={xKey}
              tickFormatter={formatLabel}
              className="fill-muted-foreground"
              fontSize={11}
              width={80}
              tick={{ fill: 'currentColor' }}
              stroke="currentColor"
            />
          </>
        ) : (
          <>
            <XAxis dataKey={xKey} tickFormatter={formatLabel} className="fill-muted-foreground" fontSize={11} tick={{ fill: 'currentColor' }} stroke="currentColor" />
            <YAxis tickFormatter={formatValue} className="fill-muted-foreground" fontSize={11} tick={{ fill: 'currentColor' }} stroke="currentColor" width={60} />
          </>
        )}

        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
            color: 'hsl(var(--card-foreground))',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            padding: '8px 12px',
            maxHeight: '300px',
            overflowY: 'auto',
          }}
          formatter={(value: number, name: string) => [formatValue(value), name]}
          labelFormatter={formatLabel}
        />

        {showLegend && yKeys.length > 1 && (
          <Legend
            content={renderLegend}
            verticalAlign={legendPosition}
          />
        )}

        {yKeys.map((key, index) => (
          <Bar
            key={key}
            dataKey={key}
            name={yLabels?.[index] || key}
            fill={colors[index % colors.length]}
            stackId={stacked ? 'stack' : undefined}
            radius={stacked ? 0 : [4, 4, 0, 0]}
          />
        ))}
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}

// Single series bar chart with individual colors per bar
interface SimpleBarChartProps {
  data: Record<string, unknown>[];
  xKey?: string;
  yKey?: string;
  horizontal?: boolean;
  showGrid?: boolean;
  formatValue?: (value: number) => string;
  formatLabel?: (label: string) => string;
}

export function SimpleBarChart({
  data,
  xKey = 'name',
  yKey = 'value',
  horizontal = false,
  showGrid = true,
  formatValue = (v) => v.toLocaleString(),
  formatLabel = (l) => l,
}: SimpleBarChartProps) {
  const layout = horizontal ? 'vertical' : 'horizontal';

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsBarChart
        data={data}
        layout={layout}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-border" opacity={0.5} />}

        {horizontal ? (
          <>
            <XAxis type="number" tickFormatter={formatValue} className="fill-muted-foreground" fontSize={12} tick={{ fill: 'currentColor' }} stroke="currentColor" />
            <YAxis
              type="category"
              dataKey={xKey}
              tickFormatter={formatLabel}
              className="fill-muted-foreground"
              fontSize={12}
              width={100}
              tick={{ fill: 'currentColor' }}
              stroke="currentColor"
            />
          </>
        ) : (
          <>
            <XAxis dataKey={xKey} tickFormatter={formatLabel} className="fill-muted-foreground" fontSize={12} tick={{ fill: 'currentColor' }} stroke="currentColor" />
            <YAxis tickFormatter={formatValue} className="fill-muted-foreground" fontSize={12} tick={{ fill: 'currentColor' }} stroke="currentColor" />
          </>
        )}

        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
            color: 'hsl(var(--card-foreground))',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          }}
          formatter={(value: number) => [formatValue(value), 'Value']}
          labelFormatter={formatLabel}
        />

        <Bar dataKey={yKey} radius={[4, 4, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={(entry as Record<string, unknown>).color as string || CHART_COLORS[index % CHART_COLORS.length]}
            />
          ))}
        </Bar>
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}
