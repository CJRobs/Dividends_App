declare module 'react-plotly.js' {
  import { Component } from 'react';

  interface PlotParams {
    data: Plotly.Data[];
    layout?: Partial<Plotly.Layout>;
    config?: Partial<Plotly.Config>;
    frames?: Plotly.Frame[];
    onInitialized?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
    onUpdate?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
    onPurge?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
    onError?: (err: Error) => void;
    style?: React.CSSProperties;
    className?: string;
    useResizeHandler?: boolean;
    debug?: boolean;
    divId?: string;
  }

  export default class Plot extends Component<PlotParams> {}
}

declare namespace Plotly {
  type ModeBarDefaultButtons =
    | 'lasso2d'
    | 'select2d'
    | 'zoom2d'
    | 'pan2d'
    | 'zoomIn2d'
    | 'zoomOut2d'
    | 'autoScale2d'
    | 'resetScale2d'
    | 'hoverClosestCartesian'
    | 'hoverCompareCartesian'
    | 'zoom3d'
    | 'pan3d'
    | 'orbitRotation'
    | 'tableRotation'
    | 'resetCameraDefault3d'
    | 'resetCameraLastSave3d'
    | 'hoverClosest3d'
    | 'zoomInGeo'
    | 'zoomOutGeo'
    | 'resetGeo'
    | 'hoverClosestGeo'
    | 'hoverClosestGl2d'
    | 'hoverClosestPie'
    | 'toggleHover'
    | 'resetViews'
    | 'toggleSpikelines'
    | 'resetViewMapbox';

  interface Data {
    type?: string;
    x?: unknown[];
    y?: unknown[];
    z?: unknown[];
    text?: unknown[];
    name?: string;
    marker?: unknown;
    line?: unknown;
    mode?: string;
    orientation?: 'v' | 'h';
    hovertemplate?: string;
    texttemplate?: string;
    textposition?: string;
    textfont?: unknown;
    insidetextanchor?: string;
    insidetextorientation?: string;
    hole?: number;
    labels?: string[];
    values?: number[];
    [key: string]: unknown;
  }

  interface AxisLayout {
    title?: string | { text?: string; font?: { color?: string; size?: number } };
    tickangle?: number;
    categoryorder?: string;
    gridcolor?: string;
    zerolinecolor?: string;
    tickfont?: { color?: string; size?: number };
    tickformat?: string;
    overlaying?: string;
    side?: string;
    [key: string]: unknown;
  }

  interface Layout {
    title?: string | { text?: string; font?: { size?: number; color?: string }; x?: number; xanchor?: string };
    height?: number;
    width?: number;
    margin?: { l?: number; r?: number; t?: number; b?: number; pad?: number };
    paper_bgcolor?: string;
    plot_bgcolor?: string;
    font?: { color?: string; size?: number; family?: string };
    showlegend?: boolean;
    legend?: {
      font?: { color?: string; size?: number };
      bgcolor?: string;
      orientation?: 'v' | 'h';
      yanchor?: string;
      y?: number;
      xanchor?: string;
      x?: number;
      title?: { text?: string; font?: { color?: string; size?: number } };
      [key: string]: unknown;
    };
    hovermode?: 'closest' | 'x' | 'y' | 'x unified' | 'y unified' | false;
    barmode?: 'group' | 'stack' | 'overlay' | 'relative';
    xaxis?: AxisLayout;
    yaxis?: AxisLayout;
    yaxis2?: AxisLayout;
    annotations?: unknown[];
    shapes?: unknown[];
    [key: string]: unknown;
  }

  interface Config {
    displayModeBar?: boolean;
    displaylogo?: boolean;
    modeBarButtonsToRemove?: ModeBarDefaultButtons[];
    responsive?: boolean;
    scrollZoom?: boolean;
    [key: string]: unknown;
  }

  interface Frame {
    name?: string;
    data?: Data[];
    layout?: Partial<Layout>;
    [key: string]: unknown;
  }

  interface Figure {
    data: Data[];
    layout: Layout;
    frames?: Frame[];
  }
}
