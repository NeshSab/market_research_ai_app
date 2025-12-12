"""Centralized security validation messages and error responses."""


def empty_input_error() -> str:
    """Error message for empty input validation."""
    return "Please enter a non-empty message."


def input_too_long_error() -> str:
    """Error message for input length validation."""
    return "Re-type your answer.\nYour message is too long."


def prompt_injection_error() -> str:
    """Error message for suspected prompt injection."""
    return "Re-type your answer.\n" "Suspected prompt-injection phrasing in the input."


def content_violation_error(violations: dict) -> str:
    """Error message for content policy violations."""
    return f"Re-type your answer.\n" f"Content violates usage guidelines: {violations}"


INJECTION_CUES = [
    "ignore previous",
    "disregard previous",
    "system prompt",
    "as the assistant",
    "you must not follow",
    "new instructions:",
    "### system",
    "BEGIN SYSTEM",
]

BANNED_WORDS = {
    "profanity": ["fuck", "shit", "bitch"],
    "discriminatory": ["racist", "sexist"],
    "harmful": ["suicide", "self-harm"],
}

MAX_INPUT_CHARS = 10000
