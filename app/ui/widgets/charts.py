"""
Market analysis charts module with consistent styling and professional visualization.

This module provides functions for creating various financial visualizations
using Plotly. Charts are designed with a consistent dark theme, professional
color palette, and standardized layout for market analysis applications.
"""

import json
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from pathlib import Path

from core.services.market_data import load_sector_data

PASTEL_COLORS_RGB = {
    "coral_orange": "rgb(248, 156, 116)",
    "aqua_blue": "rgb(102, 197, 204)",
    "sunny_yellow": "rgb(246, 207, 113)",
    "leafy_green": "rgb(135, 197, 95)",
    "soft_purple": "rgb(220, 176, 242)",
    "lavender_blue": "rgb(158, 185, 243)",
    "bubblegum_pink": "rgb(254, 136, 177)",
    "lime_zest": "rgb(201, 219, 116)",
    "mint_green": "rgb(139, 224, 164)",
    "purple_blue": "rgb(180, 151, 231)",
    "neutral_grey": "rgb(179, 179, 179)",
}
pastel_colors = list(PASTEL_COLORS_RGB.values())
pio.templates["plotly_dark"].layout.colorway = pastel_colors
pio.templates.default = "plotly_dark"


def _apply_standard_layout(
    fig: go.Figure,
    title: str,
    subtitle: str = "",
    show_legend: bool = True,
    legend_title: str = "",
) -> None:
    """
    Apply consistent styling to all charts.

    Parameters
    ----------
    fig : go.Figure
        Plotly figure to style
    title : str
        Chart title
    subtitle : str
        Chart subtitle
    show_legend : bool
        Whether to show legend
    legend_title : str
        Title for the legend
    """
    fig.update_layout(
        title=dict(
            text=title,
            xref="container",
            yref="container",
            xanchor="left",
            yanchor="bottom",
            y=0.9,
            x=0.02,
            font=dict(size=20),
        ),
        title_subtitle=dict(text=subtitle, font=dict(size=14)),
        margin=dict(l=100, r=50, t=130, b=60),
        showlegend=show_legend,
    )

    if show_legend:
        fig.update_layout(
            legend=dict(
                title=legend_title,
                orientation="h",
                yanchor="bottom",
                y=1,
                xanchor="center",
                x=0.5,
                itemsizing="constant",
            )
        )


def _load_market_indicator_names() -> dict[str, str]:
    """
    Load market indicator display names from JSON file.

    Returns
    -------
    dict[str, str]
        Dictionary mapping ticker symbols to display names
    """
    try:
        current_file = Path(__file__)
        indicators_file = (
            current_file.parent.parent.parent
            / "knowledge_base"
            / "semistatic"
            / "market_indicators.json"
        )

        if not indicators_file.exists():
            app_root = current_file.parent.parent
            indicators_file = (
                app_root / "knowledge_base" / "semistatic" / "market_indicators.json"
            )
        if not indicators_file.exists():
            indicators_file = (
                Path.cwd() / "knowledge_base" / "semistatic" / "market_indicators.json"
            )

        with open(indicators_file, "r") as f:
            data = json.load(f)
            indicators = data.get("market_indicators", {})

            simple_mapping = {}
            for symbol, info in indicators.items():
                if isinstance(info, dict):
                    simple_mapping[symbol] = info.get("name", symbol)
                else:
                    simple_mapping[symbol] = str(info)

            return simple_mapping
    except Exception:
        return {}


def _get_display_name(symbol: str, indicator_names: dict[str, str]) -> str:
    """
    Get user-friendly display name for a market indicator.

    Parameters
    ----------
    symbol : str
        The ticker symbol or column name
    indicator_names : dict[str, str]
        Dictionary of symbol to display name mappings

    Returns
    -------
    str
        User-friendly display name
    """
    return indicator_names.get(symbol, symbol)


def _normalize_data(df: pd.DataFrame, mode: str) -> tuple[pd.DataFrame, str]:
    """
    Apply normalization to DataFrame based on specified mode.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to normalize
    mode : str
        Normalization mode: 'base', 'min-max', 'mean', or 'zscore'

    Returns
    -------
    tuple[pd.DataFrame, str]
        Normalized DataFrame and corresponding y-axis title
    """
    if mode == "base":
        base = df.iloc[0]
        norm = (df / base) * 100
        ytitle = "Performance (% from start)"
    elif mode == "min-max":
        min_val = df.min()
        max_val = df.max()
        norm = (df - min_val) / (max_val - min_val) * 100
        ytitle = "Scaled (0-100)"
    elif mode == "mean":
        mean_val = df.mean()
        norm = (df / mean_val) * 100
        ytitle = "Performance (% vs average)"
    elif mode == "zscore":
        norm = (df - df.mean()) / df.std()
        ytitle = "Z-score"
    else:
        raise ValueError(
            "Invalid normalization mode. Use 'base', 'min-max', 'mean', or 'zscore'."
        )

    return norm, ytitle


