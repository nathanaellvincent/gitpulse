"""Plotly chart builders, themed to match the dark Streamlit config."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


# Shared palette. Kept in one place so every chart agrees on colour.
ACCENT = "#60a5fa"
ACCENT_SOFT = "#93c5fd"
INK = "#e6edf3"
INK_DIM = "#6b7a8f"
SURFACE = "#0f172a"


def _apply_theme(fig: go.Figure, height: int = 320) -> go.Figure:
    """Common styling: dark plot bg, dim gridlines, readable axes."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=30),
        font=dict(color=INK, family="Inter, system-ui"),
        hoverlabel=dict(bgcolor=SURFACE, font_color=INK),
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="rgba(107,122,143,0.15)", linecolor=INK_DIM)
    fig.update_yaxes(gridcolor="rgba(107,122,143,0.15)", linecolor=INK_DIM)
    return fig


def weekly_activity_chart(weekly_df: pd.DataFrame) -> go.Figure:
    """Area chart of commits per ISO week.

    An area fill under the line reads better than bars for long
    timelines — your eye tracks the silhouette rather than counting
    individual bars.
    """
    fig = go.Figure()
    if weekly_df.empty:
        return _apply_theme(fig)

    fig.add_trace(
        go.Scatter(
            x=weekly_df["week"],
            y=weekly_df["commits"],
            mode="lines",
            line=dict(color=ACCENT, width=2),
            fill="tozeroy",
            fillcolor="rgba(96,165,250,0.18)",
            hovertemplate="Week of %{x|%b %d, %Y}<br>%{y} commits<extra></extra>",
        )
    )
    return _apply_theme(fig)
