'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import {
  getChartTheme,
  getBaseLayout,
  QUALITATIVE_COLORS,
  CHART_TYPOGRAPHY,
  colorWithOpacity,
} from '@/lib/chartTheme';
import { useIsDark } from '@/hooks/useTheme';
import { cn } from '@/lib/utils';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

// =============================================================================
// TYPES
// =============================================================================

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
  /** Show confidence bands with gradient fill */
  showConfidenceBands?: boolean;
  /** Confidence band opacity (0-1) */
  bandOpacity?: number;
  className?: string;
}

// =============================================================================
// PREMIUM FORECAST CHART
// =============================================================================

export function PlotlyForecastChart({
  data,
  height = 400,
  currency = '£',
  title,
  showConfidenceBands = true,
  bandOpacity = 0.12,
  className,
}: PlotlyForecastChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  // Color definitions for forecast chart
  const colors = {
    actual: QUALITATIVE_COLORS[0], // Emerald
    forecast: QUALITATIVE_COLORS[1], // Cyan
    confidence: QUALITATIVE_COLORS[1], // Cyan (for bands)
    tracking: QUALITATIVE_COLORS[2], // Amber
  };

  const traces = useMemo(() => {
    const actualData = data.filter((d) => d.actual !== undefined);
    const forecastData = data.filter((d) => d.forecast !== undefined);
    const trackingData = data.filter((d) => d.tracking !== undefined);
    const hasConfidenceInterval = forecastData.some(
      (d) => d.lower !== undefined && d.upper !== undefined
    );

    const traces: Plotly.Data[] = [];

    // Confidence interval bands
    if (hasConfidenceInterval && showConfidenceBands) {
      // Upper bound (invisible line for fill reference)
      traces.push({
        type: 'scatter',
        name: 'Upper Bound',
        x: forecastData.map((d) => d.date),
        y: forecastData.map((d) => d.upper),
        mode: 'lines',
        line: {
          width: 0,
          shape: 'spline',
          smoothing: 1.2,
        },
        showlegend: false,
        hoverinfo: 'skip',
      });

      // Lower bound with fill to upper
      traces.push({
        type: 'scatter',
        name: '95% Confidence',
        x: forecastData.map((d) => d.date),
        y: forecastData.map((d) => d.lower),
        mode: 'lines',
        fill: 'tonexty',
        fillcolor: colorWithOpacity(colors.confidence, bandOpacity),
        line: {
          width: 0,
          shape: 'spline',
          smoothing: 1.2,
        },
        hovertemplate:
          `<b style="font-family: 'DM Sans';">95% Confidence Interval</b><br>` +
          `<span style="font-family: 'JetBrains Mono'; color: ${colors.confidence};">` +
          `${currency}%{customdata[0]:,.2f} - ${currency}%{customdata[1]:,.2f}</span>` +
          `<extra></extra>`,
        customdata: forecastData.map((d) => [d.lower, d.upper]),
      });
    }

    // Historical/Actual line with gradient fill
    if (actualData.length > 0) {
      traces.push({
        type: 'scatter',
        name: 'Actual',
        x: actualData.map((d) => d.date),
        y: actualData.map((d) => d.actual),
        mode: 'lines+markers',
        fill: 'tozeroy',
        fillcolor: colorWithOpacity(colors.actual, 0.08),
        line: {
          color: colors.actual,
          width: 3,
          shape: 'spline',
          smoothing: 1.3,
        },
        marker: {
          color: colors.actual,
          size: 8,
          symbol: 'circle',
          line: {
            color: isDark ? 'rgba(12, 10, 9, 0.8)' : 'rgba(255, 255, 255, 0.9)',
            width: 2,
          },
        },
        hovertemplate:
          `<b style="font-family: 'DM Sans';">Actual</b><br>` +
          `<span style="font-size: 12px; color: #a8a29e;">%{x}</span><br>` +
          `<span style="font-family: 'JetBrains Mono'; font-size: 15px; color: ${colors.actual}; font-weight: 500;">` +
          `${currency}%{y:,.2f}</span>` +
          `<extra></extra>`,
      });
    }

    // Forecast line
    if (forecastData.length > 0) {
      // Connect to last actual point for visual continuity
      const lastActual = actualData[actualData.length - 1];
      const xValues = lastActual
        ? [lastActual.date, ...forecastData.map((d) => d.date)]
        : forecastData.map((d) => d.date);
      const yValues = lastActual
        ? [lastActual.actual, ...forecastData.map((d) => d.forecast)]
        : forecastData.map((d) => d.forecast);

      traces.push({
        type: 'scatter',
        name: 'Forecast',
        x: xValues,
        y: yValues,
        mode: 'lines+markers',
        line: {
          color: colors.forecast,
          width: 3,
          dash: 'dash',
          shape: 'spline',
          smoothing: 1.2,
        },
        marker: {
          color: colors.forecast,
          size: 7,
          symbol: 'circle',
          line: {
            color: isDark ? 'rgba(12, 10, 9, 0.8)' : 'rgba(255, 255, 255, 0.9)',
            width: 2,
          },
        },
        hovertemplate:
          `<b style="font-family: 'DM Sans';">Forecast</b><br>` +
          `<span style="font-size: 12px; color: #a8a29e;">%{x}</span><br>` +
          `<span style="font-family: 'JetBrains Mono'; font-size: 15px; color: ${colors.forecast}; font-weight: 500;">` +
          `${currency}%{y:,.2f}</span>` +
          `<extra></extra>`,
      });
    }

    // Current month tracking point (pulsing effect via larger marker)
    if (trackingData.length > 0) {
      // Outer glow ring
      traces.push({
        type: 'scatter',
        name: '_glow',
        x: trackingData.map((d) => d.date),
        y: trackingData.map((d) => d.tracking),
        mode: 'markers',
        marker: {
          color: colorWithOpacity(colors.tracking, 0.2),
          size: 24,
          symbol: 'circle',
        },
        showlegend: false,
        hoverinfo: 'skip',
      });

      // Main tracking point
      traces.push({
        type: 'scatter',
        name: 'Current Month',
        x: trackingData.map((d) => d.date),
        y: trackingData.map((d) => d.tracking),
        mode: 'markers',
        marker: {
          color: colors.tracking,
          size: 14,
          symbol: 'circle',
          line: {
            color: isDark ? 'rgba(12, 10, 9, 0.9)' : 'rgba(255, 255, 255, 0.95)',
            width: 3,
          },
        },
        hovertemplate:
          `<b style="font-family: 'DM Sans';">Current Month (Partial)</b><br>` +
          `<span style="font-size: 12px; color: #a8a29e;">%{x}</span><br>` +
          `<span style="font-family: 'JetBrains Mono'; font-size: 15px; color: ${colors.tracking}; font-weight: 500;">` +
          `${currency}%{y:,.2f}</span>` +
          `<extra></extra>`,
      });
    }

    return traces;
  }, [data, currency, colors, isDark, showConfidenceBands, bandOpacity]);

  // Get all dates in order for the category array
  const allDates = useMemo(() => {
    return data.map((d) => d.date);
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
        tickfont: {
          family: CHART_TYPOGRAPHY.axisLabel.family,
          size: CHART_TYPOGRAPHY.axisLabel.size,
          color: theme.secondary_text,
        },
      },
      yaxis: {
        ...base.yaxis,
        title: {
          text: `Dividend Amount (${currency})`,
          font: {
            family: CHART_TYPOGRAPHY.axisTitle.family,
            color: theme.muted_text,
            size: CHART_TYPOGRAPHY.axisTitle.size,
          },
          standoff: 8,
        },
        tickprefix: currency,
        tickfont: {
          family: CHART_TYPOGRAPHY.axisLabel.family,
          size: CHART_TYPOGRAPHY.axisLabel.size,
          color: theme.secondary_text,
        },
      },
      legend: {
        ...base.legend,
        orientation: 'h' as const,
        yanchor: 'bottom',
        y: 1.02,
        xanchor: 'left',
        x: 0,
        font: {
          family: CHART_TYPOGRAPHY.legend.family,
          size: CHART_TYPOGRAPHY.legend.size,
          color: theme.secondary_text,
        },
      },
      hovermode: 'x unified' as const,
    };
  }, [theme, title, height, currency, allDates]);

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: [
      'lasso2d',
      'select2d',
      'autoScale2d',
    ] as Plotly.ModeBarDefaultButtons[],
    responsive: true,
  };

  return (
    <div className={cn('w-full', className)} style={{ height }}>
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

// =============================================================================
// PREMIUM PROJECTION BAR CHART
// =============================================================================

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
    return [
      {
        type: 'bar' as const,
        x: data.map((d) => d.year),
        y: data.map((d) => d.projected),
        marker: {
          color: QUALITATIVE_COLORS[0],
          line: {
            color: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
            width: 1,
          },
          opacity: 0.9,
        },
        text: data.map(
          (d) =>
            `${currency}${d.projected.toLocaleString(undefined, {
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            })}`
        ),
        textposition: 'outside' as const,
        textfont: {
          family: CHART_TYPOGRAPHY.dataLabel.family,
          color: theme.text_color,
          size: 11,
        },
        hovertemplate:
          `<b style="font-family: 'DM Sans';">%{x}</b><br>` +
          `<span style="font-family: 'JetBrains Mono'; font-size: 14px; color: ${QUALITATIVE_COLORS[0]}; font-weight: 500;">` +
          `Projected: ${currency}%{y:,.2f}</span>` +
          `<extra></extra>`,
      },
    ];
  }, [data, currency, theme, isDark]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      bargap: 0.35,
      xaxis: {
        ...base.xaxis,
        title: undefined,
        tickfont: {
          family: CHART_TYPOGRAPHY.axisLabel.family,
          size: CHART_TYPOGRAPHY.axisLabel.size,
          color: theme.secondary_text,
        },
      },
      yaxis: {
        ...base.yaxis,
        title: {
          text: `Projected (${currency})`,
          font: {
            family: CHART_TYPOGRAPHY.axisTitle.family,
            color: theme.muted_text,
            size: CHART_TYPOGRAPHY.axisTitle.size,
          },
          standoff: 8,
        },
        tickprefix: currency,
        tickfont: {
          family: CHART_TYPOGRAPHY.axisLabel.family,
          size: CHART_TYPOGRAPHY.axisLabel.size,
          color: theme.secondary_text,
        },
      },
      showlegend: false,
    };
  }, [theme, title, height, currency]);

  const config = {
    displayModeBar: false,
    responsive: true,
  };

  return (
    <div className={cn('w-full', className)} style={{ height }}>
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

export default PlotlyForecastChart;
