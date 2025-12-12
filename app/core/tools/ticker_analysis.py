"""
Individual stock ticker analysis tool for comprehensive equity research.

This module provides detailed analysis capabilities for individual stock
tickers, combining market data, fundamental metrics, and knowledge base
insights to deliver comprehensive equity research reports.

The tool integrates real-time price data, fundamental analysis metrics,
and semantic search over the knowledge base to provide contextual analysis
for investment decision-making and portfolio management.

Key features:
- Multi-period price performance analysis
- Fundamental metrics and valuation ratios
- Knowledge base context integration
- Comprehensive ticker research reports
- Flexible timeframe analysis capabilities
"""

import logging
from typing import Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from core.services.market_data import (
    get_ticker_info,
    get_ticker_fundamentals,
)
from core.services.retrievers import retrieve_semantic


class TickerAnalysisInput(BaseModel):
    """Input for ticker analysis tool."""

    ticker: str = Field(
        description="Stock ticker symbol (e.g., 'AAPL', 'TSLA', 'MSFT')"
    )
    period: Optional[Literal["1wk", "1mo", "3mo", "6mo", "1y"]] = Field(
        default="1wk", description="Analysis period: 1wk, 1mo, 3mo, 6mo, 1y"
    )


@tool(args_schema=TickerAnalysisInput)
def ticker_analyzer(ticker: str, period: str = "1wk") -> str:
    """
    **TICKER ANALYSIS**: Get comprehensive analysis of a specific stock ticker.

    **PERIOD OPTIONS**: 1wk, 1mo, 3mo, 6mo, 1y for flexible analysis timeframes.

    Use this for:
    • Getting performance metrics vs S&P 500 and sector
    • Understanding company fundamentals (P/E, market cap, etc.)
    • Analyzing relative outperformance or underperformance
    • Sector context and comparison with peers
    """
    try:
        ticker_data = get_ticker_info(ticker.upper(), period)
        fundamentals = get_ticker_fundamentals(ticker.upper())

        sector = ticker_data["sector"]
        query = (
            f"Explain {sector} sector performance drivers and "
            f"key factors affecting {sector} stocks"
        )
        from pathlib import Path
        app_dir = Path(__file__).parent.parent.parent
        index_path = app_dir / "var" / "faiss_index"
        docs = retrieve_semantic(str(index_path), query, k=2)

        comparison_df = ticker_data.get("comparison_data")
        date_info = ""
        if comparison_df is not None and not comparison_df.empty:
            start_date = comparison_df.index[0].strftime("%Y-%m-%d")
            end_date = comparison_df.index[-1].strftime("%Y-%m-%d")
            date_info = f" ({start_date} to {end_date})"
        analysis = []
        analysis.append(f"**{ticker.upper()} Analysis ({period.upper()}){date_info}**")
        analysis.append(f"**Company**: {ticker_data['company_name']}")
        analysis.append(f"**Sector**: {sector}")
        analysis.append(f"**Current Price**: ${ticker_data['current_price']:.2f}")

        if comparison_df is not None and not comparison_df.empty:
            ticker_symbol = ticker_data["ticker"]
            if ticker_symbol in comparison_df.columns:
                actual_start = comparison_df[ticker_symbol].iloc[0]
                actual_end = ticker_data["current_price"]
                range_display = (
                    f"**{period.upper()} Range**: "
                    f"${actual_start:.2f} to ${actual_end:.2f}"
                )
                analysis.append(range_display)
            else:
                period_low = ticker_data["period_low"]
                period_high = ticker_data["period_high"]
                analysis.append(
                    f"**Period Range**: ${period_low:.2f} - ${period_high:.2f}"
                )
        else:
            period_low = ticker_data["period_low"]
            period_high = ticker_data["period_high"]
            analysis.append(f"**Period Range**: ${period_low:.2f} - ${period_high:.2f}")

        analysis.append(f"**Analysis Period**: {period.upper()}")
        analysis.append(f"\n**Performance Metrics ({period.upper()}):**")

        ticker_perf = ticker_data["ticker_return"]
        if comparison_df is not None and not comparison_df.empty:
            ticker_symbol = ticker_data["ticker"]
            if ticker_symbol in comparison_df.columns:
                start_price = comparison_df[ticker_symbol].iloc[0]
                current_price = ticker_data["current_price"]
                ticker_line = (
                    f"• {ticker.upper()}: {ticker_perf:+.2f}% "
                    f"(from ${start_price:.2f} to ${current_price:.2f})"
                )
            else:
                ticker_line = f"• {ticker.upper()}: {ticker_perf:+.2f}%"
        else:
            ticker_line = f"• {ticker.upper()}: {ticker_perf:+.2f}%"

        analysis.append(ticker_line)
        analysis.append(f"• {sector} Sector: {ticker_data['sector_return']:+.2f}%")
        analysis.append(f"• S&P 500: {ticker_data['spx_return']:+.2f}%")

        analysis.append("\n**Relative Performance:**")
        analysis.append(f"• vs S&P 500: {ticker_data['outperformance_vs_spx']:+.2f}%")
        analysis.append(f"• vs Sector: {ticker_data['outperformance_vs_sector']:+.2f}%")

        if isinstance(fundamentals, dict) and fundamentals:
            analysis.append("\n**Key Fundamentals:**")
            key_metrics = [
                "marketCap",
                "trailingPE",
                "forwardPE",
                "dividendYield",
                "beta",
            ]
            for metric in key_metrics:
                if metric in fundamentals and fundamentals[metric] is not None:
                    value = fundamentals[metric]
                    if metric == "marketCap":
                        if value > 1e9:
                            analysis.append(f"• Market Cap: ${value/1e9:.1f}B")
                        elif value > 1e6:
                            analysis.append(f"• Market Cap: ${value/1e6:.1f}M")
                        else:
                            analysis.append(f"• Market Cap: ${value:,.0f}")
                    elif "PE" in metric:
                        analysis.append(
                            f"• {metric.replace('PE', ' P/E')}: {value:.1f}"
                        )
                    elif metric == "dividendYield":
                        analysis.append(f"• Dividend Yield: {value:.2%}")
                    elif metric == "beta":
                        analysis.append(f"• Beta: {value:.2f}")

        if docs:
            analysis.append(f"\n**{sector} Sector Context:**")
            for doc in docs[:1]:
                snippet = doc.page_content[:300].strip()
                if snippet:
                    analysis.append(f"• {snippet}...")

        return "\n".join(analysis)

    except ValueError as e:
        error_msg = str(e)
        if "No data available" in error_msg or "No price data" in error_msg:
            logging.error(
                f"Data retrieval error for ticker {ticker.upper()}: {error_msg}"
            )
            return (
                f"❌ **Error**: Ticker '{ticker.upper()}' not found "
                f"or has no price data available."
            )
        elif "Invalid ticker" in error_msg.lower():
            logging.error(f"Invalid ticker symbol provided: {ticker.upper()}")
            return f"❌ **Error**: '{ticker.upper()}' is not a valid ticker symbol."
        else:
            logging.error(f"ValueError analyzing ticker {ticker.upper()}: {error_msg}")
            return f"❌ **Error**: Unable to analyze {ticker.upper()}: {error_msg}"

    except Exception as e:
        logging.error(f"Unexpected error analyzing ticker {ticker.upper()}: {e}")
        return f"❌ **Error**: Unexpected error analyzing {ticker.upper()}: {str(e)}"
