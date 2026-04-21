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


def contributors_bar_chart(contributors_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar of contribution counts per top contributor.

    Horizontal reads better than vertical here — login names can be
    long and rotating x-axis labels always looks scrappy.
    """
    fig = go.Figure()
    if contributors_df.empty:
        return _apply_theme(fig)

    ordered = contributors_df.sort_values("contributions")
    fig.add_trace(
        go.Bar(
            x=ordered["contributions"],
            y=ordered["login"],
            orientation="h",
            marker=dict(color=ACCENT, line=dict(width=0)),
            hovertemplate="%{y}<br>%{x} commits<extra></extra>",
        )
    )
    return _apply_theme(fig, height=max(320, 30 * len(ordered)))


# Palette for language pie. Extended cool-leaning gradient that plays
# nicely with the dark theme; cycles if more than eight languages.
_LANG_PALETTE = [
    "#60a5fa",  # accent
    "#818cf8",  # violet
    "#22d3ee",  # cyan
    "#34d399",  # emerald
    "#f472b6",  # pink
    "#facc15",  # amber
    "#fb923c",  # orange
    "#a78bfa",  # purple
]


def language_pie_chart(languages: dict[str, int]) -> go.Figure:
    """Donut chart of language byte counts.

    Donut (hole=0.55) instead of a flat pie keeps the chart from
    dominating when the repo is 99% one language — the centre stays
    empty so the surrounding density reads at a glance.
    """
    fig = go.Figure()
    if not languages:
        return _apply_theme(fig)

    labels = list(languages.keys())
    values = list(languages.values())
    colours = [_LANG_PALETTE[i % len(_LANG_PALETTE)] for i in range(len(labels))]

    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colours, line=dict(color=SURFACE, width=1)),
            textinfo="label+percent",
            hovertemplate="%{label}<br>%{value:,} bytes (%{percent})<extra></extra>",
            sort=True,
            direction="clockwise",
        )
    )
    fig = _apply_theme(fig, height=360)
    fig.update_layout(showlegend=False)
    return fig
