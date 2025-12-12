"""
Purpose: Guardrails for inputs and content.
Content: early, predictable failures; prevent oversized requests, PII,
or prompt-injection from JDs.
"""

from ..prompts.security.messages import (
    empty_input_error,
    input_too_long_error,
    prompt_injection_error,
    content_violation_error,
    INJECTION_CUES,
    BANNED_WORDS,
    MAX_INPUT_CHARS,
)
import re

EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")
CCARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


class DefaultSecurity:
    """
    Security validation and content filtering service.

    Provides input validation, PII detection, prompt injection
    prevention, and content moderation capabilities.
    """

    def validate_user_input(self, text: str) -> None:
        """
        Validate user input for basic security requirements.

        Parameters
        ----------
        text : str
            User input text to validate

        Raises
        ------
        ValueError
            If input is empty or exceeds maximum length
        """
        if not text.strip():
            raise ValueError(empty_input_error())
        if len(text) > MAX_INPUT_CHARS:
            raise ValueError(input_too_long_error())

    def sanitize_for_prompt(self, text: str) -> str:
        return (text or "").replace("\x00", "").strip()

    def redact_pii(self, text: str) -> tuple[str, list[str]]:
        """
        Detect and redact personally identifiable information.

        Identifies and replaces PII patterns including emails, phone numbers,
        credit card numbers, and social security numbers.

        Parameters
        ----------
        text : str
            Input text to scan for PII

        Returns
        -------
        tuple[str, list[str]]
            Redacted text and list of detected PII types
        """
        found = []

        def _redact(rx, label) -> None:
            nonlocal text, found
            if rx.search(text):
                found.append(label)
                text = rx.sub(f"[{label}]", text)

        _redact(EMAIL, "EMAIL")
        _redact(PHONE, "PHONE")
        _redact(CCARD, "CARD")
        _redact(SSN, "SSN")
        return text, found

    def check_prompt_injection(self, text: str) -> None:
        """
        Check for potential prompt injection attempts.

        Scans input for patterns that might indicate prompt injection
        or jailbreaking attempts.

        Parameters
        ----------
        text : str
            Input text to check for injection patterns

        Raises
        ------
        ValueError
            If prompt injection patterns are detected
        """
        t = (text or "").lower()
        if any(k in t for k in INJECTION_CUES):
            raise ValueError(prompt_injection_error())

    def moderate(self, text: str) -> None:
        """
        Moderate content for banned words and inappropriate content.

        Checks input against a list of banned words and content
        patterns that violate usage policies using whole-word matching.

        Parameters
        ----------
        text : str
            Input text to moderate

        Raises
        ------
        ValueError
            If banned content is detected
        """
        text = (text or "").lower()
        violations = {}

        for category, words in BANNED_WORDS.items():
            pattern = r"\b(?:" + "|".join(re.escape(word) for word in words) + r")\b"
            matches = re.findall(pattern, text)
            if matches:
                violations[category] = matches

        if violations:
            raise ValueError(content_violation_error(violations))
