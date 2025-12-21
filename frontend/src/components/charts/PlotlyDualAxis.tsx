'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import { getChartTheme, getBaseLayout, CHART_COLORS } from '@/lib/chartTheme';
import { useIsDark } from '@/hooks/useTheme';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface BarSeries {
  x: (string | number)[];
  y: number[];
  name: string;
  color?: string;
  yaxis?: 'y' | 'y2';
}

interface LineSeries {
  x: (string | number)[];
  y: number[];
  name: string;
  color?: string;
  width?: number;
  dash?: 'solid' | 'dash' | 'dot';
  yaxis?: 'y' | 'y2';
}

interface PlotlyDualAxisChartProps {
  bars?: BarSeries[];
  lines?: LineSeries[];
  title?: string;
  xAxisTitle?: string;
  yAxisTitle?: string;
  y2AxisTitle?: string;
  height?: number;
  barmode?: 'group' | 'stack';
  className?: string;
}

export function PlotlyDualAxisChart({
  bars = [],
  lines = [],
  title,
  xAxisTitle,
  yAxisTitle,
  y2AxisTitle,
  height = 500,
  barmode = 'group',
  className,
}: PlotlyDualAxisChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const traces = useMemo(() => {
    const barTraces = bars.map((bar) => ({
      type: 'bar' as const,
      x: bar.x,
      y: bar.y,
      name: bar.name,
      marker: { color: bar.color || CHART_COLORS.primary },
      yaxis: bar.yaxis || 'y',
      hovertemplate: `<b>${bar.name}</b><br>%{x}<br>%{y:,.2f}<extra></extra>`,
    }));

    const lineTraces = lines.map((line) => ({
      type: 'scatter' as const,
      mode: 'lines+markers' as const,
      x: line.x,
      y: line.y,
      name: line.name,
      line: {
        color: line.color || CHART_COLORS.success,
        width: line.width || 3,
        dash: line.dash || 'solid',
      },
      marker: { size: 6, color: line.color || CHART_COLORS.success },
      yaxis: line.yaxis || 'y2',
      hovertemplate: `<b>${line.name}</b><br>%{x}<br>%{y:,.2f}<extra></extra>`,
    }));

    return [...barTraces, ...lineTraces];
  }, [bars, lines]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      barmode,
      hovermode: 'x unified' as const,
      xaxis: {
        ...base.xaxis,
        title: { text: xAxisTitle, font: { color: theme.text_color, size: 12 } },
        tickangle: -45,
      },
      yaxis: {
        ...base.yaxis,
        title: { text: yAxisTitle, font: { color: theme.text_color, size: 12 } },
        side: 'left' as const,
      },
      yaxis2: {
        title: { text: y2AxisTitle, font: { color: theme.text_color, size: 12 } },
        overlaying: 'y' as const,
        side: 'right' as const,
        gridcolor: 'transparent',
        tickfont: { color: theme.secondary_text },
      },
      legend: {
        ...base.legend,
        orientation: 'h' as const,
        yanchor: 'bottom',
        y: 1.02,
        xanchor: 'center',
        x: 0.5,
      },
    };
  }, [theme, title, height, barmode, xAxisTitle, yAxisTitle, y2AxisTitle]);

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

// Specialized chart for cash flow analysis (FCF vs Dividends vs CapEx)
interface CashFlowChartProps {
  years: string[];
  fcf: number[];
  dividends: number[];
  capex: number[];
  title?: string;
  height?: number;
  className?: string;
}

