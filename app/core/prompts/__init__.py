"""Centralized prompt factory with organized module structure."""

from __future__ import annotations
from ..models import (
    RespondStyle,
    RespondLanguage,
)
from . import ai_desk, market_analysis, ticker_analysis, rag_queries
from .tools import query_variants, final_response
from .security import messages


class DefaultPromptFactory:
    """
    Centralized prompt factory for all AI operations.
    Organizes prompts by domain: ai_desk, market_analysis, tools, security.
    """

    def build_system(
        self,
        *,
        language: RespondLanguage,
        style: RespondStyle,
    ) -> str:
        return ai_desk.system_prompt(
            language=language.value,
            style=style.value,
        )

    def greeting_instruction(
        self,
        language: RespondLanguage,
    ) -> str:
        return ai_desk.greeting_prompt(language=language.value)

    def market_pulse_system(self) -> str:
        return market_analysis.system_prompt()

    def market_pulse_user(self, **kwargs) -> str:
        return market_analysis.user_prompt(**kwargs)

    def query_variants_system(self) -> str:
        return query_variants.system_prompt()

    def query_variants_user(self, query: str, n_variants: int = 4) -> str:
        return query_variants.user_prompt(query, n_variants)

    def final_response_system(self) -> str:
        return final_response.system_prompt()

    def final_response_user(self, question: str, context: str) -> str:
        return final_response.user_prompt(question, context)

    def ticker_analysis_system(self) -> str:
        return ticker_analysis.system_prompt()

    def ticker_analysis_user(self, **kwargs) -> str:
        return ticker_analysis.user_prompt(**kwargs)

    def market_pulse_rag_query(self) -> str:
        return rag_queries.market_pulse_rag_query()

    def sector_analysis_rag_query(self, sector: str) -> str:
        return rag_queries.sector_analysis_rag_query(sector)

    def ticker_fundamentals_rag_query(self, ticker: str, sector: str) -> str:
        return rag_queries.ticker_fundamentals_rag_query(ticker, sector)

    def macro_economic_rag_query(self) -> str:
        return rag_queries.macro_economic_rag_query()

    def empty_input_error(self) -> str:
        return messages.empty_input_error()

    def input_too_long_error(self) -> str:
        return messages.input_too_long_error()

    def prompt_injection_error(self) -> str:
        return messages.prompt_injection_error()

    def content_violation_error(self, violations: dict) -> str:
        return messages.content_violation_error(violations)
