"""
Market analysis and market pulse generation prompt templates.

This module provides specialized prompt templates for generating market
analysis reports and market pulse summaries. The prompts are designed
to create concise, factual analysis based on market regime data, sector
performance, and supporting documentation.

The templates integrate real-time market data with analytical frameworks
to produce professional market commentary suitable for investment
decision-making and market research applications.

Key features:
- Market regime analysis integration
- Sector performance incorporation
- Timestamp-aware analysis context
- Factual, non-speculative analysis tone
- Structured market pulse generation
"""

from __future__ import annotations
from textwrap import dedent
from datetime import datetime


def system_prompt() -> str:
    """
    Generate system prompt for market pulse analysis.

    Creates a focused system prompt that guides the assistant to produce
    factual, concise market analysis avoiding overconfidence and speculation.

    Returns
    -------
    str
        System prompt for market analysis tasks
    """
    return dedent(
        """
        You are a concise market analyst.
        Use the provided regime and docs. Be factual and avoid overconfidence.
        Include change_pct exactly as provided in top_sectors for each sector.
    """
    ).strip()


def user_prompt(
    *, regime_text: str, sectors_text: str, docs_text: str, timestamp: str = None
) -> str:
    """User prompt for market pulse with dynamic data."""
    if not timestamp:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d")

    return dedent(
        f"""
        Market Analysis Data:
        As of: {timestamp}
        Current Market Regime: {regime_text}

        Top Performing Sectors:
        {sectors_text}

        Knowledge Base Context:
        {docs_text}

        Please analyze this market data and provide insights.
    """
    ).strip()
