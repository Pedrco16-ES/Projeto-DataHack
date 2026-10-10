"""Gráficos interativos padronizados com Plotly e paleta oficial Univag."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Cores oficiais Univag
UNIVAG_COLORS = {
    "navy": "#1A2B5E",
    "blue": "#0066CC",
    "light_blue": "#00AEF0",
    "purple": "#6F42C1",
    "pink": "#E83E8C",
    "good": "#28A745",
    "warning": "#FFC107",
    "critical": "#DC3545",
    "neutral": "#6C757D",
}


def apply_theme(fig: go.Figure, title: str = "", height: int = 420) -> go.Figure:
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>" if title else "",
            "font": {"size": 16, "color": UNIVAG_COLORS["navy"], "family": "Segoe UI, sans-serif"},
            "x": 0.0,
            "xanchor": "left"
        },
        height=height,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font={"color": UNIVAG_COLORS["navy"], "family": "Segoe UI, sans-serif", "size": 12},
        margin={"l": 40, "r": 30, "t": 50 if title else 25, "b": 40},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.22,
            "xanchor": "center",
            "x": 0.5,
            "title": {"text": ""}
        },
        hoverlabel={"bgcolor": "#FFFFFF", "font_size": 12, "font_family": "Segoe UI, sans-serif"}
    )
    fig.update_xaxes(showgrid=True, gridcolor="#F1F5F9", linecolor="#CBD5E1")
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", linecolor="#CBD5E1")
    return fig


def plot_stacked_trajetoria(df: pd.DataFrame, title: str = "Trajetória Acumulada dos Ingressantes (100%)") -> go.Figure:
    """Gráfico de barras empilhadas 100% (Desistência, Conclusão, Permanência)."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["ano_curso"],
        y=df["tda"],
        name="Desistência Acumulada (TDA)",
        marker_color=UNIVAG_COLORS["critical"],
        text=[f"{v:.1f}%" for v in df["tda"]],
        textposition="inside",
        hovertemplate="<b>%{x}</b><br>Desistência Acumulada: <b>%{y:.2f}%</b><extra></extra>"
    ))

    fig.add_trace(go.Bar(
        x=df["ano_curso"],
        y=df["tca"],
        name="Conclusão Acumulada (TCA)",
        marker_color=UNIVAG_COLORS["good"],
        text=[f"{v:.1f}%" for v in df["tca"]],
        textposition="inside",
        hovertemplate="<b>%{x}</b><br>Conclusão Acumulada: <b>%{y:.2f}%</b><extra></extra>"
    ))

    fig.add_trace(go.Bar(
        x=df["ano_curso"],
        y=df["tap"],
        name="Permanência / Cursando (TAP)",
        marker_color=UNIVAG_COLORS["blue"],
        text=[f"{v:.1f}%" for v in df["tap"]],
        textposition="inside",
        hovertemplate="<b>%{x}</b><br>Permanência no Curso: <b>%{y:.2f}%</b><extra></extra>"
    ))

    fig.update_layout(barmode="stack", yaxis={"range": [0, 100], "ticksuffix": "%"})
    return apply_theme(fig, title)


def plot_horizontal_ranking(
    df: pd.DataFrame,
    cat_col: str,
    val_col: str,
    title: str = "",
    color: str = UNIVAG_COLORS["blue"],
    suffix: str = "%"
) -> go.Figure:
    """Ranking em barras horizontais ordenadas."""
    df_sorted = df.sort_values(val_col, ascending=True)

    fig = go.Figure(go.Bar(
        x=df_sorted[val_col],
        y=df_sorted[cat_col],
        orientation="h",
        marker_color=color,
        text=[f"{v:.1f}{suffix}" for v in df_sorted[val_col]],
        textposition="outside",
        hovertemplate=f"<b>%{{y}}</b><br>Valor: <b>%{{x:.2f}}{suffix}</b><extra></extra>"
    ))
    fig.update_layout(xaxis={"ticksuffix": suffix})
    return apply_theme(fig, title)


def plot_evolution_lines(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    group_col: str,
    title: str = "",
    y_suffix: str = ""
) -> go.Figure:
    """Linhas de evolução temporal por grupo."""
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        color=group_col,
        markers=True,
        color_discrete_sequence=[
            UNIVAG_COLORS["blue"],
            UNIVAG_COLORS["purple"],
            UNIVAG_COLORS["light_blue"],
            UNIVAG_COLORS["pink"]
        ]
    )
    fig.update_traces(line={"width": 3}, marker={"size": 7})
    fig.update_layout(yaxis={"ticksuffix": y_suffix})
    return apply_theme(fig, title)


def plot_scatter_correlation(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    hover_name: str,
    title: str = "",
    color_col: str | None = None
) -> go.Figure:
    """Dispersão entre variáveis."""
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        hover_name=hover_name,
        color=color_col,
        color_discrete_sequence=[UNIVAG_COLORS["blue"], UNIVAG_COLORS["purple"], UNIVAG_COLORS["good"]],
        opacity=0.75
    )
    return apply_theme(fig, title)
