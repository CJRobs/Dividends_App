'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import {
  getChartTheme,
  getBaseLayout,
  QUALITATIVE_COLORS,
  CHART_TYPOGRAPHY,
  getGrowthColors,
  colorWithOpacity,
} from '@/lib/chartTheme';
import { useIsDark } from '@/hooks/useTheme';
import { cn } from '@/lib/utils';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

// =============================================================================
// TYPES
// =============================================================================

export interface BarChartData {
  x: (string | number)[];
  y: number[];
  name?: string;
}

interface SimpleBarChartProps {
  labels: (string | number)[];
  values: number[];
  title?: string;
  xAxisTitle?: string;
  yAxisTitle?: string;
  height?: number;
  orientation?: 'vertical' | 'horizontal';
  /** Single color for all bars */
  color?: string;
  /** Use green/red based on positive/negative values */
  conditionalColors?: boolean;
  /** Show value labels on bars */
  showValues?: boolean;
  textPosition?: 'inside' | 'outside' | 'auto' | 'none';
  valueFormat?: string;
  valuePrefix?: string;
  valueSuffix?: string;
  /** Rounded bar corners (visual enhancement) */
  rounded?: boolean;
  className?: string;
}

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
  valuePrefix?: string;
  valueSuffix?: string;
  className?: string;
}

