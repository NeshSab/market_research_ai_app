"""
Sector performance analysis tool for equity market sector strength assessment.

This module provides comprehensive sector strength analysis capabilities,
enabling identification of sector rotation patterns and relative performance
trends across different time periods. It supports investment decision-making
through detailed sector performance rankings and analysis.

The tool leverages real-time market data to analyze sector ETF performance
and provides structured output for sector allocation strategies and rotation
analysis workflows.

Key capabilities:
- Multi-period sector performance analysis
- Sector rotation pattern identification
- Relative strength ranking and comparison
- Investment decision support analytics
- Flexible timeframe analysis (1wk to 1y)
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from core.services.market_data import get_sector_perf, load_sector_data


class SectorStrengthInput(BaseModel):
    """Input for sector strength analysis tool."""

    period: Optional[Literal["1wk", "1mo", "3mo", "6mo", "1y"]] = Field(
        default="1wk", description="Analysis period: 1wk, 1mo, 3mo, 6mo, 1y"
    )


@tool(args_schema=SectorStrengthInput)
def sector_strength_analyzer(period: str = "1wk") -> str:
    """
    **SECTOR ANALYSIS**: Get comprehensive sector performance rankings.

    **PERIOD OPTIONS**: 1wk, 1mo, 3mo, 6mo, 1y for flexible analysis timeframes.

    Use this for:
    • Identifying sector rotation patterns and trends
    • Finding outperforming and underperforming sectors
    • Analyzing relative sector strength over time
    • Supporting sector allocation and investment decisions
    """
    df = get_sector_perf(period=period)
    analysis = []
    date_info = ""
    if not df.empty and "start_date" in df.columns and "end_date" in df.columns:
        first_row = df.iloc[0]
        start_date = first_row.get("start_date")
        end_date = first_row.get("end_date")
        if start_date and end_date:
            date_info = f" ({start_date} to {end_date})"

    analysis.append(f"**Sector Performance Rankings ({period}){date_info}**")

    if not df.empty:
        analysis.append("\n**ETF Sector Performance Ranking (Best to Worst):**")
        sector_data = load_sector_data()

        for i, row in df.iterrows():
            etf_symbol = row.get("sector", "Unknown")
            performance = row.get("return", 0) * 100
            rank = i + 1
            start_price = row.get("start_price")
            end_price = row.get("end_price")
            sector_info = sector_data.get(etf_symbol, {})
            sector_name = sector_info.get("sector_name", etf_symbol)
            display_name = f"{etf_symbol} ({sector_name})"

            if performance > 5:
                indicator = "Strong Outperformer"
            elif performance > 0:
                indicator = "Positive"
            elif performance > -5:
                indicator = "Negative"
            else:
                indicator = "Underperformer"
            price_context = ""
            if start_price and end_price:
                price_context = f" (from ${start_price:.2f} to ${end_price:.2f})"

            analysis.append(
                f"{rank}. **{display_name}**: "
                f"{performance:+.2f}%{price_context} {indicator}"
            )

        best_performer = df.iloc[0]
        worst_performer = df.iloc[-1]
        analysis.append("\n**Summary:**")
        best_return = best_performer.get("return", 0) * 100
        worst_return = worst_performer.get("return", 0) * 100
        spread = best_return - worst_return

        analysis.append(f"• Best: {best_performer.get('sector')} ({best_return:+.2f}%)")
        worst_sector = worst_performer.get("sector")
        analysis.append(f"• Worst: {worst_sector} ({worst_return:+.2f}%)")
        analysis.append(f"• Spread: {spread:.2f} percentage points")
    else:
        analysis.append("\nNo sector performance data available for this period.")

    return "\n".join(analysis)
