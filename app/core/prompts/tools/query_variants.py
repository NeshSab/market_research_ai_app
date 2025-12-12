"""Prompts for generating diverse query variants for better search recall."""

from textwrap import dedent


def system_prompt() -> str:
    """System prompt for query variant generation."""
    return "You are a helpful search assistant."


def user_prompt(query: str, n_variants: int = 4) -> str:
    """Generate diverse query variants for improved search recall."""
    return dedent(
        f"""
        Rewrite the user's query into {n_variants} diverse search queries
        covering different phrasings, synonyms, and angles.
        Return each on a new line without numbering.

        User query: {query}
    """
    ).strip()
