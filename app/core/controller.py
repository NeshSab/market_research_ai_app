"""
Market Intelligence Session Controller.

This module provides the primary orchestration point for market intelligence
sessions. The controller coordinates between LLM interactions, market data
services, and user interface components while maintaining session state and
applying security guardrails.

Key features:
- Session state management with token usage tracking
- LLM conversation history management via LangChain
- Market data analysis integration (regime, sectors, tickers)
- Security validation and content filtering
- RAG-based market insights with knowledge base retrieval
- Cost tracking and usage monitoring

The controller serves as the single entry point for all AI interactions,
preventing direct coupling between UI components and internal services.
"""

from __future__ import annotations
from typing import Optional
import logging

from .models import (
    SessionState,
    LLMSettings,
    MarketPulse,
    TickerAnalysis,
    RespondLanguage,
    RespondStyle,
)
from .prompts import DefaultPromptFactory
from .services.llm_openai import LLMClient
from .interfaces import SecurityGuard, PromptFactory, LLMClientInt
from .services.security import DefaultSecurity
from .services.rate_limit import RateLimiter

from .services.pricing import estimate_cost
from core.tools.registry import get_functions_for_openai

from .services.market_data import (
    get_sector_perf,
    get_ticker_samples,
    get_market_snapshot,
    get_ticker_fundamentals,
    get_ticker_info,
)
from .services.retrievers import retrieve_semantic
from .analyzers.regime import load_regime_config, classify_regime


