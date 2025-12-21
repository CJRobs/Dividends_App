'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import { getChartTheme, getBaseLayout, QUALITATIVE_COLORS } from '@/lib/chartTheme';
import { useIsDark } from '@/hooks/useTheme';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface PlotlyPieChartProps {
  labels: string[];
  values: number[];
  title?: string;
  height?: number;
  hole?: number; // 0 for pie, 0.4 for donut
  showLegend?: boolean;
  textInfo?: 'percent' | 'label' | 'value' | 'percent+label' | 'label+value' | 'none';
  className?: string;
}

export function PlotlyPieChart({
  labels,
  values,
  title,
  height = 400,
  hole = 0,
  showLegend = true,
  textInfo = 'percent+label',
  className,
}: PlotlyPieChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const trace = useMemo(() => ({
    type: 'pie' as const,
    labels,
    values,
    hole,
    marker: {
      colors: QUALITATIVE_COLORS,
      line: { color: '#ffffff', width: 2 },
    },
    textinfo: textInfo,
    textposition: 'inside' as const,
    textfont: { color: '#ffffff', size: 11 },
    insidetextorientation: 'radial' as const,
    hovertemplate: '<b>%{label}</b><br>%{value:,.2f}<br>%{percent}<extra></extra>',
  }), [labels, values, hole, textInfo]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      showlegend: showLegend,
      legend: {
        ...base.legend,
        orientation: 'v' as const,
        yanchor: 'middle',
        y: 0.5,
        xanchor: 'left',
        x: 1.02,
      },
    };
  }, [theme, title, height, showLegend]);

  const config = {
    displayModeBar: false,
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

// Donut chart variant with center text support
interface PlotlyDonutChartProps extends Omit<PlotlyPieChartProps, 'hole'> {
  centerText?: string;
  centerValue?: string;
}

export function PlotlyDonutChart({
  labels,
  values,
  title,
  height = 400,
  showLegend = true,
  textInfo = 'percent+label',
  centerText,
  centerValue,
  className,
}: PlotlyDonutChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const trace = useMemo(() => ({
    type: 'pie' as const,
    labels,
    values,
    hole: 0.4,
    marker: {
      colors: QUALITATIVE_COLORS,
      line: { color: '#ffffff', width: 2 },
    },
    textinfo: textInfo,
    textposition: 'inside' as const,
    textfont: { color: '#ffffff', size: 10 },
    insidetextorientation: 'radial' as const,
    hovertemplate: '<b>%{label}</b><br>%{value:,.2f}<br>%{percent}<extra></extra>',
  }), [labels, values, textInfo]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    const annotations = centerText || centerValue ? [
      ...(centerValue ? [{
        text: centerValue,
        font: { size: 20, color: theme.text_color, weight: 700 },
        showarrow: false,
        x: 0.5,
        y: 0.55,
      }] : []),
      ...(centerText ? [{
        text: centerText,
        font: { size: 12, color: theme.secondary_text },
        showarrow: false,
        x: 0.5,
        y: 0.45,
      }] : []),
    ] : undefined;

    return {
      ...base,
      height,
      showlegend: showLegend,
      annotations,
      legend: {
        ...base.legend,
        orientation: 'v' as const,
        yanchor: 'middle',
        y: 0.5,
        xanchor: 'left',
        x: 1.02,
      },
    };
  }, [theme, title, height, showLegend, centerText, centerValue]);

  const config = {
    displayModeBar: false,
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
