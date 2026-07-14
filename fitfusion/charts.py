"""Reusable Plotly chart builders styled to the FitFusion dark/glass theme."""
import plotly.graph_objects as go

from fitfusion.config import GOLD, BLUE, GREEN, TEXT_SECONDARY

_LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#FFFFFF"),
    margin=dict(l=10, r=10, t=30, b=10),
)


def progress_ring(value: float, max_value: float, label: str, color: str = GOLD, suffix: str = "") -> go.Figure:
    pct = 0 if max_value <= 0 else max(0, min(100, round(value / max_value * 100)))
    fig = go.Figure(go.Pie(
        values=[pct, 100 - pct], hole=0.75, rotation=90, direction="clockwise",
        marker=dict(colors=[color, "#242424"]), textinfo="none", hoverinfo="skip", sort=False,
    ))
    fig.update_layout(
        **_LAYOUT_BASE, showlegend=False, height=190,
        annotations=[
            dict(text=f"<b>{pct}%</b>", x=0.5, y=0.56, font=dict(size=22, color="#FFFFFF"), showarrow=False),
            dict(text=f"{label}", x=0.5, y=0.34, font=dict(size=11, color=TEXT_SECONDARY), showarrow=False),
        ],
    )
    return fig


def line_trend(dates: list[str], values: list[float], label: str, color: str = BLUE) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=dates, y=values, mode="lines+markers", line=dict(color=color, width=3, shape="spline"),
        marker=dict(size=6, color=color), fill="tozeroy", fillcolor=_alpha(color, 0.12), name=label,
    ))
    fig.update_layout(
        **_LAYOUT_BASE, height=260,
        xaxis=dict(showgrid=False, color=TEXT_SECONDARY),
        yaxis=dict(showgrid=True, gridcolor="#242424", color=TEXT_SECONDARY),
    )
    return fig


def bar_weekly(labels: list[str], values: list[float], label: str, color: str = GREEN) -> go.Figure:
    fig = go.Figure(go.Bar(x=labels, y=values, marker=dict(color=color, line=dict(width=0)), name=label))
    fig.update_layout(
        **_LAYOUT_BASE, height=240,
        xaxis=dict(showgrid=False, color=TEXT_SECONDARY),
        yaxis=dict(showgrid=True, gridcolor="#242424", color=TEXT_SECONDARY),
        bargap=0.35,
    )
    return fig


def macro_donut(protein_g: float, carbs_g: float, fat_g: float) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=["Protein", "Carbs", "Fat"], values=[protein_g, carbs_g, fat_g],
        hole=0.55, marker=dict(colors=[BLUE, GOLD, GREEN]),
        textinfo="label+percent", textfont=dict(color="#FFFFFF", size=12),
    ))
    fig.update_layout(**_LAYOUT_BASE, height=280, showlegend=False)
    return fig


def dual_line(dates: list[str], series_a: list[float], series_b: list[float], name_a: str, name_b: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=series_a, name=name_a, mode="lines+markers", line=dict(color=GOLD, width=3)))
    fig.add_trace(go.Scatter(x=dates, y=series_b, name=name_b, mode="lines+markers", line=dict(color=BLUE, width=3)))
    fig.update_layout(
        **_LAYOUT_BASE, height=280,
        xaxis=dict(showgrid=False, color=TEXT_SECONDARY),
        yaxis=dict(showgrid=True, gridcolor="#242424", color=TEXT_SECONDARY),
        legend=dict(orientation="h", y=1.15, font=dict(color="#FFFFFF")),
    )
    return fig


def _alpha(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
