"""
Chart Theming and Styling Utilities for the Dividend Portfolio Dashboard.

This module provides consistent chart theming across all visualizations
with support for light and dark modes.
"""

import plotly.graph_objects as go
from typing import Dict, Any, List

# Professional Color Palette
COLORS = {
    "primary": "#3b82f6",  # Blue
    "secondary": "#64748b",  # Gray
    "success": "#10b981",  # Green
    "warning": "#f59e0b",  # Orange
    "danger": "#ef4444",  # Red
    "info": "#06b6d4",  # Cyan
    "purple": "#8b5cf6",  # Purple
    "pink": "#ec4899",  # Pink
    "indigo": "#6366f1",  # Indigo
    "teal": "#14b8a6",  # Teal
}

QUALITATIVE_COLORS = [
    "#3b82f6",  # Blue
    "#10b981",  # Green
    "#f59e0b",  # Orange
    "#ef4444",  # Red
    "#8b5cf6",  # Purple
    "#06b6d4",  # Cyan
    "#ec4899",  # Pink
    "#6366f1",  # Indigo
    "#14b8a6",  # Teal
    "#64748b",  # Gray
]

SEQUENTIAL_COLORS = [
    "#dbeafe",  # Light blue
    "#bfdbfe",
    "#93c5fd",
    "#60a5fa",
    "#3b82f6",  # Primary blue
    "#2563eb",
    "#1d4ed8",
    "#1e40af",
    "#1e3a8a",
    "#1e3a8a",  # Dark blue
]


def get_chart_theme(theme: str = "Light") -> Dict[str, Any]:
    """
    Get chart theme configuration for Plotly charts.

    Args:
        theme: Theme mode ("Light" or "Dark")

    Returns:
        Dictionary with theme configuration
    """
    is_dark = theme.lower() == "dark"

    if is_dark:
        return {
            "template": "plotly_dark",
            "paper_bgcolor": "#2d2d2d",
            "plot_bgcolor": "#2d2d2d",
            "font_color": "#ffffff",
            "grid_color": "#404040",
            "line_color": "#404040",
            "background_color": "#2d2d2d",
            "text_color": "#ffffff",
            "secondary_text": "#e0e0e0",
            "border_color": "#404040",
        }
    else:
        return {
            "template": "plotly_white",
            "paper_bgcolor": "#ffffff",
            "plot_bgcolor": "#ffffff",
            "font_color": "#0f172a",
            "grid_color": "#e2e8f0",
            "line_color": "#cbd5e1",
            "background_color": "#ffffff",
            "text_color": "#0f172a",
            "secondary_text": "#475569",
            "border_color": "#e2e8f0",
        }


def apply_chart_theme(
    fig: go.Figure, theme: str = "Light", title: str = None
) -> go.Figure:
    """
    Apply consistent theming to a Plotly figure.

    Args:
        fig: Plotly figure object
        theme: Theme mode ("Light" or "Dark")
        title: Optional chart title

    Returns:
        Styled Plotly figure
    """
    theme_config = get_chart_theme(theme)

    # Update layout with theme
    fig.update_layout(
        template=theme_config["template"],
        paper_bgcolor=theme_config["paper_bgcolor"],
        plot_bgcolor=theme_config["plot_bgcolor"],
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            size=12,
            color=theme_config["font_color"],
        ),
        title=dict(
            text=title,
            font=dict(size=18, weight="bold", color=theme_config["text_color"]),
            x=0.5,
            xanchor="center",
            pad=dict(t=20, b=20),
        )
        if title
        else None,
        margin=dict(l=60, r=60, t=80, b=60),
        showlegend=True,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=theme_config["border_color"],
            borderwidth=1,
            font=dict(color=theme_config["font_color"]),
        ),
        xaxis=dict(
            gridcolor=theme_config["grid_color"],
            linecolor=theme_config["line_color"],
            tickfont=dict(color=theme_config["secondary_text"]),
            title=dict(font=dict(color=theme_config["text_color"], size=14)),
        ),
        yaxis=dict(
            gridcolor=theme_config["grid_color"],
            linecolor=theme_config["line_color"],
            tickfont=dict(color=theme_config["secondary_text"]),
            title=dict(font=dict(color=theme_config["text_color"], size=14)),
        ),
        hoverlabel=dict(
            bgcolor=theme_config["background_color"],
            bordercolor=theme_config["border_color"],
            font=dict(color=theme_config["font_color"]),
        ),
    )

    return fig


