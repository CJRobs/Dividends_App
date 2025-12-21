'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import { getChartTheme, getBaseLayout, QUALITATIVE_COLORS } from '@/lib/chartTheme';
import { useIsDark } from '@/hooks/useTheme';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface StackedBarData {
  periods: string[];
  series: {
    name: string;
    values: number[];
  }[];
}

interface PlotlyStackedBarChartProps {
  data: StackedBarData;
  title?: string;
  xAxisTitle?: string;
  yAxisTitle?: string;
  height?: number;
  currency?: string;
  showTextLabels?: boolean;
  className?: string;
}

export function PlotlyStackedBarChart({
  data,
  title,
  xAxisTitle,
  yAxisTitle,
  height = 600,
  currency = '£',
  showTextLabels = true,
  className,
}: PlotlyStackedBarChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const traces = useMemo(() => {
    return data.series.map((series, idx) => ({
      type: 'bar' as const,
      name: series.name,
      x: data.periods,
      y: series.values,
      text: showTextLabels ? series.values.map(v => v > 0 ? `${currency}${v.toFixed(0)}` : '') : undefined,
      textposition: 'inside' as const,
      textfont: { color: '#ffffff', size: 10 },
      insidetextanchor: 'middle' as const,
      marker: {
        color: QUALITATIVE_COLORS[idx % QUALITATIVE_COLORS.length],
      },
      hovertemplate: `<b>${series.name}</b><br>Period: %{x}<br>Amount: ${currency}%{y:,.2f}<extra></extra>`,
    }));
  }, [data, currency, showTextLabels]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      barmode: 'stack' as const,
      xaxis: {
        ...base.xaxis,
        title: { text: xAxisTitle || 'Time Period', font: { color: theme.text_color, size: 12 } },
        tickangle: -45,
      },
      yaxis: {
        ...base.yaxis,
        title: { text: yAxisTitle || `Dividend Amount (${currency})`, font: { color: theme.text_color, size: 12 } },
      },
      legend: {
        ...base.legend,
        title: { text: 'Stock', font: { color: theme.text_color, size: 12 } },
        orientation: 'v' as const,
        yanchor: 'top',
        y: 1,
        xanchor: 'left',
        x: 1.02,
      },
    };
  }, [theme, title, height, xAxisTitle, yAxisTitle, currency]);

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'] as Plotly.ModeBarDefaultButtons[],
    responsive: true,
  };

  return (
    <div className={className} style={{ width: '100%', height }}>
      <Plot
        data={traces}
        layout={layout}
        config={config}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
      />
    </div>
  );
}

// Grouped bar chart for comparison (Assets vs Liabilities vs Equity)
interface GroupedBarData {
  categories: string[];
  series: {
    name: string;
    values: number[];
    color?: string;
  }[];
}

interface PlotlyGroupedBarChartProps {
  data: GroupedBarData;
  title?: string;
  xAxisTitle?: string;
  yAxisTitle?: string;
  height?: number;
  className?: string;
}

const DEFAULT_GROUP_COLORS = [QUALITATIVE_COLORS[0], QUALITATIVE_COLORS[3], QUALITATIVE_COLORS[1]]; // Blue, Red, Green

export function PlotlyGroupedBarChart({
  data,
  title,
  xAxisTitle,
  yAxisTitle,
  height = 500,
  className,
}: PlotlyGroupedBarChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const traces = useMemo(() => {
    return data.series.map((series, idx) => ({
      type: 'bar' as const,
      name: series.name,
      x: data.categories,
      y: series.values,
      marker: {
        color: series.color || DEFAULT_GROUP_COLORS[idx % DEFAULT_GROUP_COLORS.length],
      },
      hovertemplate: `<b>${series.name}</b><br>%{x}<br>%{y:,.2f}B<extra></extra>`,
    }));
  }, [data]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      barmode: 'group' as const,
      xaxis: {
        ...base.xaxis,
        title: { text: xAxisTitle || 'Year', font: { color: theme.text_color, size: 12 } },
      },
      yaxis: {
        ...base.yaxis,
        title: { text: yAxisTitle || 'Amount ($ Billions)', font: { color: theme.text_color, size: 12 } },
      },
    };
  }, [theme, title, height, xAxisTitle, yAxisTitle]);

  const config = {
    displayModeBar: true,
    displaylogo: false,
    responsive: true,
  };

  return (
    <div className={className} style={{ width: '100%', height }}>
      <Plot
        data={traces}
        layout={layout}
        config={config}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
      />
    </div>
  );
}
