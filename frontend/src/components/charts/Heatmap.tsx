'use client';

import { useMemo } from 'react';

interface HeatmapProps {
  data: {
    row: string;
    col: string;
    value: number;
  }[];
  rows: string[];
  cols: string[];
  formatValue?: (value: number) => string;
  colorScale?: 'blue' | 'green' | 'purple' | 'orange';
  showValues?: boolean;
}

// Color scales
const COLOR_SCALES = {
  blue: {
    min: '#1e3a5f',
    mid: '#3b82f6',
    max: '#93c5fd',
  },
  green: {
    min: '#14532d',
    mid: '#10b981',
    max: '#86efac',
  },
  purple: {
    min: '#3b0764',
    mid: '#8b5cf6',
    max: '#c4b5fd',
  },
  orange: {
    min: '#7c2d12',
    mid: '#f59e0b',
    max: '#fcd34d',
  },
};

function interpolateColor(value: number, min: number, max: number, scale: typeof COLOR_SCALES.blue): string {
  if (max === min) return scale.mid;

  const normalized = (value - min) / (max - min);

  // Parse hex colors
  const parseHex = (hex: string) => ({
    r: parseInt(hex.slice(1, 3), 16),
    g: parseInt(hex.slice(3, 5), 16),
    b: parseInt(hex.slice(5, 7), 16),
  });

  const minColor = parseHex(scale.min);
  const midColor = parseHex(scale.mid);
  const maxColor = parseHex(scale.max);

  let r, g, b;

  if (normalized < 0.5) {
    const t = normalized * 2;
    r = Math.round(minColor.r + (midColor.r - minColor.r) * t);
    g = Math.round(minColor.g + (midColor.g - minColor.g) * t);
    b = Math.round(minColor.b + (midColor.b - minColor.b) * t);
  } else {
    const t = (normalized - 0.5) * 2;
    r = Math.round(midColor.r + (maxColor.r - midColor.r) * t);
    g = Math.round(midColor.g + (maxColor.g - midColor.g) * t);
    b = Math.round(midColor.b + (maxColor.b - midColor.b) * t);
  }

  return `rgb(${r}, ${g}, ${b})`;
}

export function Heatmap({
  data,
  rows,
  cols,
  formatValue = (v) => v.toLocaleString(),
  colorScale = 'blue',
  showValues = true,
}: HeatmapProps) {
  // Create lookup map for quick access
  const valueMap = useMemo(() => {
    const map = new Map<string, number>();
    data.forEach((item) => {
      map.set(`${item.row}-${item.col}`, item.value);
    });
    return map;
  }, [data]);

  // Calculate min/max for color scaling
  const { minValue, maxValue } = useMemo(() => {
    const values = data.map((d) => d.value).filter((v) => v > 0);
    return {
      minValue: values.length > 0 ? Math.min(...values) : 0,
      maxValue: values.length > 0 ? Math.max(...values) : 1,
    };
  }, [data]);

  const scale = COLOR_SCALES[colorScale];
  const cellWidth = `${100 / (cols.length + 1)}%`;

  return (
    <div className="w-full h-full overflow-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr>
            <th
              className="p-2 text-left text-muted-foreground font-medium sticky left-0 bg-background z-10"
              style={{ width: cellWidth }}
            >
              {/* Empty corner cell */}
            </th>
            {cols.map((col) => (
              <th
                key={col}
                className="p-2 text-center text-muted-foreground font-medium"
                style={{ width: cellWidth }}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row}>
              <td className="p-2 text-left text-muted-foreground font-medium sticky left-0 bg-background">
                {row}
              </td>
              {cols.map((col) => {
                const value = valueMap.get(`${row}-${col}`) || 0;
                const bgColor = value > 0
                  ? interpolateColor(value, minValue, maxValue, scale)
                  : '#1f2937';

                return (
                  <td
                    key={`${row}-${col}`}
                    className="p-2 text-center transition-colors cursor-pointer hover:opacity-80"
                    style={{
                      backgroundColor: bgColor,
                      color: value > 0 ? '#ffffff' : '#6b7280',
                    }}
                    title={`${row} - ${col}: ${formatValue(value)}`}
                  >
                    {showValues && (value > 0 ? formatValue(value) : '-')}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Color legend */}
      <div className="flex items-center justify-center gap-2 mt-4 text-xs text-muted-foreground">
        <span>Low</span>
        <div
          className="w-24 h-3 rounded"
          style={{
            background: `linear-gradient(to right, ${scale.min}, ${scale.mid}, ${scale.max})`,
          }}
        />
        <span>High</span>
      </div>
    </div>
  );
}