class MarketIntelligenceSessionController:
    """
    Primary session controller for market intelligence operations.

    Coordinates LLM interactions, market data analysis, and session state
    management. Provides high-level interface for AI-powered market analysis
    while abstracting away internal service implementations.
    """

    def __init__(
        self,
        ops_per_min: int,
        session_id: str = "default_session",
    ):
        """
        Initialize market intelligence session controller.

        Parameters
        ----------
        ops_per_min : int
            Maximum operations per minute for rate limiting
        session_id : str, optional
            Unique session identifier, by default "default_session"
        """
        self.session_id = session_id
        self.prompts: PromptFactory = DefaultPromptFactory()
        self.rate_limiter = RateLimiter(max_ops_per_min=ops_per_min)
        self.llm_client: LLMClientInt = LLMClient(
            prompts=self.prompts, rate_limiter=self.rate_limiter
        )
        self.security: SecurityGuard = DefaultSecurity()
        self.state = SessionState()

    def is_ready(self) -> bool:
        """
        Check if controller is ready for operations.

        Returns
        -------
        bool
            True if the controller has an initialized LLM client
        """
        return self.llm_client is not None

    def get_history(self) -> list:
        """
        Get conversation history for current session.

        Returns
        -------
        list
            List of LangChain message objects from session history
        """
        return self.llm_client.get_session_history_messages(self.session_id)

    def append_user(self, text: str) -> None:
        """
        Add user message to conversation history.

        Parameters
        ----------
        text : str
            User message content
        message_type : str, optional
            Type of message, by default "chat"
        """
        self.llm_client.add_user_message_to_session(self.session_id, text)

    def append_assistant(self, text: str) -> None:
        """
        Add assistant message to conversation history.

        Parameters
        ----------
        text : str
            Assistant message content
        message_type : str, optional
            Type of message, by default "chat"
        """
        self.llm_client.add_ai_message_to_session(self.session_id, text)

    def clear_history(self) -> None:
        """
        Clear all conversation history for current session.

        Removes all messages from LangChain conversation memory.
        """
        self.llm_client.clear_session_history(self.session_id)

    def _track_usage(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """
        Track token usage per model and calculate incremental cost.

        Returns:
            Cost of this specific call
        """
        if model not in self.state.model_usage:
            self.state.model_usage[model] = {"tokens_in": 0, "tokens_out": 0}

        self.state.model_usage[model]["tokens_in"] += tokens_in
        self.state.model_usage[model]["tokens_out"] += tokens_out

        cost = estimate_cost(model, tokens_in, tokens_out)
        self.state.total_cost += cost

        return cost

    def get_usage_summary(self) -> dict:
        """Get a summary of all usage and costs."""
        return {
            "total_tokens_in": self.tokens_in,
            "total_tokens_out": self.tokens_out,
            "total_cost": self.state.total_cost,
            "models": self.state.model_usage.copy(),
            "breakdown": [
                {
                    "model": model,
                    "tokens_in": usage["tokens_in"],
                    "tokens_out": usage["tokens_out"],
                    "cost": estimate_cost(
                        model, usage["tokens_in"], usage["tokens_out"]
                    ),
                }
                for model, usage in self.state.model_usage.items()
            ],
        }

    @property
    def tokens_in(self) -> int:
        """Total input tokens across all models."""
        return sum(usage["tokens_in"] for usage in self.state.model_usage.values())

    @property
    def tokens_out(self) -> int:
        """Total output tokens across all models."""
        return sum(usage["tokens_out"] for usage in self.state.model_usage.values())

    @property
    def model_used(self) -> Optional[str]:
        """Most recently used model (for compatibility)."""
        if not self.state.model_usage:
            return None
        return list(self.state.model_usage.keys())[-1]

    def reset(self) -> None:
        """Clear LangChain history and reset state."""
        self.clear_history()
        self.state = SessionState()

    def ai_desk_chat(
        self,
        *,
        settings: LLMSettings,
        language: RespondLanguage,
        style: RespondStyle,
        user_text: Optional[str] = None,
        use_web_search: bool = False,
    ) -> str:
        """
        Handles a normal back-and-forth chat turn with LangChain history management.
        Now with automatic conversation history and tool calling support.
        """
        user_query = user_text or ""
        self.security.validate_user_input(user_query)
        self.security.moderate(user_query)
        user_query = self.security.sanitize_for_prompt(user_query)
        user_query, pii = self.security.redact_pii(user_query)
        self.security.check_prompt_injection(user_query)

        system_prompt = self.prompts.build_system(
            language=language,
            style=style,
        )

        tool_map = get_functions_for_openai(enable_web_search=use_web_search)

        reply, meta = self.llm_client.chat_with_tools_and_history(
            system_prompt=system_prompt,
            user_input=user_query,
            session_id=self.session_id,
            settings=settings,
            tool_map=tool_map,
        )

        self._track_usage(
            model=meta["model"],
            tokens_in=meta["tokens_in"],
            tokens_out=meta["tokens_out"],
        )

        tools_used = meta.get("tools_used", [])
        if tools_used:
            logging.info(f"Tools used in this turn: {tools_used}")
        return reply, meta

    def greet_and_open(
        self,
        *,
        settings: LLMSettings,
        language: RespondLanguage,
        style: RespondStyle,
    ) -> str:
        """
        One assistant turn: brief greeting + invite the user
        to ask stocks related questions.
        """
        system_prompt = self.prompts.build_system(
            language=language,
            style=style,
        )
        greet_instr = self.prompts.greeting_instruction(
            language=language,
        )

        reply, meta = self.llm_client.chat(
            system_prompt=system_prompt, user_prompt=greet_instr, settings=settings
        )
        self.llm_client.add_ai_message_to_session(self.session_id, reply)

        _ = self._track_usage(
            model=meta["model"],
            tokens_in=meta["tokens_in"],
            tokens_out=meta["tokens_out"],
        )
        return reply

    def run_market_pulse(
        self,
        index_path: str,
        period: str,
    ) -> MarketPulse:
        """
        Generate a market pulse analysis using current market data and RAG context.

        Analysis approach:
        - Sector performance: Uses specified period for charts/rankings
        - Market regime: Uses specified period for consistent analysis
        - RAG context: Retrieves relevant market analysis from knowledge base

        Args:
            index_path: Path to FAISS index for RAG retrieval
            period: Time period for analysis (e.g., "1wk", "1mo", "3mo", "6mo", "1y")

        Returns:
            MarketPulse object with regime, sectors, and narrative
        """
        sectors_df = get_sector_perf(period=period)
        snapshot = get_market_snapshot(period=period)
        cfg = load_regime_config()

        deltas = snapshot["deltas"]
        regime = classify_regime(
            spx_pct=deltas["spx_pct"],
            vix_pct=deltas["vix_pct"],
            dxy_pct=deltas["dxy_pct"],
            ust10y_bp=deltas["ust10y_bp"],
            cfg=cfg,
        )
        query = self.prompts.market_pulse_rag_query()
        docs = retrieve_semantic(index_path, query, k=4)
        doc_snips = [
            {
                "text": d.page_content[:800],
                "source": d.metadata.get("source", "kb"),
                "chunk": d.metadata.get("chunk", ""),
            }
            for d in docs
        ]

        samples = get_ticker_samples()
        top_sectors = sectors_df.head(3).to_dict(orient="records")
        sectors_text = "\\n".join(
            [
                (
                    "- "
                    + sector["sector"]
                    + ": "
                    + f"{float(sector['return']):.1%}"
                    + " change, "
                    + "tickers: "
                    + ", ".join(samples.get(sector["sector"], []))
                )
                for sector in top_sectors
            ]
        )

        docs_text = "\n\n".join(
            ["Source: " + d["source"] + "\n" + d["text"] for d in doc_snips]
        )
        if isinstance(regime, dict):
            regime_text = regime.get("regime", "Unknown")
        else:
            regime_text = str(regime)

        system = self.prompts.market_pulse_system()
        user_prompt = self.prompts.market_pulse_user(
            regime_text=regime_text, sectors_text=sectors_text, docs_text=docs_text
        )

        result, meta = self.llm_client.chat_structured(
            system_prompt=system,
            user_prompt=user_prompt,
            schema=MarketPulse,
        )

        _ = self._track_usage(
            model=meta["model"],
            tokens_in=meta["tokens_in"],
            tokens_out=meta["tokens_out"],
        )

        analysis_text = f"Regime: {result.detected_regime}. Top sectors: " + ", ".join(
            [s["sector"] for s in top_sectors]
        )
        self.state.last_market_summary = analysis_text

        citations = []
        for d in doc_snips:
            source_path = d["source"].replace("knowledge_base/playbooks/", "")
            chunk_info = f" (chunk {d['chunk']})" if d.get("chunk") != "" else ""
            citations.append(f"{source_path}{chunk_info}")

        result.citations = sorted(set(citations))

        return result

    def run_ticker_deep_dive(
        self,
        index_path: str,
        ticker: str,
        period: str,
    ) -> "TickerAnalysis":
        """
        Generate deep dive analysis for a specific ticker.

        Analysis approach:
        - Ticker performance: Always uses 1-week (5 trading days) for consistency
        - Chart period: User-selected period for broader visualization context
        - RAG context: Retrieves relevant sector and market analysis from knowledge base
        """
        try:
            ticker_data = get_ticker_info(ticker, period)
            fundamentals = get_ticker_fundamentals(ticker)
        except ValueError as e:
            logging.error(f"Error retrieving data for ticker {ticker}: {e}")
            error_msg = str(e)
            if "No data available" in error_msg or "No price data" in error_msg:
                error_msg = (
                    f"Ticker '{ticker}' not found or has no price data available."
                )
            elif "Invalid ticker" in error_msg.lower():
                error_msg = f"'{ticker}' is not a valid ticker symbol."

            return TickerAnalysis(
                ticker=ticker,
                company_name=ticker,
                sector="Unknown",
                analysis=f"Error: {error_msg}",
                ticker_return=0.0,
                spx_return=0.0,
                sector_return=0.0,
                comparison_data=None,
                fundamentals={},
                citations=[],
            )

        sector = ticker_data["sector"]
        query = self.prompts.sector_analysis_rag_query(sector)
        docs = retrieve_semantic(index_path, query, k=3)
        doc_snips = [
            {
                "text": d.page_content[:600],
                "source": d.metadata.get("source", "kb"),
                "chunk": d.metadata.get("chunk", ""),
            }
            for d in docs
        ]

        if self.state.last_market_summary:
            market_context = self.state.last_market_summary
        else:
            market_context = "Market regime unknown - run Market Pulse first"

        docs_text = "\n\n".join(
            ["Source: " + d["source"] + "\n" + d["text"] for d in doc_snips]
        )

        if isinstance(fundamentals, dict):
            fundamentals_text = "\n".join(
                ["- " + key + ": " + str(value) for key, value in fundamentals.items()]
            )
        else:
            fundamentals_text = str(fundamentals)

        system = self.prompts.ticker_analysis_system()
        user_prompt = self.prompts.ticker_analysis_user(
            ticker=ticker,
            company_name=ticker_data["company_name"],
            sector=sector,
            period="1 week (5 trading days) analysis.",
            ticker_return=ticker_data["ticker_return"],
            sector_return=ticker_data["sector_return"],
            spx_return=ticker_data["spx_return"],
            outperformance_vs_spx=ticker_data["outperformance_vs_spx"],
            outperformance_vs_sector=ticker_data["outperformance_vs_sector"],
            market_context=market_context,
            fundamentals_text=fundamentals_text,
            docs_text=docs_text,
        )
        text, meta = self.llm_client.chat(
            system_prompt=system,
            user_prompt=user_prompt,
        )

        _ = self._track_usage(
            model=meta["model"],
            tokens_in=meta["tokens_in"],
            tokens_out=meta["tokens_out"],
        )
        citations = []
        for d in doc_snips:
            source_path = d["source"].replace("knowledge_base/playbooks/", "")
            chunk_info = f" (chunk {d['chunk']})" if d.get("chunk") != "" else ""
            citations.append(f"{source_path}{chunk_info}")

        return TickerAnalysis(
            ticker=ticker,
            company_name=ticker_data["company_name"],
            sector=sector,
            analysis=text,
            ticker_return=ticker_data["ticker_return"],
            spx_return=ticker_data["spx_return"],
            sector_return=ticker_data["sector_return"],
            outperformance_vs_spx=ticker_data["outperformance_vs_spx"],
            outperformance_vs_sector=ticker_data["outperformance_vs_sector"],
            comparison_data=ticker_data["comparison_data"],
            fundamentals=fundamentals,
            citations=sorted(set(citations)),
        )
