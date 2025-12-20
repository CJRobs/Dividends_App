'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import { getChartTheme, getBaseLayout, QUALITATIVE_COLORS, getGrowthColors } from '@/lib/chartTheme';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export interface BarChartData {
  x: (string | number)[];
  y: number[];
  name?: string;
}

// New simplified interface for single series
interface SimpleBarChartProps {
  labels: (string | number)[];
  values: number[];
  title?: string;
  xAxisTitle?: string;
  yAxisTitle?: string;
  height?: number;
  orientation?: 'vertical' | 'horizontal';
  color?: string;
  conditionalColors?: boolean; // Green/red based on positive/negative
  showValues?: boolean;
  textPosition?: 'inside' | 'outside' | 'auto' | 'none';
  valueFormat?: string;
  valuePrefix?: string;
  valueSuffix?: string;
  className?: string;
}

// Original complex interface
interface ComplexBarChartProps {
  data: BarChartData | BarChartData[];
  title?: string;
  xAxisTitle?: string;
  yAxisTitle?: string;
  height?: number;
  orientation?: 'v' | 'h';
  barmode?: 'group' | 'stack' | 'overlay';
  showLegend?: boolean;
  colorByValue?: boolean;
  textTemplate?: string;
  textPosition?: 'inside' | 'outside' | 'auto' | 'none';
  hoverTemplate?: string;
  className?: string;
}

// Simple bar chart component for labels/values interface
export function PlotlyBarChart({
  labels,
  values,
  title,
  xAxisTitle,
  yAxisTitle,
  height = 400,
  orientation = 'vertical',
  color,
  conditionalColors = false,
  showValues = false,
  textPosition = 'none',
  valueFormat = ',.2f',
  valuePrefix = '',
  valueSuffix = '',
  className,
}: SimpleBarChartProps) {
  const theme = getChartTheme(true);
  const isVertical = orientation === 'vertical';
  const colors = conditionalColors ? getGrowthColors(values) : (color || QUALITATIVE_COLORS[0]);

  const trace = useMemo(() => ({
    type: 'bar' as const,
    x: isVertical ? labels : values,
    y: isVertical ? values : labels,
    orientation: isVertical ? 'v' as const : 'h' as const,
    marker: {
      color: colors,
      line: { color: 'rgba(255,255,255,0.1)', width: 1 },
    },
    text: showValues ? values.map(v => `${valuePrefix}${v.toFixed(valueFormat.includes('f') ? parseInt(valueFormat.match(/\.(\d+)f/)?.[1] || '2') : 2)}${valueSuffix}`) : undefined,
    textposition: showValues && textPosition !== 'none' ? textPosition : undefined,
    textfont: { color: textPosition === 'inside' ? '#ffffff' : theme.text_color, size: 11 },
    hovertemplate: `<b>%{${isVertical ? 'x' : 'y'}}</b><br>${valuePrefix}%{${isVertical ? 'y' : 'x'}:${valueFormat}}${valueSuffix}<extra></extra>`,
  }), [labels, values, isVertical, colors, showValues, textPosition, valueFormat, valuePrefix, valueSuffix, theme]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      showlegend: false,
      xaxis: {
        ...base.xaxis,
        title: { text: isVertical ? xAxisTitle : yAxisTitle, font: { color: theme.text_color, size: 12 } },
        tickangle: isVertical ? -45 : 0,
        categoryorder: !isVertical ? 'total ascending' as const : undefined,
      },
      yaxis: {
        ...base.yaxis,
        title: { text: isVertical ? yAxisTitle : xAxisTitle, font: { color: theme.text_color, size: 12 } },
      },
    };
  }, [theme, title, height, isVertical, xAxisTitle, yAxisTitle]);

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'] as Plotly.ModeBarDefaultButtons[],
    responsive: true,
  };

  return (
    <div className={className} style={{ width: '100%', height }}>
      <Plot
        data={[trace]}
        layout={layout}
        config={config}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler
      />
    </div>
  );
}

// Complex bar chart component for data array interface
export function PlotlyMultiBarChart({
  data,
  title,
  xAxisTitle,
  yAxisTitle,
  height = 400,
  orientation = 'v',
  barmode = 'group',
  showLegend = true,
  colorByValue = false,
  textTemplate,
  textPosition = 'none',
  hoverTemplate,
  className,
}: ComplexBarChartProps) {
  const theme = getChartTheme(true);

  const traces = useMemo(() => {
    const dataArray = Array.isArray(data) ? data : [data];

    return dataArray.map((d, idx) => {
      const colors = colorByValue ? getGrowthColors(d.y) : QUALITATIVE_COLORS[idx % QUALITATIVE_COLORS.length];

      return {
        type: 'bar' as const,
        x: orientation === 'v' ? d.x : d.y,
        y: orientation === 'v' ? d.y : d.x,
        name: d.name || `Series ${idx + 1}`,
        orientation,
        marker: {
          color: colors,
          line: { color: 'rgba(255,255,255,0.1)', width: 1 },
        },
        text: textPosition !== 'none' ? d.y.map(v => v.toLocaleString()) : undefined,
        texttemplate: textTemplate,
        textposition: textPosition !== 'none' ? textPosition : undefined,
        textfont: { color: textPosition === 'inside' ? '#ffffff' : theme.text_color, size: 10 },
        hovertemplate: hoverTemplate || `<b>%{${orientation === 'v' ? 'x' : 'y'}}</b><br>%{${orientation === 'v' ? 'y' : 'x'}:,.2f}<extra>${d.name || ''}</extra>`,
      };
    });
  }, [data, orientation, colorByValue, textTemplate, textPosition, hoverTemplate, theme]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      barmode,
      showlegend: showLegend && (Array.isArray(data) ? data.length > 1 : false),
      xaxis: {
        ...base.xaxis,
        title: { text: orientation === 'v' ? xAxisTitle : yAxisTitle, font: { color: theme.text_color, size: 12 } },
        tickangle: orientation === 'v' ? -45 : 0,
        categoryorder: orientation === 'h' ? 'total ascending' as const : undefined,
      },
      yaxis: {
        ...base.yaxis,
        title: { text: orientation === 'v' ? yAxisTitle : xAxisTitle, font: { color: theme.text_color, size: 12 } },
      },
      legend: showLegend ? {
        ...base.legend,
        orientation: 'v' as const,
        yanchor: 'top',
        y: 1,
        xanchor: 'left',
        x: 1.02,
      } : undefined,
    };
  }, [theme, title, height, barmode, showLegend, data, xAxisTitle, yAxisTitle, orientation]);

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
