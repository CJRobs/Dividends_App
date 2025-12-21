'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import { getChartTheme, getBaseLayout, CHART_COLORS } from '@/lib/chartTheme';
import { useIsDark } from '@/hooks/useTheme';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface ForecastDataPoint {
  date: string;
  actual?: number;
  forecast?: number;
  lower?: number;
  upper?: number;
  tracking?: number;
}

interface PlotlyForecastChartProps {
  data: ForecastDataPoint[];
  height?: number;
  currency?: string;
  title?: string;
  className?: string;
}

export function PlotlyForecastChart({
  data,
  height = 400,
  currency = '£',
  title,
  className,
}: PlotlyForecastChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const traces = useMemo(() => {
    const actualData = data.filter(d => d.actual !== undefined);
    const forecastData = data.filter(d => d.forecast !== undefined);
    const trackingData = data.filter(d => d.tracking !== undefined);
    const hasConfidenceInterval = forecastData.some(d => d.lower !== undefined && d.upper !== undefined);

    const traces: Plotly.Data[] = [];

    // Confidence interval (upper bound fill)
    if (hasConfidenceInterval) {
      traces.push({
        type: 'scatter',
        name: 'Upper Bound',
        x: forecastData.map(d => d.date),
        y: forecastData.map(d => d.upper),
        mode: 'lines',
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
      });

      traces.push({
        type: 'scatter',
        name: 'Confidence Interval',
        x: forecastData.map(d => d.date),
        y: forecastData.map(d => d.lower),
        mode: 'lines',
        fill: 'tonexty',
        fillcolor: 'rgba(59, 130, 246, 0.15)',
        line: { width: 0 },
        hovertemplate: `95% CI: ${currency}%{customdata[0]:,.2f} - ${currency}%{customdata[1]:,.2f}<extra></extra>`,
        customdata: forecastData.map(d => [d.lower, d.upper]),
      });
    }

    // Historical/Actual line
    if (actualData.length > 0) {
      traces.push({
        type: 'scatter',
        name: 'Actual',
        x: actualData.map(d => d.date),
        y: actualData.map(d => d.actual),
        mode: 'lines+markers',
        line: {
          color: CHART_COLORS.success,
          width: 2,
          shape: 'spline',
        },
        marker: {
          color: CHART_COLORS.success,
          size: 6,
          symbol: 'circle',
        },
        hovertemplate: `<b>Actual</b><br>%{x}<br>${currency}%{y:,.2f}<extra></extra>`,
      });
    }

    // Forecast line
    if (forecastData.length > 0) {
      // Connect to last actual point for visual continuity
      const lastActual = actualData[actualData.length - 1];
      const xValues = lastActual
        ? [lastActual.date, ...forecastData.map(d => d.date)]
        : forecastData.map(d => d.date);
      const yValues = lastActual
        ? [lastActual.actual, ...forecastData.map(d => d.forecast)]
        : forecastData.map(d => d.forecast);

      traces.push({
        type: 'scatter',
        name: 'Forecast',
        x: xValues,
        y: yValues,
        mode: 'lines+markers',
        line: {
          color: CHART_COLORS.primary,
          width: 2,
          dash: 'dash',
          shape: 'spline',
        },
        marker: {
          color: CHART_COLORS.primary,
          size: 6,
          symbol: 'circle',
        },
        hovertemplate: `<b>Forecast</b><br>%{x}<br>${currency}%{y:,.2f}<extra></extra>`,
      });
    }

    // Current month tracking point (partial data)
    if (trackingData.length > 0) {
      traces.push({
        type: 'scatter',
        name: 'Current Month (Partial)',
        x: trackingData.map(d => d.date),
        y: trackingData.map(d => d.tracking),
        mode: 'markers',
        marker: {
          color: CHART_COLORS.warning,
          size: 14,
          symbol: 'circle',
          line: {
            color: '#ffffff',
            width: 3,
          },
        },
        hovertemplate: `<b>Current Month (Partial)</b><br>%{x}<br>${currency}%{y:,.2f}<extra></extra>`,
      });
    }

    return traces;
  }, [data, currency]);

  // Get all dates in order for the category array
  const allDates = useMemo(() => {
    return data.map(d => d.date);
  }, [data]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      xaxis: {
        ...base.xaxis,
        tickangle: -45,
        type: 'category' as const,
        categoryorder: 'array' as const,
        categoryarray: allDates,
      },
      yaxis: {
        ...base.yaxis,
        title: { text: `Dividend Amount (${currency})`, font: { color: theme.text_color, size: 12 } },
        tickformat: `${currency},.0f`,
        tickprefix: currency,
      },
      legend: {
        ...base.legend,
        orientation: 'h' as const,
        yanchor: 'bottom',
        y: 1.02,
        xanchor: 'center',
        x: 0.5,
      },
      hovermode: 'x unified' as const,
    };
  }, [theme, title, height, currency, allDates]);

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

// Simple bar chart for annual projections
interface AnnualProjection {
  year: string;
  projected: number;
}

interface PlotlyProjectionBarChartProps {
  data: AnnualProjection[];
  height?: number;
  currency?: string;
  title?: string;
  className?: string;
}

export function PlotlyProjectionBarChart({
  data,
  height = 200,
  currency = '£',
  title,
  className,
}: PlotlyProjectionBarChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const traces = useMemo(() => {
    return [{
      type: 'bar' as const,
      x: data.map(d => d.year),
      y: data.map(d => d.projected),
      marker: {
        color: CHART_COLORS.primary,
        line: {
          color: CHART_COLORS.primary,
          width: 1,
        },
      },
      text: data.map(d => `${currency}${d.projected.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`),
      textposition: 'outside' as const,
      textfont: {
        color: theme.text_color,
        size: 11,
      },
      hovertemplate: `<b>%{x}</b><br>Projected: ${currency}%{y:,.2f}<extra></extra>`,
    }];
  }, [data, currency, theme]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      bargap: 0.3,
      xaxis: {
        ...base.xaxis,
        title: undefined,
      },
      yaxis: {
        ...base.yaxis,
        title: { text: `Projected (${currency})`, font: { color: theme.text_color, size: 12 } },
        tickprefix: currency,
      },
      showlegend: false,
    };
  }, [theme, title, height, currency]);

  const config = {
    displayModeBar: false,
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