// =============================================================================
// PREMIUM SIMPLE BAR CHART
// =============================================================================

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
  rounded = true,
  className,
}: SimpleBarChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);
  const isVertical = orientation === 'vertical';

  // Determine bar colors
  const barColors = useMemo(() => {
    if (conditionalColors) {
      return getGrowthColors(values, isDark);
    }
    return color || QUALITATIVE_COLORS[0];
  }, [conditionalColors, values, color, isDark]);

  const trace = useMemo(
    () => ({
      type: 'bar' as const,
      x: isVertical ? labels : values,
      y: isVertical ? values : labels,
      orientation: isVertical ? ('v' as const) : ('h' as const),

      // Premium marker styling
      marker: {
        color: barColors,
        line: {
          color: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
          width: 1,
        },
        opacity: 0.9,
      },

      // Value labels
      text:
        showValues && textPosition !== 'none'
          ? values.map((v) => {
              const formatted = v.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              });
              return `${valuePrefix}${formatted}${valueSuffix}`;
            })
          : undefined,
      textposition: showValues && textPosition !== 'none' ? textPosition : undefined,
      textfont: {
        family: CHART_TYPOGRAPHY.dataLabel.family,
        color: textPosition === 'inside' ? '#ffffff' : theme.text_color,
        size: CHART_TYPOGRAPHY.dataLabel.size,
      },
      textangle: 0,
      constraintext: 'both',
      cliponaxis: false,

      // Premium hover template
      hovertemplate:
        `<b style="font-family: 'DM Sans';">%{${isVertical ? 'x' : 'y'}}</b><br>` +
        `<span style="font-family: 'JetBrains Mono'; font-size: 14px; font-weight: 500;">` +
        `${valuePrefix}%{${isVertical ? 'y' : 'x'}:${valueFormat}}${valueSuffix}</span>` +
        `<extra></extra>`,
    }),
    [
      labels,
      values,
      isVertical,
      barColors,
      showValues,
      textPosition,
      valueFormat,
      valuePrefix,
      valueSuffix,
      theme,
      isDark,
    ]
  );

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      showlegend: false,
      bargap: 0.3,
      bargroupgap: 0.1,

      xaxis: {
        ...base.xaxis,
        title: {
          text: isVertical ? xAxisTitle : yAxisTitle,
          font: {
            family: CHART_TYPOGRAPHY.axisTitle.family,
            color: theme.muted_text,
            size: CHART_TYPOGRAPHY.axisTitle.size,
          },
          standoff: 12,
        },
        tickangle: isVertical ? -45 : 0,
        categoryorder: !isVertical ? ('total ascending' as const) : undefined,
      },

      yaxis: {
        ...base.yaxis,
        title: {
          text: isVertical ? yAxisTitle : xAxisTitle,
          font: {
            family: CHART_TYPOGRAPHY.axisTitle.family,
            color: theme.muted_text,
            size: CHART_TYPOGRAPHY.axisTitle.size,
          },
          standoff: 8,
        },
        tickprefix: isVertical && valuePrefix ? valuePrefix : undefined,
        ticksuffix: isVertical && valueSuffix ? valueSuffix : undefined,
      },
    };
  }, [theme, title, height, isVertical, xAxisTitle, yAxisTitle, valuePrefix, valueSuffix]);

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'] as Plotly.ModeBarDefaultButtons[],
    responsive: true,
  };

  return (
    <div className={cn('w-full', className)} style={{ height }}>
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

// =============================================================================
// PREMIUM MULTI-SERIES BAR CHART
// =============================================================================

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
  valuePrefix = '',
  valueSuffix = '',
  className,
}: ComplexBarChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const traces = useMemo(() => {
    const dataArray = Array.isArray(data) ? data : [data];

    return dataArray.map((d, idx) => {
      const seriesColor = QUALITATIVE_COLORS[idx % QUALITATIVE_COLORS.length];
      const barColors = colorByValue ? getGrowthColors(d.y, isDark) : seriesColor;

      return {
        type: 'bar' as const,
        x: orientation === 'v' ? d.x : d.y,
        y: orientation === 'v' ? d.y : d.x,
        name: d.name || `Series ${idx + 1}`,
        orientation,

        // Premium marker styling
        marker: {
          color: barColors,
          line: {
            color: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
            width: 1,
          },
          opacity: 0.9,
        },

        // Value labels
        text:
          textPosition !== 'none'
            ? d.y.map((v) => v.toLocaleString(undefined, { maximumFractionDigits: 2 }))
            : undefined,
        texttemplate: textTemplate,
        textposition: textPosition !== 'none' ? textPosition : undefined,
        textfont: {
          family: CHART_TYPOGRAPHY.dataLabel.family,
          color: textPosition === 'inside' ? '#ffffff' : theme.text_color,
          size: 10,
        },

        // Premium hover template
        hovertemplate:
          hoverTemplate ||
          `<b style="font-family: 'DM Sans';">%{${orientation === 'v' ? 'x' : 'y'}}</b><br>` +
            `<span style="font-family: 'JetBrains Mono'; font-size: 14px; color: ${seriesColor};">` +
            `${valuePrefix}%{${orientation === 'v' ? 'y' : 'x'}:,.2f}${valueSuffix}</span>` +
            `<extra>${d.name || ''}</extra>`,
      };
    });
  }, [data, orientation, colorByValue, textTemplate, textPosition, hoverTemplate, valuePrefix, valueSuffix, theme, isDark]);

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    const dataArray = Array.isArray(data) ? data : [data];

    return {
      ...base,
      height,
      barmode,
      bargap: 0.25,
      bargroupgap: 0.1,
      showlegend: showLegend && dataArray.length > 1,

      legend: {
        ...base.legend,
        orientation: 'h' as const,
        yanchor: 'bottom',
        y: 1.02,
        xanchor: 'left',
        x: 0,
      },

      xaxis: {
        ...base.xaxis,
        title: {
          text: orientation === 'v' ? xAxisTitle : yAxisTitle,
          font: {
            family: CHART_TYPOGRAPHY.axisTitle.family,
            color: theme.muted_text,
            size: CHART_TYPOGRAPHY.axisTitle.size,
          },
          standoff: 12,
        },
        tickangle: orientation === 'v' ? -45 : 0,
        categoryorder: orientation === 'h' ? ('total ascending' as const) : undefined,
      },

      yaxis: {
        ...base.yaxis,
        title: {
          text: orientation === 'v' ? yAxisTitle : xAxisTitle,
          font: {
            family: CHART_TYPOGRAPHY.axisTitle.family,
            color: theme.muted_text,
            size: CHART_TYPOGRAPHY.axisTitle.size,
          },
          standoff: 8,
        },
        tickprefix: orientation === 'v' && valuePrefix ? valuePrefix : undefined,
        ticksuffix: orientation === 'v' && valueSuffix ? valueSuffix : undefined,
      },
    };
  }, [theme, title, height, barmode, showLegend, data, xAxisTitle, yAxisTitle, orientation, valuePrefix, valueSuffix]);

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'] as Plotly.ModeBarDefaultButtons[],
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
// GROWTH BAR CHART (Preset for positive/negative values)
// =============================================================================

interface GrowthBarChartProps {
  labels: (string | number)[];
  values: number[];
  title?: string;
  xAxisTitle?: string;
  yAxisTitle?: string;
  height?: number;
  orientation?: 'vertical' | 'horizontal';
  showValues?: boolean;
  valuePrefix?: string;
  valueSuffix?: string;
  className?: string;
}

export function PlotlyGrowthBarChart({
  labels,
  values,
  title,
  xAxisTitle,
  yAxisTitle,
  height = 400,
  orientation = 'vertical',
  showValues = true,
  valuePrefix = '',
  valueSuffix = '',
  className,
}: GrowthBarChartProps) {
  return (
    <PlotlyBarChart
      labels={labels}
      values={values}
      title={title}
      xAxisTitle={xAxisTitle}
      yAxisTitle={yAxisTitle}
      height={height}
      orientation={orientation}
      conditionalColors
      showValues={showValues}
      textPosition="outside"
      valuePrefix={valuePrefix}
      valueSuffix={valueSuffix}
      className={className}
    />
  );
}

export default PlotlyBarChart;
