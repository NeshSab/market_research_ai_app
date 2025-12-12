"""
Individual ticker analysis prompt templates for equity research reports.

This module provides specialized prompt templates for generating detailed
individual stock analysis reports, including performance comparisons,
sector context, and market-relative analysis.

The prompts are designed to create concise, fact-based equity analysis
that highlights key performance drivers and relative positioning within
sectors and broader market context.

Key features:
- Ticker performance analysis templates
- Sector and market comparison frameworks
- Concise equity analysis guidelines
- Outperformance/underperformance highlighting
- Structured stock analysis reporting
"""

from textwrap import dedent


def system_prompt() -> str:
    """
    Generate system prompt for ticker deep-dive analysis.
    
    Creates focused system prompt for generating concise equity analysis
    with emphasis on relative performance and key insights.
    
    Returns
    -------
    str
        System prompt for ticker analysis tasks
    """
    return dedent(
        """
        You are a concise equity analyst.
        Analyze the ticker's performance relative to its sector and the S&P 500.
        Be factual and use the provided data. Highlight key insights about
        outperformance/underperformance.
        Keep analysis under 200 words.
    """
    ).strip()


def user_prompt(
    *,
    ticker: str,
    company_name: str,
    sector: str,
    period: str,
    ticker_return: float,
    sector_return: float,
    spx_return: float,
    outperformance_vs_spx: float,
    outperformance_vs_sector: float,
    market_context: str,
    fundamentals_text: str,
    docs_text: str,
) -> str:
    """
    Generate comprehensive user prompt for ticker analysis.
    
    Parameters
    ----------
    ticker : str
        Stock ticker symbol
    company_name : str
        Company full name
    sector : str
        Industry sector classification
    period : str
        Analysis time period
    ticker_return : float
        Stock return for the period
    sector_return : float
        Sector return for comparison
    spx_return : float
        S&P 500 return for benchmark
    outperformance_vs_spx : float
        Relative performance vs market
    outperformance_vs_sector : float
        Relative performance vs sector
    market_context : str
        Market regime and context information
    fundamentals_text : str
        Fundamental analysis data
    docs_text : str
        Supporting documentation context
        
    Returns
    -------
    str
        Complete user prompt with all analysis data
    """
    return dedent(
        f"""
        Ticker Analysis Data:

        Company: {company_name} ({ticker})
        Sector: {sector}
        Analysis Period: {period}

        Performance Metrics:
        - {ticker}: {ticker_return:.2f}%
        - {sector} Sector: {sector_return:.2f}%
        - S&P 500: {spx_return:.2f}%

        Relative Performance:
        - vs S&P 500: {outperformance_vs_spx:+.2f}%
        - vs Sector: {outperformance_vs_sector:+.2f}%

        Market Context: {market_context}

        Fundamentals:
        {fundamentals_text}

        Sector Analysis Context:
        {docs_text}

        Please provide a concise analysis of this ticker's performance.
    """
    ).strip()