def create_line_chart(
    data,
    x_col: str,
    y_col: str,
    title: str,
    theme: str = "Light",
    color: str = None,
    **kwargs,
) -> go.Figure:
    """
    Create a styled line chart.

    Args:
        data: DataFrame or data source
        x_col: X-axis column name
        y_col: Y-axis column name
        title: Chart title
        theme: Theme mode
        color: Line color (optional)
        **kwargs: Additional plotly express arguments

    Returns:
        Styled Plotly figure
    """
    import plotly.express as px

    line_color = color or COLORS["primary"]

    fig = px.line(data, x=x_col, y=y_col, **kwargs)

    # Update trace styling
    fig.update_traces(
        line=dict(color=line_color, width=3),
        mode="lines+markers",
        marker=dict(size=6, color=line_color),
        hovertemplate="<b>%{x}</b><br>%{y}<extra></extra>",
    )

    return apply_chart_theme(fig, theme, title)


def create_bar_chart(
    data,
    x_col: str,
    y_col: str,
    title: str,
    theme: str = "Light",
    color_col: str = None,
    **kwargs,
) -> go.Figure:
    """
    Create a styled bar chart.

    Args:
        data: DataFrame or data source
        x_col: X-axis column name
        y_col: Y-axis column name
        title: Chart title
        theme: Theme mode
        color_col: Column for color mapping (optional)
        **kwargs: Additional plotly express arguments

    Returns:
        Styled Plotly figure
    """
    import plotly.express as px

    color_discrete_map = kwargs.pop("color_discrete_map", None)
    if not color_discrete_map and color_col:
        unique_values = data[color_col].unique()
        color_discrete_map = {
            val: QUALITATIVE_COLORS[i % len(QUALITATIVE_COLORS)]
            for i, val in enumerate(unique_values)
        }

    fig = px.bar(
        data,
        x=x_col,
        y=y_col,
        color=color_col,
        color_discrete_map=color_discrete_map,
        **kwargs,
    )

    # Update trace styling
    fig.update_traces(
        marker_line_color="rgba(0,0,0,0)",
        hovertemplate="<b>%{x}</b><br>%{y}<extra></extra>",
    )

    return apply_chart_theme(fig, theme, title)


def create_pie_chart(
    data, values_col: str, names_col: str, title: str, theme: str = "Light", **kwargs
) -> go.Figure:
    """
    Create a styled pie chart.

    Args:
        data: DataFrame or data source
        values_col: Values column name
        names_col: Names column name
        title: Chart title
        theme: Theme mode
        **kwargs: Additional plotly express arguments

    Returns:
        Styled Plotly figure
    """
    import plotly.express as px

    fig = px.pie(
        data,
        values=values_col,
        names=names_col,
        color_discrete_sequence=QUALITATIVE_COLORS,
        **kwargs,
    )

    # Update trace styling
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>%{value}<br>%{percent}<extra></extra>",
        marker=dict(line=dict(color="#ffffff", width=2)),
    )

    return apply_chart_theme(fig, theme, title)


