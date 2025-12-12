"""
Final response generation prompt templates for tool-assisted analysis.

This module provides prompt templates for generating comprehensive final
responses that synthesize information from multiple tool executions and
data sources. The prompts ensure consistency, accuracy, and transparency
in AI-generated market analysis reports.

Key features:
- Tool result synthesis prompts
- Context integration templates
- Accuracy and transparency guidelines
- Source attribution requirements
- Comprehensive response formatting
"""

from textwrap import dedent


def system_prompt() -> str:
    """
    Generate system prompt for final response synthesis.

    Creates system prompt that guides the AI to synthesize tool results
    into comprehensive, accurate responses with proper source attribution.

    Returns
    -------
    str
        System prompt for final response generation
    """
    return dedent(
        """
        You are a helpful financial analysis AI assistant. Use the
        provided context to answer the user's question comprehensively.
        Add add sources and hyperlinks, as well as dates 
        where relevant for clarity and transparency.
        If the context contains errors or limitations, acknowledge them.
        Focus on being helpful while maintaining accuracy.
    """
    ).strip()


def user_prompt(question: str, context: str) -> str:
    """
    Generate user prompt for final response with tool execution context.

    Parameters
    ----------
    question : str
        Original user question or request
    context : str
        Aggregated context from tool execution results

    Returns
    -------
    str
        Formatted user prompt with question and context
    """
    return dedent(
        f"""
        Question: {question}

        Available Context:
        {context}

        Please provide a comprehensive response based on the available context.
    """
    ).strip()
