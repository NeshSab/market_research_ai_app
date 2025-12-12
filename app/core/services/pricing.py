"""
Purpose: Token math & cost estimation.
Central pricing logic so UI/controller do not duplicate calculations.
"""

import tiktoken
from ..models import Price


PRICE_TABLE = {
    "gpt-4o": Price(input_per_1M=2.50, output_per_1M=10.00),
    "gpt-4.1-mini": Price(input_per_1M=0.40, output_per_1M=1.60),
    "gpt-4o-mini": Price(input_per_1M=0.15, output_per_1M=0.60),
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """
    Calculate estimated cost for LLM API usage.

    Parameters
    ----------
    model : str
        LLM model name for pricing lookup
    tokens_in : int
        Number of input tokens used
    tokens_out : int
        Number of output tokens generated

    Returns
    -------
    float
        Estimated cost in USD for the token usage
    """
    p = PRICE_TABLE.get(model, Price(input_per_1M=0.0, output_per_1M=0.0))
    return (tokens_in / 1000000) * p.input_per_1M + (
        tokens_out / 1000000
    ) * p.output_per_1M


def estimate_tokens_from_text(text: str) -> int:
    """
    Estimate token count using fast character-based heuristic.

    Uses approximation of ~4 characters per token for quick estimates
    without requiring tiktoken encoding.

    Parameters
    ----------
    text : str
        Text content to estimate token count for

    Returns
    -------
    int
        Estimated number of tokens
    """
    t = (text or "").strip()
    if not t:
        return 0

    return (len(t) + 3) // 4


def estimate_tokens(text: str, model: str) -> int:
    """
    Estimate token count using tiktoken with fallback to heuristic.

    Attempts to use tiktoken for accurate model-specific encoding,
    falls back to character-based estimation if unavailable.

    Parameters
    ----------
    text : str
        Text content to tokenize
    model : str
        LLM model name for tiktoken encoding

    Returns
    -------
    int
        Accurate or estimated token count
    """
    if tiktoken:
        try:
            enc = tiktoken.encoding_for_model(model)
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    return max(1, len(text) // 4)


def estimate_messages_tokens(messages: list[dict[str, str]], model: str) -> int:
    """
    Estimate total token count for a list of chat messages.

    Parameters
    ----------
    messages : list[dict[str, str]]
        List of message dictionaries with 'content' keys
    model : str
        LLM model name for tiktoken encoding

    Returns
    -------
    int
        Total estimated token count for all messages
    """
    return sum(estimate_tokens(m.get("content", ""), model) for m in messages)