def market_regime_chart(
    df: pd.DataFrame,
    title: str = "Market Regime Indicators",
    subtitle: str = "scaled by min-max normalization",
    mode: str = "min-max",
) -> go.Figure:
    """
    Create market regime indicators chart with professional styling.

    Designed for comparing market indicators like DXY, S&P500, Gold, VIX
    on a normalized scale for regime analysis.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with time series data for market indicators
    title : str
        Chart title
    subtitle : str
        Chart subtitle
    mode : str
        Normalization mode: 'base', 'min-max', 'mean', or 'zscore'

    Returns
    -------
    go.Figure
        Styled Plotly figure
    """
    norm, ytitle = _normalize_data(df, mode)
    indicator_names = _load_market_indicator_names()

    fig = go.Figure()
    for i, col in enumerate(norm.columns):
        color = pastel_colors[i % len(pastel_colors)]
        display_name = _get_display_name(col, indicator_names)

        fig.add_trace(
            go.Scatter(
                x=norm.index,
                y=norm[col],
                mode="lines",
                name=display_name,
                line=dict(width=2.5, color=color),
                hovertemplate=f"%{{y:.1f}}<br>{display_name}<br>%{{x}}<extra></extra>",
            )
        )

    _apply_standard_layout(fig, title, subtitle)
    fig.update_yaxes(title_text=ytitle)
    fig.update_xaxes(tickformat="%Y-%m-%d")

    return fig


def sector_bar(
    df_sec: pd.DataFrame,
    title: str = "Sector Performance Analysis",
    subtitle: str = "weekly returns by sector",
) -> go.Figure:
    """
    Create sector performance bar chart with professional styling.

    Parameters
    ----------
    df_sec : pd.DataFrame
        DataFrame with 'sector' and 'return' columns
    title : str
        Chart title
    subtitle : str
        Chart subtitle

    Returns
    -------
    go.Figure
        Styled Plotly figure
    """
    sector_data = load_sector_data()

    df_sorted = df_sec.sort_values("return", ascending=False)
    if df_sorted["return"].abs().max() < 1:
        df_sorted = df_sorted.copy()
        df_sorted["return"] = df_sorted["return"] * 100

    colors = [
        (
            PASTEL_COLORS_RGB["leafy_green"]
            if ret >= 0
            else PASTEL_COLORS_RGB["coral_orange"]
        )
        for ret in df_sorted["return"]
    ]

    fig = go.Figure()

    hover_texts = []
    for _, row in df_sorted.iterrows():
        etf_symbol = row["sector"]
        sector_info = sector_data.get(etf_symbol, {})
        sector_name = sector_info.get("sector_name", "")

        if sector_name and sector_name != etf_symbol:
            friendly_name = f"{etf_symbol} ({sector_name})"
        else:
            friendly_name = etf_symbol

        hover_texts.append(friendly_name)

    fig.add_trace(
        go.Bar(
            x=df_sorted["sector"],
            y=df_sorted["return"],
            marker=dict(color=colors),
            text=[f"{ret:+.1f}%" for ret in df_sorted["return"]],
            textposition="outside",
            customdata=hover_texts,
            hovertemplate="%{customdata}<br>Return: %{y:.1f}%<extra></extra>",
        )
    )

    _apply_standard_layout(fig, title, subtitle, show_legend=False)
    fig.update_xaxes(title_text="Sector ETF", tickangle=45)

    y_max = df_sorted["return"].max()
    y_min = df_sorted["return"].min()
    y_range = y_max - y_min
    padding = y_range * 0.15

    fig.update_yaxes(
        title_text="Weekly Return (%)", range=[y_min - padding, y_max + padding]
    )

    return fig


def ticker_comparison_chart(
    df: pd.DataFrame,
    title: str = "Performance Comparison Analysis",
    subtitle: str = "scaled by min-max normalization",
    method: str = "min-max",
) -> go.Figure:
    """
    Create professional ticker comparison line chart.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns for ticker, sector, and market data
    title : str
        Chart title
    subtitle : str
        Chart subtitle
    method : str
        Normalization method: "min-max", "base", or "zscore"

    Returns
    -------
    go.Figure
        Styled Plotly figure
    """
    if method in ["min-max", "base", "zscore"]:
        norm, yaxis_title = _normalize_data(df, method)
    else:
        norm = df
        yaxis_title = "Price"

    fig = go.Figure()

    comparison_colors = [
        PASTEL_COLORS_RGB["aqua_blue"],
        PASTEL_COLORS_RGB["sunny_yellow"],
        PASTEL_COLORS_RGB["leafy_green"],
    ]

    for idx, col in enumerate(norm.columns):
        color = comparison_colors[idx % len(comparison_colors)]
        line_width = 3 if idx == 0 else 2

        fig.add_trace(
            go.Scatter(
                x=norm.index,
                y=norm[col],
                mode="lines",
                name=col,
                line=dict(width=line_width, color=color),
                hovertemplate=f"%{{y:.1f}}<br>{col}<br>%{{x}}<extra></extra>",
            )
        )

    _apply_standard_layout(fig, title, subtitle)
    fig.update_xaxes(tickformat="%Y-%m-%d", dtick="D1")
    fig.update_yaxes(title_text=yaxis_title)
    fig.update_layout(hovermode="x unified")

    return fig