def create_scatter_chart(
    data,
    x_col: str,
    y_col: str,
    title: str,
    theme: str = "Light",
    size_col: str = None,
    color_col: str = None,
    **kwargs,
) -> go.Figure:
    """
    Create a styled scatter chart.

    Args:
        data: DataFrame or data source
        x_col: X-axis column name
        y_col: Y-axis column name
        title: Chart title
        theme: Theme mode
        size_col: Column for marker size (optional)
        color_col: Column for color mapping (optional)
        **kwargs: Additional plotly express arguments

    Returns:
        Styled Plotly figure
    """
    import plotly.express as px

    color_discrete_map = kwargs.pop("color_discrete_map", None)
    if not color_discrete_map and color_col:
        unique_values = data[color_col].unique()
        color_discrete_map = {
            val: QUALITATIVE_COLORS[i % len(QUALITATIVE_COLORS)]
            for i, val in enumerate(unique_values)
        }

    fig = px.scatter(
        data,
        x=x_col,
        y=y_col,
        size=size_col,
        color=color_col,
        color_discrete_map=color_discrete_map,
        **kwargs,
    )

    # Update trace styling
    fig.update_traces(
        marker=dict(opacity=0.8, line=dict(width=1, color="rgba(255,255,255,0.3)")),
        hovertemplate="<b>%{x}</b><br>%{y}<extra></extra>",
    )

    return apply_chart_theme(fig, theme, title)


def create_area_chart(
    data,
    x_col: str,
    y_col: str,
    title: str,
    theme: str = "Light",
    color_col: str = None,
    **kwargs,
) -> go.Figure:
    """
    Create a styled area chart.

    Args:
        data: DataFrame or data source
        x_col: X-axis column name
        y_col: Y-axis column name
        title: Chart title
        theme: Theme mode
        color_col: Column for color mapping (optional)
        **kwargs: Additional plotly express arguments

    Returns:
        Styled Plotly figure
    """
    import plotly.express as px

    color_discrete_map = kwargs.pop("color_discrete_map", None)
    if not color_discrete_map and color_col:
        unique_values = data[color_col].unique()
        color_discrete_map = {
            val: QUALITATIVE_COLORS[i % len(QUALITATIVE_COLORS)]
            for i, val in enumerate(unique_values)
        }

    fig = px.area(
        data,
        x=x_col,
        y=y_col,
        color=color_col,
        color_discrete_map=color_discrete_map,
        **kwargs,
    )

    # Update trace styling
    fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y}<extra></extra>")

    return apply_chart_theme(fig, theme, title)


def add_chart_annotations(
    fig: go.Figure, annotations: List[Dict[str, Any]]
) -> go.Figure:
    """
    Add annotations to a chart with consistent styling.

    Args:
        fig: Plotly figure object
        annotations: List of annotation dictionaries

    Returns:
        Figure with annotations
    """
    for annotation in annotations:
        fig.add_annotation(
            x=annotation.get("x"),
            y=annotation.get("y"),
            text=annotation.get("text"),
            showarrow=annotation.get("showarrow", True),
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor=annotation.get("color", COLORS["primary"]),
            font=dict(size=12, color=annotation.get("color", COLORS["primary"])),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=annotation.get("color", COLORS["primary"]),
            borderwidth=1,
        )

    return fig


def get_color_palette(n_colors: int, palette_type: str = "qualitative") -> List[str]:
    """
    Get a color palette with specified number of colors.

    Args:
        n_colors: Number of colors needed
        palette_type: Type of palette ("qualitative" or "sequential")

    Returns:
        List of color hex codes
    """
    if palette_type == "sequential":
        if n_colors <= len(SEQUENTIAL_COLORS):
            return SEQUENTIAL_COLORS[:n_colors]
        else:
            # Extend with interpolated colors
            base_colors = SEQUENTIAL_COLORS
            extended = []
            for i in range(n_colors):
                idx = (i * (len(base_colors) - 1)) / (n_colors - 1)
                extended.append(base_colors[int(idx)])
            return extended
    else:
        # Qualitative colors
        if n_colors <= len(QUALITATIVE_COLORS):
            return QUALITATIVE_COLORS[:n_colors]
        else:
            # Repeat colors if needed
            return (QUALITATIVE_COLORS * ((n_colors // len(QUALITATIVE_COLORS)) + 1))[
                :n_colors
            ]
