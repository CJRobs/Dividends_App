'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import { getChartTheme, getBaseLayout } from '@/lib/chartTheme';
import { useIsDark } from '@/hooks/useTheme';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface HeatmapDataPoint {
  row: string;
  col: string;
  value: number;
}

interface PlotlyHeatmapProps {
  data: HeatmapDataPoint[];
  rows: string[];
  cols: string[];
  title?: string;
  height?: number;
  colorScale?: 'blues' | 'greens' | 'oranges' | 'purples' | 'viridis';
  showValues?: boolean;
  currency?: string;
  className?: string;
}

export function PlotlyHeatmap({
  data,
  rows,
  cols,
  title,
  height = 400,
  colorScale = 'blues',
  showValues = true,
  currency = '£',
  className,
}: PlotlyHeatmapProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  // Build the z-matrix (rows x cols)
  const { zValues, textValues } = useMemo(() => {
    // Create lookup map
    const valueMap = new Map<string, number>();
    data.forEach((item) => {
      valueMap.set(`${item.row}-${item.col}`, item.value);
    });

    // Build z-matrix (each row is a row in the heatmap)
    const zMatrix: number[][] = [];
    const textMatrix: string[][] = [];

    rows.forEach((row) => {
      const rowValues: number[] = [];
      const rowTexts: string[] = [];
      cols.forEach((col) => {
        const value = valueMap.get(`${row}-${col}`) || 0;
        rowValues.push(value);
        rowTexts.push(value > 0 ? `${currency}${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : '-');
      });
      zMatrix.push(rowValues);
      textMatrix.push(rowTexts);
    });

    return { zValues: zMatrix, textValues: textMatrix };
  }, [data, rows, cols, currency]);

  // Color scale mapping
  const plotlyColorScale = useMemo(() => {
    switch (colorScale) {
      case 'blues':
        return [
          [0, '#1e3a5f'],
          [0.5, '#3b82f6'],
          [1, '#93c5fd'],
        ];
      case 'greens':
        return [
          [0, '#14532d'],
          [0.5, '#10b981'],
          [1, '#86efac'],
        ];
      case 'oranges':
        return [
          [0, '#7c2d12'],
          [0.5, '#f59e0b'],
          [1, '#fcd34d'],
        ];
      case 'purples':
        return [
          [0, '#3b0764'],
          [0.5, '#8b5cf6'],
          [1, '#c4b5fd'],
        ];
      case 'viridis':
      default:
        return 'Viridis';
    }
  }, [colorScale]);

  const traces = useMemo(() => {
    return [{
      type: 'heatmap' as const,
      z: zValues,
      x: cols,
      y: rows,
      text: showValues ? textValues : undefined,
      texttemplate: showValues ? '%{text}' : undefined,
      textfont: { color: '#ffffff', size: 10 },
      colorscale: plotlyColorScale,
      showscale: true,
      colorbar: {
        title: { text: 'Amount', font: { color: theme.text_color, size: 11 } },
        tickfont: { color: theme.secondary_text, size: 10 },
        tickprefix: currency,
      },
      hovertemplate: '<b>%{y}</b> - %{x}<br>%{z:,.2f}<extra></extra>',
      xgap: 1,
      ygap: 1,
    }];
  }, [zValues, cols, rows, textValues, showValues, plotlyColorScale, theme, currency]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      xaxis: {
        ...base.xaxis,
        side: 'top' as const,
        tickangle: 0,
      },
      yaxis: {
        ...base.yaxis,
        autorange: 'reversed' as const,
      },
      margin: { l: 60, r: 80, t: title ? 80 : 60, b: 40 },
    };
  }, [theme, title, height]);

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
