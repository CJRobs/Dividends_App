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

export interface LineChartData {
  x: (string | number | Date)[];
  y: number[];
  name?: string;
  color?: string;
  dash?: 'solid' | 'dash' | 'dot' | 'dashdot';
  width?: number;
  showMarkers?: boolean;
  /** Show gradient fill below the line */
  showFill?: boolean;
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
  xAxisFormat?: string;
  yAxisFormat?: string;
  /** Show gradient fill under line(s) */
  showAreaFill?: boolean;
  /** Value prefix for tooltips (e.g., '£') */
  valuePrefix?: string;
  /** Value suffix for tooltips */
  valueSuffix?: string;
  className?: string;
}

// =============================================================================
// PREMIUM LINE CHART
// =============================================================================

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
  showAreaFill = false,
  valuePrefix = '',
  valueSuffix = '',
  className,
}: PlotlyLineChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const traces = useMemo(() => {
    const dataArray = Array.isArray(data) ? data : [data];

    return dataArray.map((d, idx) => {
      const seriesColor = d.color || QUALITATIVE_COLORS[idx % QUALITATIVE_COLORS.length];
      const shouldFill = d.showFill ?? showAreaFill;
      const shouldShowMarkers = d.showMarkers !== false && showMarkers;

      return {
        type: 'scatter' as const,
        mode: shouldShowMarkers ? ('lines+markers' as const) : ('lines' as const),
        x: d.x,
        y: d.y,
        name: d.name || `Series ${idx + 1}`,

        // Premium line styling
        line: {
          color: seriesColor,
          width: d.width || 3,
          dash: d.dash || 'solid',
          shape: curveType,
          smoothing: curveType === 'spline' ? 1.3 : undefined,
        },

        // Enhanced marker styling
        marker: {
          size: 7,
          color: seriesColor,
          line: {
            color: isDark ? 'rgba(12, 10, 9, 0.8)' : 'rgba(255, 255, 255, 0.9)',
            width: 2,
          },
          symbol: 'circle',
        },

        // Gradient fill under the line
        ...(shouldFill && {
          fill: 'tozeroy' as const,
          fillcolor: colorWithOpacity(seriesColor, 0.15),
          fillgradient: {
            type: 'vertical' as const,
            colorscale: [
              [0, colorWithOpacity(seriesColor, 0.25)],
              [1, colorWithOpacity(seriesColor, 0.02)],
            ] as [number, string][],
          },
        }),

        // Premium hover template
        hovertemplate:
          `<b style="font-family: 'DM Sans'; font-size: 13px;">%{x}</b><br>` +
          `<span style="font-family: 'JetBrains Mono'; font-size: 14px; font-weight: 500; color: ${seriesColor};">` +
          `${valuePrefix}%{y:,.2f}${valueSuffix}</span>` +
          `<extra>${d.name || ''}</extra>`,
      };
    });
  }, [data, showMarkers, curveType, showAreaFill, valuePrefix, valueSuffix, isDark]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    const dataArray = Array.isArray(data) ? data : [data];

    return {
      ...base,
      height,
      showlegend: showLegend && dataArray.length > 1,
      hovermode: hoverMode,

      // Enhanced X-axis
      xaxis: {
        ...base.xaxis,
        title: xAxisTitle
          ? {
              text: xAxisTitle,
              font: {
                family: CHART_TYPOGRAPHY.axisTitle.family,
                color: theme.muted_text,
                size: CHART_TYPOGRAPHY.axisTitle.size,
              },
              standoff: 12,
            }
          : undefined,
        tickformat: xAxisFormat,
        tickangle: -45,
        showspikes: true,
        spikecolor: colorWithOpacity(theme.positive_color, 0.3),
        spikethickness: 1,
        spikedash: 'dot',
        spikemode: 'across',
      },

      // Enhanced Y-axis
      yaxis: {
        ...base.yaxis,
        title: yAxisTitle
          ? {
              text: yAxisTitle,
              font: {
                family: CHART_TYPOGRAPHY.axisTitle.family,
                color: theme.muted_text,
                size: CHART_TYPOGRAPHY.axisTitle.size,
              },
              standoff: 8,
            }
          : undefined,
        tickformat: yAxisFormat,
        tickprefix: valuePrefix || undefined,
        ticksuffix: valueSuffix || undefined,
      },

      // Unified hover styling
      hoverlabel: {
        bgcolor: theme.background_color,
        bordercolor: theme.border_color,
        font: {
          family: CHART_TYPOGRAPHY.tooltip.family,
          color: theme.font_color,
          size: CHART_TYPOGRAPHY.tooltip.size,
        },
        align: 'left' as const,
        namelength: -1,
      },
    };
  }, [
    theme,
    title,
    height,
    showLegend,
    data,
    xAxisTitle,
    yAxisTitle,
    hoverMode,
    xAxisFormat,
    yAxisFormat,
    valuePrefix,
    valueSuffix,
  ]);

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
// PREMIUM AREA CHART (Pre-configured line chart with fill)
// =============================================================================

