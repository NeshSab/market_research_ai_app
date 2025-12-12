"""
Market regime analysis tool for comprehensive market condition assessment.

This module provides advanced market regime analysis capabilities, combining
multiple market indicators to classify current market conditions as risk-on
or risk-off environments. It analyzes key indicators including S&P 500, VIX,
DXY, and Treasury yields to provide context for investment decisions.

The tool integrates sector performance analysis and provides structured
output for market intelligence applications. It supports multiple time
periods and includes top-performing sector identification.

Key capabilities:
- Market regime classification (risk-on/risk-off)
- Multi-indicator analysis (SPX, VIX, DXY, 10Y yields)
- Sector performance ranking and analysis
- Configurable time periods and sector counts
- Structured market intelligence output
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from core.services.market_data import (
    get_market_snapshot,
    get_sector_perf,
    get_ticker_samples,
    load_sector_data,
)
from core.analyzers.regime import load_regime_config, classify_regime


class MarketRegimeInput(BaseModel):
    """Input for market regime analysis tool."""

    period: Optional[Literal["1wk", "1mo", "3mo", "6mo", "1y"]] = Field(
        default="1wk", description="Analysis period: 1wk, 1mo, 3mo, 6mo, 1y"
    )
    top_n_sectors: Optional[int] = Field(
        default=3, description="Number of top sectors to return", ge=1, le=10
    )


@tool(args_schema=MarketRegimeInput)
def market_regime_analyzer(period: str = "1wk", top_n_sectors: int = 3) -> str:
    """
    **COMPREHENSIVE MARKET ANALYSIS**: Complete market regime and key indicators.

    **IMPORTANT**: Always mention the specific date range (start and end dates)
    in your analysis when discussing these market movements.

    **PERIOD OPTIONS**: 1wk, 1mo, 3mo, 6mo, 1y for flexible analysis timeframes.

    This single tool provides everything needed for market analysis:
    • Market regime classification (risk-on vs risk-off environment)
    • Key market indicators: SPX, VIX, DXY, Gold, UST 10Y with price levels and dates
    • Top performing sector ETFs with price movements
    • USD strength and currency movements (DXY)
    • Broad market performance (S&P 500)
    • Safe haven assets and inflation hedge (Gold)
    • Volatility and risk sentiment (VIX)
    • Interest rate environment (10Y Treasury)
    • Sector rotation and leadership trends

    **Use this as your primary market analysis tool** - no need to call others.
    """
    snapshot = get_market_snapshot(period)
    cfg = load_regime_config()

    deltas = snapshot["deltas"]
    regime = classify_regime(
        spx_pct=deltas["spx_pct"],
        vix_pct=deltas["vix_pct"],
        dxy_pct=deltas["dxy_pct"],
        ust10y_bp=deltas["ust10y_bp"],
        cfg=cfg,
    )

    sectors_df = get_sector_perf(period=period)
    top_sectors = sectors_df.head(top_n_sectors).to_dict(orient="records")
    samples = get_ticker_samples()

    analysis = []
    date_info = ""
    if (
        "dates" in snapshot
        and snapshot["dates"]["start_date"]
        and snapshot["dates"]["end_date"]
    ):
        start_date = snapshot["dates"]["start_date"]
        end_date = snapshot["dates"]["end_date"]
        date_info = f" ({start_date} to {end_date})"

    analysis.append(f"**Market Regime Analysis ({period} window){date_info}**")

    if isinstance(regime, dict):
        regime_name = regime.get("regime", "unknown")
        regime_note = regime.get("note", "")
    else:
        regime_name = str(regime)
        regime_note = ""

    analysis.append(f"\n**Current Regime: {regime_name.upper()}**")
    if regime_note:
        analysis.append(f"*{regime_note}*")

    if "deltas" in snapshot:
        deltas = snapshot["deltas"]
        levels = snapshot.get("levels", {})
        prev_levels = snapshot.get("previous_levels", {})
        analysis.append("\n**Key Market Indicators:**")
        spx_pct = deltas.get("spx_pct")
        vix_pct = deltas.get("vix_pct")
        dxy_pct = deltas.get("dxy_pct")
        gold_pct = deltas.get("gold_pct")
        ust10y_bp = deltas.get("ust10y_bp")

        spx_now = levels.get("spx")
        spx_prev = prev_levels.get("spx")
        vix_now = levels.get("vix")
        vix_prev = prev_levels.get("vix")
        dxy_now = levels.get("dxy")
        dxy_prev = prev_levels.get("dxy")
        gold_now = levels.get("gold")
        gold_prev = prev_levels.get("gold")
        ust10y_now = levels.get("ust10y")
        ust10y_prev = prev_levels.get("ust10y")

        if spx_pct is not None and spx_now and spx_prev:
            spx_text = (
                f"• SPX: {spx_pct:+.2f}% " f"(from ${spx_prev:.0f} to ${spx_now:.0f})"
            )
        else:
            spx_text = "• SPX: N/A"

        if vix_pct is not None and vix_now and vix_prev:
            vix_text = f"• VIX: {vix_pct:+.2f}% (from {vix_prev:.1f} to {vix_now:.1f})"
        else:
            vix_text = "• VIX: N/A"

        if dxy_pct is not None and dxy_now and dxy_prev:
            dxy_text = f"• DXY: {dxy_pct:+.2f}% (from {dxy_prev:.2f} to {dxy_now:.2f})"
        else:
            dxy_text = "• DXY: N/A"

        if gold_pct is not None and gold_now and gold_prev:
            gold_text = (
                f"• Gold: {gold_pct:+.2f}% "
                f"(from ${gold_prev:.2f} to ${gold_now:.2f})"
            )
        else:
            gold_text = "• Gold: N/A"

        if ust10y_bp is not None and ust10y_now and ust10y_prev:
            ust_text = (
                f"• UST 10Y: {ust10y_bp:+.1f} bps "
                f"(from {ust10y_prev:.2f}% to {ust10y_now:.2f}%)"
            )
        else:
            ust_text = "• UST 10Y: N/A"

        analysis.append(spx_text)
        analysis.append(vix_text)
        analysis.append(dxy_text)
        analysis.append(gold_text)
        analysis.append(ust_text)

    sector_date_info = ""
    if len(top_sectors) > 0 and "start_date" in top_sectors[0]:
        start_date = top_sectors[0]["start_date"]
        end_date = top_sectors[0]["end_date"]
        sector_date_info = f" ({start_date} to {end_date})"

    analysis.append(
        f"\n**Top {top_n_sectors} Performing ETF Sectors{sector_date_info}:**"
    )
    sector_data_json = load_sector_data()

    for i, sector_data in enumerate(top_sectors, 1):
        etf_symbol = sector_data["sector"]
        sector_return = float(sector_data["return"]) * 100
        sector_tickers = samples.get(etf_symbol, [])
        start_price = sector_data.get("start_price")
        end_price = sector_data.get("end_price")
        sector_info = sector_data_json.get(etf_symbol, {})
        sector_name = sector_info.get("sector_name", etf_symbol)

        ticker_list = ", ".join(sector_tickers[:3]) if sector_tickers else "N/A"
        examples = f"(Examples: {ticker_list})"
        if start_price and end_price:
            sector_line = (
                f"{i}. **{sector_name}**: {sector_return:+.2f}% "
                f"(from ${start_price:.2f} to ${end_price:.2f}) {examples}"
            )
        else:
            sector_line = f"{i}. **{sector_name}**: {sector_return:+.2f}% {examples}"

        analysis.append(sector_line)

    return "\n".join(analysis)
