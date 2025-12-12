"""
Core data models for market intelligence application.

This module defines Pydantic models for data validation and serialization
across the application. Models provide type safety and automatic validation
for market data, LLM settings, analysis results, and UI state management.

Key model categories:
- Market analysis results (MarketPulse, TickerAnalysis, SectorPick)
- LLM configuration and settings (LLMSettings, RespondLanguage, RespondStyle)
- Session state management (SessionState)
- API response structures for consistent data interchange

All models use Pydantic BaseModel for automatic validation, serialization,
and documentation generation.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any


class SectorPick(BaseModel):
    """
    Sector performance analysis result.

    Represents a single sector's performance metrics with supporting
    evidence and reasoning from market analysis.
    """

    sector: str
    tickers: list[str]
    change_pct: float
    reasoning: str


class MarketPulse(BaseModel):
    """
    Comprehensive market analysis snapshot.

    Contains market regime classification, top performing sectors,
    and overall market summary with supporting citations from
    knowledge base sources.
    """

    as_of: str
    detected_regime: str
    sectors: list[SectorPick]
    global_summary: str
    citations: list[str]


class TickerAnalysis(BaseModel):
    """Ticker deep dive analysis result."""

    ticker: str
    company_name: str
    sector: str
    analysis: str
    ticker_return: float
    spx_return: float
    sector_return: float
    outperformance_vs_spx: float = 0.0
    outperformance_vs_sector: float = 0.0
    comparison_data: Optional[Any] = None
    fundamentals: dict = Field(default_factory=dict)
    citations: list[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class SessionState(BaseModel):
    model_usage: dict[str, dict[str, int]] = Field(default_factory=dict)
    total_cost: float = 0.0

    last_market_summary: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class LLMSettings(BaseModel):
    model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=0.9)
    max_tokens: int = Field(default=1024)
    frequency_penalty: float = Field(default=0.0)
    presence_penalty: float = Field(default=0.0)
    response_format: dict | None = Field(default=None)

    @field_validator("temperature", "top_p", "frequency_penalty", "presence_penalty")
    @classmethod
    def _clamp_01(cls, v: float) -> float:
        if v is None:
            return 0.0
        return max(0.0, min(1.0, float(v)))

    @field_validator("max_tokens")
    @classmethod
    def _cap_max_tokens(cls, v: int) -> int:
        v = int(v)
        return min(v, 1024)

    def as_kwargs(self) -> dict:
        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "logprobs": False,
            "top_logprobs": None,
        }
        if self.response_format:
            kwargs["response_format"] = self.response_format
        return kwargs


class Price(BaseModel):
    input_per_1M: float
    output_per_1M: float

    class Config:
        frozen = True


class RespondStyle(str, Enum):
    CONCISE = "Concise"
    DETAILED = "Detailed"


class RespondLanguage(str, Enum):
    ENGLISH = "English"
    SPANISH = "Spanish"
    FRENCH = "French"
    GERMAN = "German"
