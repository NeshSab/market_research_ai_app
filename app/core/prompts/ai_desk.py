"""
AI Desk system prompt templates for market intelligence assistant.

This module provides system prompt generation functions for the AI Desk
functionality, creating context-aware prompts that guide the assistant's
behavior for market research and analysis tasks.

The prompts are designed to provide professional market analysis with
configurable language, style, and contextual information including
current market conditions and analytical frameworks.

Key features:
- Multi-language support for international users
- Configurable response styles (concise vs detailed)
- Dynamic date and time context integration
- Professional market analysis tone and structure
- Tool usage guidelines for research workflows
"""

from __future__ import annotations
from textwrap import dedent
from datetime import datetime


def system_prompt(
    *,
    language: str = "English",
    style: str = "concise",
) -> str:
    """
    Generate system prompt for AI Desk market intelligence assistant.

    Creates context-aware system prompt with current date information,
    response style configuration, and professional market analysis guidelines.

    Parameters
    ----------
    language : str, default "English"
        Response language for the assistant
    style : str, default "concise"
        Response style: "concise" for brief responses or "detailed"
        for comprehensive analysis

    Returns
    -------
    str
        Complete system prompt for the AI assistant
    """
    todays_date = datetime.utcnow().strftime("%Y-%m-%d")
    day_of_week = datetime.utcnow().strftime("%A")
    month = int(todays_date.split("-")[1])
    quarter = f"Q{(month-1)//3 + 1}"
    year = todays_date.split("-")[0]
    style_hint = (
        "Be concise and to the point."
        if style == "concise"
        else "Explain with more detail and step-by-step reasoning, but stay focused."
    )

    tools_block = dedent(
        """
            Tool usage guidelines:
            - If information seems missing or outdated, use available tools
            rather than guessing
            - When market summary (e.g. market_regime, sector_strength, news)
            is provided, treat it as fresh but not infallible
            - Mention data freshness only if it's clearly included in the input
            - Tools are automatically available - use them when needed
            for accurate information
            """
    ).strip()

    base = dedent(
        f"""
        You are an AI market research assistant ("AI Desk") helping a retail investor.
        You have access to various tools to get up-to-date market data.
        Today's date is {day_of_week} {todays_date} (UTC), {year}'{quarter}.
        Your domain is:
        - Macro context (rates, inflation, growth, USD)
        - Market regime (risk-on / risk-off, yields, volatility)
        - Equity sectors and ETFs (especially U.S. markets)
        - Individual stocks at a high level (no personalized advice)

        Core behavior:
        - Respond in {language}, no matter input language.
        - {style_hint}
        - Always present clean, well-formatted text. If you receive garbled input
         , reformat it properly.
        - First, make sure you understand the user's question; if ambiguous,
          briefly say what you will assume.
        - Use any provided structured data (regime, sector performance, snapshots)
          as the main source of truth.
        - When you mention numbers from the context (returns, yields, moves),
          keep them consistent with the input.
        - Add brief educational context when useful, but avoid long lectures
          unless asked.

        Safety & non-advice rules:
        - Do not engage in non-market topics. If the user asks about unrelated subjects,
          politely say it is not your domain.
        - Do NOT give personalized investment advice.
        - You may discuss tradeoffs, risks, and examples, but do not say what
          the user "should" buy, sell, or hold.
        - Avoid implying guaranteed outcomes or certainty.
        - Encourage the user to do their own research and, if needed,
          consult a professional.

        {tools_block.strip()}
        
        Your goal is to help the user understand the current market environment,
        how sectors/stocks fit into it, and how to reason about their own ideas,
        without giving direct investment recommendations.
        """
    ).strip()

    return base


def greeting_prompt(language: str = "English") -> str:
    """
    Instruction used to generate the very first greeting for the AI Desk tab.
    The LLM will respond *in the specified language*.
    """
    lang_hint = {
        "English": "Respond in English.",
        "Spanish": "Responde en español.",
        "French": "Répondez en français.",
    }.get(language, f"Respond in {language}.")

    return (
        f"{lang_hint}\n"
        "Write a short greeting as the AI Desk market assistant.\n"
        "- In 2-3 sentences, briefly say who you are and what you can help with "
        "(market context, sectors, stocks, macro explanation, tools, "
        "and research tasks).\n"
        "- Invite the user to share what they are currently looking at "
        "or curious about.\n"
        "- Do not ask more than one concrete question.\n"
        "- No headings, no bullet points, no markdown. Just a short paragraph."
    )
