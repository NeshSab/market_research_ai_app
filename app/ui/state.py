"""
UI session state management using Pydantic.
Consolidated configuration constants from core/config.py.
"""

from datetime import datetime
import streamlit as st
import logging
from typing import Any, Optional
from core.controller import MarketIntelligenceSessionController
import os
from pydantic import BaseModel, Field


class Session(BaseModel):
    """Session state using Pydantic for consistency."""

    controller: Optional[Any] = None
    api_key: str = ""
    fred_key: str = ""
    langsmith_key: str = ""
    langsmith_project: str = ""
    api_key_set: bool = False

    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024

    language: str = "English"
    style: str = "Concise"

    tokens_in: int = 0
    tokens_out: int = 0

    period: str = "3mo"
    cache_ttl: int = 30

    last_market_pulse: Optional[Any] = None
    last_pulse_period: str = "3mo"
    last_pulse_chart_data: Optional[Any] = None
    last_sector_data: Optional[Any] = None
    show_ticker_dive: bool = False
    ticker_analyses: list = Field(default_factory=list)
    last_tools_used: list = Field(default_factory=list)

    langsmith_enabled: str = "false"

    ops_per_min: int = 30

    session_start_ts: float = Field(default_factory=lambda: datetime.now().timestamp())
    messages: list = Field(default_factory=list)
    greeting_in_progress: bool = False

    user_understanding: bool = False
    enable_web_search: bool = False
    file_uploader_key: int = 0
    web_uploader_key: int = 0

    market_analysis_config: dict = {
        "default_period": {
            "period": "1wk",
            "full_name": "one week",
            "alternative_name": "5 trading days",
            "description": "Standard analysis window for market regime detection",
        },
        "core_indicators": {
            "indicators": ["^GSPC", "^VIX", "DX-Y.NYB", "GC=F"],
            "chart_name": "US Dollar Index vs S&P500 vs Gold vs Volatility",
        },
    }

    class Config:
        arbitrary_types_allowed = True


def init_state() -> None:
    """Initialize session state on first run."""
    if "ui_session_state" not in st.session_state:
        st.session_state.ui_session_state = Session()
        logging.info("Initialized new UI session state.")


def init_controller() -> "MarketIntelligenceSessionController":
    """
    Initialize the controller after API key is set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        ui_state = ui_session_state()
        api_key = ui_state.api_key
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            raise ValueError("OPENAI_API_KEY not set")

    ui_state = ui_session_state()

    controller = MarketIntelligenceSessionController(ops_per_min=ui_state.ops_per_min)
    ui_state.controller = controller

    logging.info("Initialized new controller.")
    return controller


def ui_session_state() -> Session:
    """
    Return the UI session state object.
    """
    if "ui_session_state" not in st.session_state:
        init_state()
    return st.session_state.ui_session_state