export function PlotlyCashFlowChart({
  years,
  fcf,
  dividends,
  capex,
  title = 'Free Cash Flow vs Dividends & CapEx',
  height = 500,
  className,
}: CashFlowChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const traces = [
    {
      type: 'scatter' as const,
      mode: 'lines+markers' as const,
      x: years,
      y: fcf,
      name: 'Free Cash Flow',
      line: { color: CHART_COLORS.primary, width: 4 },
      marker: { size: 8 },
      hovertemplate: '<b>FCF</b><br>%{x}<br>%{y:,.2f}B<extra></extra>',
    },
    {
      type: 'scatter' as const,
      mode: 'lines+markers' as const,
      x: years,
      y: dividends,
      name: 'Dividends Paid',
      line: { color: CHART_COLORS.success, width: 3 },
      marker: { size: 6 },
      hovertemplate: '<b>Dividends</b><br>%{x}<br>%{y:,.2f}B<extra></extra>',
    },
    {
      type: 'scatter' as const,
      mode: 'lines+markers' as const,
      x: years,
      y: capex,
      name: 'Capital Expenditures',
      line: { color: CHART_COLORS.danger, width: 3 },
      marker: { size: 6 },
      hovertemplate: '<b>CapEx</b><br>%{x}<br>%{y:,.2f}B<extra></extra>',
    },
  ];

  const layout = {
    ...getBaseLayout(theme, title),
    height,
    hovermode: 'x unified' as const,
    xaxis: {
      title: { text: 'Year', font: { color: theme.text_color, size: 12 } },
      gridcolor: theme.grid_color,
    },
    yaxis: {
      title: { text: 'Amount ($ Billions)', font: { color: theme.text_color, size: 12 } },
      gridcolor: theme.grid_color,
    },
  };

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

// Payout ratio chart with safety zones
interface PayoutRatioChartProps {
  years: string[];
  values: number[];
  title?: string;
  height?: number;
  className?: string;
}

export function PlotlyPayoutRatioChart({
  years,
  values,
  title = 'Payout Ratio Over Time',
  height = 400,
  className,
}: PayoutRatioChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const traces = [
    {
      type: 'bar' as const,
      x: years,
      y: values,
      name: 'Payout Ratio',
      marker: { color: CHART_COLORS.purple },
      hovertemplate: '<b>%{x}</b><br>Payout Ratio: %{y:.1f}%<extra></extra>',
    },
  ];

  const layout = {
    ...getBaseLayout(theme, title),
    height,
    shapes: [
      // Safe zone (0-60%)
      {
        type: 'rect' as const,
        xref: 'paper' as const,
        yref: 'y' as const,
        x0: 0,
        x1: 1,
        y0: 0,
        y1: 60,
        fillcolor: 'rgba(34, 197, 94, 0.1)',
        line: { width: 0 },
        layer: 'below' as const,
      },
      // Caution zone (60-80%)
      {
        type: 'rect' as const,
        xref: 'paper' as const,
        yref: 'y' as const,
        x0: 0,
        x1: 1,
        y0: 60,
        y1: 80,
        fillcolor: 'rgba(245, 158, 11, 0.1)',
        line: { width: 0 },
        layer: 'below' as const,
      },
      // Risk zone (80%+)
      {
        type: 'rect' as const,
        xref: 'paper' as const,
        yref: 'y' as const,
        x0: 0,
        x1: 1,
        y0: 80,
        y1: Math.max(...values, 100) + 20,
        fillcolor: 'rgba(239, 68, 68, 0.1)',
        line: { width: 0 },
        layer: 'below' as const,
      },
    ],
    annotations: [
      { x: 1.02, y: 30, xref: 'paper' as const, yref: 'y' as const, text: 'Safe', showarrow: false, font: { size: 10, color: CHART_COLORS.success } },
      { x: 1.02, y: 70, xref: 'paper' as const, yref: 'y' as const, text: 'Caution', showarrow: false, font: { size: 10, color: CHART_COLORS.warning } },
      { x: 1.02, y: 90, xref: 'paper' as const, yref: 'y' as const, text: 'Risk', showarrow: false, font: { size: 10, color: CHART_COLORS.danger } },
    ],
    xaxis: {
      title: { text: 'Year', font: { color: theme.text_color, size: 12 } },
      gridcolor: theme.grid_color,
    },
    yaxis: {
      title: { text: 'Payout Ratio (%)', font: { color: theme.text_color, size: 12 } },
      gridcolor: theme.grid_color,
      range: [0, Math.max(...values, 100) + 20],
    },
  };

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
