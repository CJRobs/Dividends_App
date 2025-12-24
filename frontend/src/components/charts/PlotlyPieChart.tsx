'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import {
  getChartTheme,
  getBaseLayout,
  QUALITATIVE_COLORS,
  CHART_TYPOGRAPHY,
} from '@/lib/chartTheme';
import { useIsDark } from '@/hooks/useTheme';
import { cn } from '@/lib/utils';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

// =============================================================================
// TYPES
// =============================================================================

interface PlotlyPieChartProps {
  labels: string[];
  values: number[];
  title?: string;
  height?: number;
  /** 0 for pie, 0.4+ for donut */
  hole?: number;
  showLegend?: boolean;
  textInfo?: 'percent' | 'label' | 'value' | 'percent+label' | 'label+value' | 'none';
  /** Custom color palette */
  colors?: string[];
  /** Value prefix for tooltips */
  valuePrefix?: string;
  /** Value suffix for tooltips */
  valueSuffix?: string;
  /** Pull distance for slices on hover (0-0.2) */
  pull?: number;
  className?: string;
}

// =============================================================================
// PREMIUM PIE CHART
// =============================================================================

export function PlotlyPieChart({
  labels,
  values,
  title,
  height = 400,
  hole = 0,
  showLegend = true,
  textInfo = 'percent+label',
  colors,
  valuePrefix = '',
  valueSuffix = '',
  pull = 0.02,
  className,
}: PlotlyPieChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const trace = useMemo(
    () => ({
      type: 'pie' as const,
      labels,
      values,
      hole,
      pull,

      // Premium marker styling
      marker: {
        colors: colors || QUALITATIVE_COLORS,
        line: {
          color: isDark ? 'rgba(12, 10, 9, 0.8)' : 'rgba(255, 255, 255, 0.95)',
          width: 2,
        },
      },

      // Text styling
      textinfo: textInfo,
      textposition: 'inside' as const,
      textfont: {
        family: CHART_TYPOGRAPHY.dataLabel.family,
        color: '#ffffff',
        size: 11,
      },
      insidetextorientation: 'radial' as const,

      // Premium hover template
      hovertemplate:
        `<b style="font-family: 'DM Sans'; font-size: 14px;">%{label}</b><br>` +
        `<span style="font-family: 'JetBrains Mono'; font-size: 15px; font-weight: 500;">` +
        `${valuePrefix}%{value:,.2f}${valueSuffix}</span><br>` +
        `<span style="font-size: 12px; color: #a8a29e;">%{percent}</span>` +
        `<extra></extra>`,

      // Interaction
      hoverlabel: {
        bgcolor: theme.background_color,
        bordercolor: theme.border_color,
        font: {
          family: CHART_TYPOGRAPHY.tooltip.family,
          size: CHART_TYPOGRAPHY.tooltip.size,
          color: theme.font_color,
        },
      },

      // Smooth rotation
      rotation: -90,
      direction: 'clockwise' as const,
      sort: false,
    }),
    [labels, values, hole, pull, textInfo, colors, valuePrefix, valueSuffix, theme, isDark]
  );

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
        font: {
          family: CHART_TYPOGRAPHY.legend.family,
          size: CHART_TYPOGRAPHY.legend.size,
          color: theme.secondary_text,
        },
        itemsizing: 'constant',
        itemwidth: 30,
      },
      margin: { l: 20, r: showLegend ? 140 : 20, t: title ? 60 : 20, b: 20 },
    };
  }, [theme, title, height, showLegend]);

  const config = {
    displayModeBar: false,
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
// PREMIUM DONUT CHART (with center text)
// =============================================================================

interface PlotlyDonutChartProps extends Omit<PlotlyPieChartProps, 'hole'> {
  /** Text displayed in the center (label) */
  centerText?: string;
  /** Value displayed in the center (large number) */
  centerValue?: string;
  /** Donut hole size (0.35-0.7) */
  holeSize?: number;
}

export function PlotlyDonutChart({
  labels,
  values,
  title,
  height = 400,
  showLegend = true,
  textInfo = 'percent',
  colors,
  valuePrefix = '',
  valueSuffix = '',
  pull = 0.02,
  centerText,
  centerValue,
  holeSize = 0.45,
  className,
}: PlotlyDonutChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  const trace = useMemo(
    () => ({
      type: 'pie' as const,
      labels,
      values,
      hole: holeSize,
      pull,

      // Premium marker styling
      marker: {
        colors: colors || QUALITATIVE_COLORS,
        line: {
          color: isDark ? 'rgba(12, 10, 9, 0.8)' : 'rgba(255, 255, 255, 0.95)',
          width: 2,
        },
      },

      // Text styling
      textinfo: textInfo,
      textposition: 'inside' as const,
      textfont: {
        family: CHART_TYPOGRAPHY.dataLabel.family,
        color: '#ffffff',
        size: 10,
      },
      insidetextorientation: 'radial' as const,

      // Premium hover template
      hovertemplate:
        `<b style="font-family: 'DM Sans'; font-size: 14px;">%{label}</b><br>` +
        `<span style="font-family: 'JetBrains Mono'; font-size: 15px; font-weight: 500;">` +
        `${valuePrefix}%{value:,.2f}${valueSuffix}</span><br>` +
        `<span style="font-size: 12px; color: #a8a29e;">%{percent}</span>` +
        `<extra></extra>`,

      hoverlabel: {
        bgcolor: theme.background_color,
        bordercolor: theme.border_color,
        font: {
          family: CHART_TYPOGRAPHY.tooltip.family,
          size: CHART_TYPOGRAPHY.tooltip.size,
          color: theme.font_color,
        },
      },

      rotation: -90,
      direction: 'clockwise' as const,
      sort: false,
    }),
    [labels, values, holeSize, pull, textInfo, colors, valuePrefix, valueSuffix, theme, isDark]
  );

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);

    // Center annotations
    const annotations =
      centerText || centerValue
        ? [
            // Center value (large number)
            ...(centerValue
              ? [
                  {
                    text: centerValue,
                    font: {
                      family: CHART_TYPOGRAPHY.title.family,
                      size: 24,
                      color: theme.text_color,
                    },
                    showarrow: false,
                    x: 0.5,
                    y: centerText ? 0.55 : 0.5,
                    xanchor: 'center' as const,
                    yanchor: 'middle' as const,
                  },
                ]
              : []),
            // Center text (label)
            ...(centerText
              ? [
                  {
                    text: centerText,
                    font: {
                      family: CHART_TYPOGRAPHY.subtitle.family,
                      size: 12,
                      color: theme.secondary_text,
                    },
                    showarrow: false,
                    x: 0.5,
                    y: centerValue ? 0.42 : 0.5,
                    xanchor: 'center' as const,
                    yanchor: 'middle' as const,
                  },
                ]
              : []),
          ]
        : undefined;

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
        font: {
          family: CHART_TYPOGRAPHY.legend.family,
          size: CHART_TYPOGRAPHY.legend.size,
          color: theme.secondary_text,
        },
        itemsizing: 'constant',
        itemwidth: 30,
      },
      margin: { l: 20, r: showLegend ? 140 : 20, t: title ? 60 : 20, b: 20 },
    };
  }, [theme, title, height, showLegend, centerText, centerValue]);

  const config = {
    displayModeBar: false,
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
// HALF DONUT / GAUGE CHART
// =============================================================================

interface PlotlyGaugeChartProps {
  value: number;
  min?: number;
  max?: number;
  title?: string;
  label?: string;
  height?: number;
  /** Color stops for the gauge */
  colorStops?: { value: number; color: string }[];
  valuePrefix?: string;
  valueSuffix?: string;
  className?: string;
}

export function PlotlyGaugeChart({
  value,
  min = 0,
  max = 100,
  title,
  label,
  height = 300,
  colorStops,
  valuePrefix = '',
  valueSuffix = '',
  className,
}: PlotlyGaugeChartProps) {
  const isDark = useIsDark();
  const theme = getChartTheme(isDark);

  // Default color stops (green to red)
  const defaultColorStops = [
    { value: 0, color: '#22c55e' },
    { value: 50, color: '#f59e0b' },
    { value: 100, color: '#ef4444' },
  ];

  const stops = colorStops || defaultColorStops;

  const trace = useMemo(
    () => ({
      type: 'indicator' as const,
      mode: 'gauge+number' as const,
      value,
      number: {
        prefix: valuePrefix,
        suffix: valueSuffix,
        font: {
          family: CHART_TYPOGRAPHY.title.family,
          size: 32,
          color: theme.text_color,
        },
      },
      gauge: {
        axis: {
          range: [min, max],
          tickwidth: 1,
          tickcolor: theme.border_color,
          tickfont: {
            family: CHART_TYPOGRAPHY.axisLabel.family,
            size: 10,
            color: theme.secondary_text,
          },
        },
        bar: {
          color: QUALITATIVE_COLORS[0],
          thickness: 0.75,
        },
        bgcolor: theme.border_color,
        borderwidth: 0,
        steps: stops.map((stop, idx) => ({
          range: [
            idx === 0 ? min : stops[idx - 1].value,
            stop.value,
          ],
          color: `${stop.color}20`,
        })),
        threshold: {
          line: { color: theme.text_color, width: 2 },
          thickness: 0.75,
          value,
        },
      },
    }),
    [value, min, max, valuePrefix, valueSuffix, stops, theme]
  );

  const layout = useMemo(() => {
    const base = getBaseLayout(theme, title);
    return {
      ...base,
      height,
      margin: { l: 30, r: 30, t: title ? 60 : 30, b: 30 },
      ...(label && {
        annotations: [
          {
            text: label,
            font: {
              family: CHART_TYPOGRAPHY.subtitle.family,
              size: 13,
              color: theme.secondary_text,
            },
            showarrow: false,
            x: 0.5,
            y: 0.25,
            xanchor: 'center' as const,
            yanchor: 'top' as const,
          },
        ],
      }),
    };
  }, [theme, title, height, label]);

  const config = {
    displayModeBar: false,
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

export default PlotlyPieChart;
