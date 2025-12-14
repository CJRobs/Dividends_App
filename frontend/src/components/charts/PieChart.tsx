'use client';

import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieLabelRenderProps,
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
  '#ec4899', // pink
  '#84cc16', // lime
  '#06b6d4', // cyan
  '#f97316', // orange
];

interface PieChartProps {
  data: { name: string; value: number; color?: string }[];
  colors?: string[];
  showLegend?: boolean;
  legendPosition?: 'right' | 'bottom';
  innerRadius?: number;
  outerRadius?: number;
  formatValue?: (value: number) => string;
  showLabels?: boolean;
}

export function PieChart({
  data,
  colors = CHART_COLORS,
  showLegend = true,
  legendPosition = 'bottom',
  innerRadius = 0,
  outerRadius = 80,
  formatValue = (v) => v.toLocaleString(),
  showLabels = false,
}: PieChartProps) {
  const renderLabel = (props: PieLabelRenderProps) => {
    const { name, percent } = props;
    if (typeof percent !== 'number') return null;
    return `${name}: ${(percent * 100).toFixed(1)}%`;
  };

  // Custom legend renderer for better formatting
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const renderLegend = (props: any) => {
    const { payload } = props;
    if (!payload) return null;

    if (legendPosition === 'bottom') {
      return (
        <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 mt-4 px-2">
          {payload.map((entry: { value: string; color: string }, index: number) => (
            <div key={`legend-${index}`} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-sm flex-shrink-0"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-muted-foreground truncate max-w-[120px]">
                {entry.value}
              </span>
            </div>
          ))}
        </div>
      );
    }

    return (
      <div className="flex flex-col gap-2 pl-4">
        {payload.map((entry: { value: string; color: string }, index: number) => (
          <div key={`legend-${index}`} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-sm flex-shrink-0"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm text-muted-foreground truncate max-w-[100px]">
              {entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  };

  // Adjust pie position based on legend position
  const pieCenter = legendPosition === 'right' ? '40%' : '50%';

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsPieChart margin={{ top: 10, right: 10, left: 10, bottom: legendPosition === 'bottom' ? 10 : 5 }}>
        <Pie
          data={data}
          cx={pieCenter}
          cy="45%"
          labelLine={showLabels}
          label={showLabels ? renderLabel : undefined}
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.color || colors[index % colors.length]}
              stroke="hsl(var(--card))"
              strokeWidth={2}
            />
          ))}
        </Pie>

        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
            color: 'hsl(var(--card-foreground))',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            padding: '8px 12px',
          }}
          formatter={(value: number, name: string) => [formatValue(value), name]}
        />

        {showLegend && (
          <Legend
            content={renderLegend}
            layout={legendPosition === 'bottom' ? 'horizontal' : 'vertical'}
            align={legendPosition === 'bottom' ? 'center' : 'right'}
            verticalAlign={legendPosition === 'bottom' ? 'bottom' : 'middle'}
          />
        )}
      </RechartsPieChart>
    </ResponsiveContainer>
  );
}

// Donut chart variant
interface DonutChartProps extends PieChartProps {
  centerLabel?: string;
  centerValue?: string;
}

export function DonutChart({
  data,
  colors = CHART_COLORS,
  showLegend = true,
  legendPosition = 'bottom',
  formatValue = (v) => v.toLocaleString(),
  centerLabel,
  centerValue,
}: DonutChartProps) {
  // Custom legend renderer for better formatting
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const renderLegend = (props: any) => {
    const { payload } = props;
    if (!payload) return null;

    if (legendPosition === 'bottom') {
      return (
        <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 mt-4 px-2">
          {payload.map((entry: { value: string; color: string }, index: number) => (
            <div key={`legend-${index}`} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-sm flex-shrink-0"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-muted-foreground truncate max-w-[120px]">
                {entry.value}
              </span>
            </div>
          ))}
        </div>
      );
    }

    return (
      <div className="flex flex-col gap-2 pl-4">
        {payload.map((entry: { value: string; color: string }, index: number) => (
          <div key={`legend-${index}`} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-sm flex-shrink-0"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm text-muted-foreground truncate max-w-[100px]">
              {entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  };

  // Adjust pie position based on legend position
  const pieCenter = legendPosition === 'right' ? '35%' : '50%';

  return (
    <ResponsiveContainer width="100%" height="100%">
      <RechartsPieChart margin={{ top: 10, right: 10, left: 10, bottom: legendPosition === 'bottom' ? 10 : 5 }}>
        <Pie
          data={data}
          cx={pieCenter}
          cy="45%"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.color || colors[index % colors.length]}
              stroke="hsl(var(--card))"
              strokeWidth={2}
            />
          ))}
        </Pie>

        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '8px',
            color: 'hsl(var(--card-foreground))',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            padding: '8px 12px',
          }}
          formatter={(value: number, name: string) => [formatValue(value), name]}
        />

        {showLegend && (
          <Legend
            content={renderLegend}
            layout={legendPosition === 'bottom' ? 'horizontal' : 'vertical'}
            align={legendPosition === 'bottom' ? 'center' : 'right'}
            verticalAlign={legendPosition === 'bottom' ? 'bottom' : 'middle'}
          />
        )}

        {/* Center text overlay */}
        {(centerLabel || centerValue) && (
          <text
            x={pieCenter}
            y="45%"
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-foreground"
          >
            {centerValue && (
              <tspan x={pieCenter} dy="-0.3em" fontSize="20" fontWeight="bold" className="fill-card-foreground">
                {centerValue}
              </tspan>
            )}
            {centerLabel && (
              <tspan x={pieCenter} dy="1.4em" fontSize="11" className="fill-muted-foreground">
                {centerLabel}
              </tspan>
            )}
          </text>
        )}
      </RechartsPieChart>
    </ResponsiveContainer>
  );
}