interface PlotlyAreaChartProps extends Omit<PlotlyLineChartProps, 'showAreaFill'> {
  /** Gradient intensity (0-1) */
  gradientIntensity?: number;
}

export function PlotlyAreaChart({
  gradientIntensity = 0.2,
  showMarkers = false,
  ...props
}: PlotlyAreaChartProps) {
  return (
    <PlotlyLineChart {...props} showAreaFill showMarkers={showMarkers} />
  );
}

// =============================================================================
// SCATTER WITH MOVING AVERAGE
// =============================================================================

interface ScatterWithMAProps {
  x: (string | Date)[];
  y: number[];
  title?: string;
  xAxisTitle?: string;
  yAxisTitle?: string;
  height?: number;
  maWindow?: number;
  valuePrefix?: string;
  valueSuffix?: string;
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
  valuePrefix = '',
  valueSuffix = '',
  className,
}: ScatterWithMAProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

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
    // Scatter points
    {
      type: 'scatter' as const,
      mode: 'markers' as const,
      x,
      y,
      name: 'Individual Payments',
      marker: {
        size: 10,
        color: QUALITATIVE_COLORS[0],
        line: {
          color: isDark ? 'rgba(12, 10, 9, 0.8)' : 'rgba(255, 255, 255, 0.9)',
          width: 2,
        },
        opacity: 0.9,
      },
      hovertemplate:
        `<b>%{x}</b><br>` +
        `<span style="font-family: 'JetBrains Mono'; color: ${QUALITATIVE_COLORS[0]};">` +
        `${valuePrefix}%{y:,.2f}${valueSuffix}</span>` +
        `<extra></extra>`,
    },
    // Moving average line
    ...(ma.length > 0
      ? [
          {
            type: 'scatter' as const,
            mode: 'lines' as const,
            x,
            y: ma,
            name: `${maWindow}-Point MA`,
            line: {
              color: QUALITATIVE_COLORS[2], // Amber
              width: 3,
              shape: 'spline' as const,
              smoothing: 1.2,
            },
            hovertemplate:
              `<b>%{x}</b><br>` +
              `<span style="font-family: 'JetBrains Mono'; color: ${QUALITATIVE_COLORS[2]};">` +
              `MA: ${valuePrefix}%{y:,.2f}${valueSuffix}</span>` +
              `<extra></extra>`,
          },
        ]
      : []),
  ];

  const layout = {
    ...getBaseLayout(theme, title),
    height,
    hovermode: 'closest' as const,
    xaxis: {
      title: xAxisTitle
        ? {
            text: xAxisTitle,
            font: {
              family: CHART_TYPOGRAPHY.axisTitle.family,
              color: theme.muted_text,
              size: CHART_TYPOGRAPHY.axisTitle.size,
            },
          }
        : undefined,
      gridcolor: theme.grid_color,
      tickangle: -45,
      tickfont: {
        family: CHART_TYPOGRAPHY.axisLabel.family,
        color: theme.secondary_text,
        size: CHART_TYPOGRAPHY.axisLabel.size,
      },
    },
    yaxis: {
      title: yAxisTitle
        ? {
            text: yAxisTitle,
            font: {
              family: CHART_TYPOGRAPHY.axisTitle.family,
              color: theme.muted_text,
              size: CHART_TYPOGRAPHY.axisTitle.size,
            },
          }
        : undefined,
      gridcolor: theme.grid_color,
      tickfont: {
        family: CHART_TYPOGRAPHY.axisLabel.family,
        color: theme.secondary_text,
        size: CHART_TYPOGRAPHY.axisLabel.size,
      },
      tickprefix: valuePrefix || undefined,
      ticksuffix: valueSuffix || undefined,
    },
  };

  const config = {
    displayModeBar: true,
    displaylogo: false,
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

export default PlotlyLineChart;
