"""
RAG search query templates for knowledge base document retrieval.

This module provides specialized query templates for retrieving relevant
information from the knowledge base using RAG (Retrieval-Augmented Generation)
techniques. The queries are designed to find contextual information for
market analysis, sector research, and individual ticker analysis.

The templates support various analysis workflows including market pulse
generation, sector analysis, ticker fundamentals research, and thematic
investment research with optimized search patterns for maximum relevance.

Key features:
- Market regime and sector rotation queries
- Sector-specific performance driver research
- Individual ticker fundamental analysis
- Thematic investment research templates
- Optimized search query construction
"""

from textwrap import dedent


def market_pulse_rag_query() -> str:
    """
    Generate RAG query for market regime and sector rotation context.
    
    Creates search query optimized for retrieving information about
    market regime impacts on asset classes and sector rotation patterns.
    
    Returns
    -------
    str
        Search query for market regime context retrieval
    """
    return dedent(
        """
        Explain USD/rates effect on equities, commodities 
        and sector rotation in risk-on vs risk-off.
    """
    ).strip()


def sector_analysis_rag_query(sector: str) -> str:
    """
    Generate RAG query for sector-specific performance analysis.
    
    Parameters
    ----------
    sector : str
        Sector name for performance driver analysis
        
    Returns
    -------
    str
        Search query for sector performance context
    """
    return (f"Explain {sector} sector performance drivers and key factors "
            f"affecting {sector} stocks")


def ticker_fundamentals_rag_query(ticker: str, sector: str) -> str:
    """
    Generate RAG query for individual ticker fundamental analysis.
    
    Parameters
    ----------
    ticker : str
        Stock ticker symbol for analysis
    sector : str
        Sector context for the ticker
        
    Returns
    -------
    str
        Search query for ticker fundamental analysis context
    """
    return dedent(
        f"""
        Analyze {ticker} stock fundamentals, valuation metrics,
        and key business drivers within the {sector} sector
    """
    ).strip()


def macro_economic_rag_query() -> str:
    """Query for retrieving macroeconomic context and market drivers."""
    return dedent(
        """
        Current macroeconomic trends affecting equity markets: 
        inflation, interest rates, GDP growth, and monetary policy impacts
    """
    ).strip()


def risk_sentiment_rag_query() -> str:
    """Query for retrieving risk sentiment and volatility analysis."""
    return dedent(
        """
        Market risk sentiment indicators, VIX analysis, 
        and volatility regime impact on asset allocation
    """
    ).strip()


def earnings_season_rag_query(sector: str = "") -> str:
    """Query for retrieving earnings season and guidance context."""
    sector_filter = f" in the {sector} sector" if sector else ""
    return f"Earnings season trends, guidance revisions, and analyst expectations{sector_filter}"


def geopolitical_rag_query() -> str:
    """Query for retrieving geopolitical events affecting markets."""
    return dedent(
        """
        Current geopolitical events and tensions affecting 
        global markets, trade, and sector performance
    """
    ).strip()


def technical_analysis_rag_query(asset: str) -> str:
    """Query for retrieving technical analysis and chart patterns."""
    return f"Technical analysis patterns, support/resistance levels, and momentum indicators for {asset}"


def commodity_correlation_rag_query() -> str:
    """Query for retrieving commodity-equity correlations."""
    return dedent(
        """
        Commodity price movements and correlations with equity sectors,
        oil prices, gold, and currency impacts on stocks
    """
    ).strip()


def fed_policy_rag_query() -> str:
    """Query for retrieving Federal Reserve policy and rate impact analysis."""
    return dedent(
        """
        Federal Reserve policy decisions, interest rate changes,
        and monetary policy impact on different market sectors
    """
    ).strip()
