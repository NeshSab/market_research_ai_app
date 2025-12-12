"""
Service interfaces and protocols for dependency inversion.

This module defines abstract interfaces (protocols) for core services,
enabling loose coupling, testability, and pluggable implementations.
The controller depends on these interfaces rather than concrete implementations,
following the dependency inversion principle.

Key interfaces:
- LLMClientInt: Language model client for chat and structured outputs
- PromptFactory: Dynamic prompt generation with context
- SecurityGuard: Input validation and content filtering

This design enables:
- Easy testing with mock implementations
- Future service provider swapping (e.g., different LLM providers)
- Clear separation of concerns between layers
- Type safety through protocol definitions
"""

from __future__ import annotations
from typing import Optional, Protocol, Union, Type, Any, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from .models import (
        LLMSettings,
        RespondLanguage,
        RespondStyle,
        MarketPulse,
        TickerAnalysis,
    )


class LLMClientInt(Protocol):
    """Protocol defining the interface for LLM client implementations."""

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        settings: Union["LLMSettings", str, None] = None,
    ) -> tuple[str, dict[str, Any]]: ...

    def chat_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Type[BaseModel],
        settings: Union["LLMSettings", str, None] = None,
    ) -> tuple[BaseModel, dict[str, Any]]: ...

    def chat_with_history(
        self,
        system_prompt: str,
        user_input: str,
        session_id: str,
        settings: Union["LLMSettings", str, None] = None,
    ) -> tuple[str, dict[str, Any]]: ...

    def chat_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        settings: "LLMSettings",
        tool_map: dict,
    ) -> tuple[str, dict]: ...

    def chat_with_tools_and_history(
        self,
        system_prompt: str,
        user_input: str,
        session_id: str,
        settings: "LLMSettings",
        tool_map: dict,
    ) -> tuple[str, dict]: ...

    def get_session_history_messages(self, session_id: str) -> list: ...
    def clear_session_history(self, session_id: str) -> None: ...
    def add_user_message_to_session(self, session_id: str, message: str) -> None: ...
    def add_ai_message_to_session(self, session_id: str, message: str) -> None: ...


class PromptFactory(Protocol):
    """Protocol for centralized prompt management across all AI operations."""

    def build_system(
        self,
        *,
        language: str,
        style: str,
        market_analysis_summary: Optional[str] = None,
        web_search_enabled: bool = False,
    ) -> str: ...
    def greeting_instruction(self, language: str) -> str: ...

    def market_pulse_system(self) -> str: ...
    def market_pulse_user(self, **kwargs) -> str: ...

    def ticker_analysis_system(self) -> str: ...
    def ticker_analysis_user(self, **kwargs) -> str: ...

    def query_variants_system(self) -> str: ...
    def query_variants_user(self, query: str, n_variants: int = 4) -> str: ...
    def final_response_system(self) -> str: ...
    def final_response_user(self, question: str, context: str) -> str: ...

    def market_pulse_rag_query(self) -> str: ...
    def sector_analysis_rag_query(self, sector: str) -> str: ...
    def ticker_fundamentals_rag_query(self, ticker: str, sector: str) -> str: ...
    def macro_economic_rag_query(self) -> str: ...

    def empty_input_error(self) -> str: ...
    def input_too_long_error(self) -> str: ...
    def prompt_injection_error(self) -> str: ...
    def content_violation_error(self, violations: dict) -> str: ...


class SecurityGuard(Protocol):
    def validate_user_input(self, text: str) -> None: ...

    def sanitize_for_prompt(self, text: str) -> str: ...

    def redact_pii(self, text: str) -> tuple[str, list[str]]: ...

    def check_prompt_injection(self, text: str) -> None: ...

    def moderate(self, text: str) -> None: ...


class MarketIntelligenceController(Protocol):
    """Protocol defining the interface for the market intelligence session controller."""

    def get_history(self) -> list: ...
    def clear_history(self) -> None: ...
    def is_ready(self) -> bool: ...

    def ai_desk_chat(
        self,
        *,
        settings: "LLMSettings",
        language: "RespondLanguage",
        style: "RespondStyle",
        user_text: Optional[str] = None,
        use_web_search: bool = False,
    ) -> str: ...

    def greet_and_open(
        self,
        settings: "LLMSettings",
        language: "RespondLanguage",
        style: "RespondStyle",
    ) -> str: ...

    def run_market_pulse(
        self,
        index_path: str,
        period: str = "1mo",
    ) -> "MarketPulse": ...

    def run_ticker_deep_dive(
        self,
        ticker: str,
        period: str = "3mo",
    ) -> "TickerAnalysis": ...
