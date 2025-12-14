'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import { getChartTheme, getBaseLayout, QUALITATIVE_COLORS } from '@/lib/chartTheme';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export interface LineChartData {
  x: (string | number | Date)[];
  y: number[];
  name?: string;
  color?: string;
  dash?: 'solid' | 'dash' | 'dot' | 'dashdot';
  width?: number;
  showMarkers?: boolean;
}

interface PlotlyLineChartProps {
  data: LineChartData | LineChartData[];
  title?: string;
  xAxisTitle?: string;
  yAxisTitle?: string;
  height?: number;
  showLegend?: boolean;
  showMarkers?: boolean;
  curveType?: 'linear' | 'spline';
  hoverMode?: 'closest' | 'x' | 'x unified';
  xAxisFormat?: string; // e.g., '%b %Y' for month year
  yAxisFormat?: string;
  className?: string;
}

export function PlotlyLineChart({
  data,
  title,
  xAxisTitle,
  yAxisTitle,
  height = 400,
  showLegend = true,
  showMarkers = true,
  curveType = 'spline',
  hoverMode = 'x unified',
  xAxisFormat,
  yAxisFormat,
  className,
}: PlotlyLineChartProps) {
  const theme = getChartTheme(true);

  const traces = useMemo(() => {
    const dataArray = Array.isArray(data) ? data : [data];

    return dataArray.map((d, idx) => ({
      type: 'scatter' as const,
      mode: (d.showMarkers !== false && showMarkers) ? 'lines+markers' as const : 'lines' as const,
      x: d.x,
      y: d.y,
      name: d.name || `Series ${idx + 1}`,
      line: {
        color: d.color || QUALITATIVE_COLORS[idx % QUALITATIVE_COLORS.length],
        width: d.width || 3,
        dash: d.dash || 'solid',
        shape: curveType,
      },
      marker: {
        size: 6,
        color: d.color || QUALITATIVE_COLORS[idx % QUALITATIVE_COLORS.length],
      },
      hovertemplate: `<b>%{x}</b><br>%{y:,.2f}<extra>${d.name || ''}</extra>`,
    }));
  }, [data, showMarkers, curveType]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      showlegend: showLegend && (Array.isArray(data) ? data.length > 1 : false),
      hovermode: hoverMode,
      xaxis: {
        ...base.xaxis,
        title: { text: xAxisTitle, font: { color: theme.text_color, size: 12 } },
        tickformat: xAxisFormat,
        tickangle: -45,
      },
      yaxis: {
        ...base.yaxis,
        title: { text: yAxisTitle, font: { color: theme.text_color, size: 12 } },
        tickformat: yAxisFormat,
      },
    };
  }, [theme, title, height, showLegend, data, xAxisTitle, yAxisTitle, hoverMode, xAxisFormat, yAxisFormat]);

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'] as Plotly.ModeBarDefaultButtons[],
    responsive: true,
  };

  return (
    <div className={className}>
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

// Specialized component for scatter plot with moving average
interface ScatterWithMAProps {
  x: (string | Date)[];
  y: number[];
  title?: string;
  xAxisTitle?: string;
  yAxisTitle?: string;
  height?: number;
  maWindow?: number;
  className?: string;
}

export function PlotlyScatterWithMA({
  x,
  y,
  title,
  xAxisTitle,
  yAxisTitle,
  height = 500,
  maWindow = 3,
  className,
}: ScatterWithMAProps) {
  const theme = getChartTheme(true);

  // Calculate moving average
  const ma = useMemo(() => {
    if (y.length < maWindow) return [];
    const result: (number | null)[] = [];
    for (let i = 0; i < y.length; i++) {
      if (i < maWindow - 1) {
        result.push(null);
      } else {
        const sum = y.slice(i - maWindow + 1, i + 1).reduce((a, b) => a + b, 0);
        result.push(sum / maWindow);
      }
    }
    return result;
  }, [y, maWindow]);

  const traces = [
    {
      type: 'scatter' as const,
      mode: 'markers' as const,
      x,
      y,
      name: 'Individual Payments',
      marker: {
        size: 10,
        color: QUALITATIVE_COLORS[0],
      },
      hovertemplate: '<b>%{x}</b><br>%{y:,.2f}<extra></extra>',
    },
    ...(ma.length > 0 ? [{
      type: 'scatter' as const,
      mode: 'lines' as const,
      x,
      y: ma,
      name: `${maWindow}-Point Moving Average`,
      line: {
        color: 'rgba(255, 165, 0, 0.7)',
        width: 3,
      },
      hovertemplate: '<b>%{x}</b><br>MA: %{y:,.2f}<extra></extra>',
    }] : []),
  ];

  const layout = {
    ...getBaseLayout(theme, title),
    height,
    hovermode: 'closest' as const,
    xaxis: {
      title: { text: xAxisTitle, font: { color: theme.text_color, size: 12 } },
      gridcolor: theme.grid_color,
      tickangle: -45,
    },
    yaxis: {
      title: { text: yAxisTitle, font: { color: theme.text_color, size: 12 } },
      gridcolor: theme.grid_color,
    },
  };

  const config = {
    displayModeBar: true,
    displaylogo: false,
    responsive: true,
  };

  return (
    <div className={className}>
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
