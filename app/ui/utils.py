"""
Utility functions for the UI components.
"""

import glob
import os

from .state import ui_session_state
from core.models import LLMSettings, RespondLanguage, RespondStyle


def make_llm_settings(
    model: str, temperature: float, top_p: float, max_tokens: int = 512
) -> LLMSettings:
    """
    Create LLMSettings object from UI parameters.

    Parameters
    ----------
    model : str
        LLM model identifier
    temperature : float
        Sampling temperature for response generation
    top_p : float
        Top-p sampling parameter
    max_tokens : int, default 512
        Maximum tokens in response

    Returns
    -------
    LLMSettings
        Configured LLM settings object
    """
    return LLMSettings(
        model=model,
        temperature=float(temperature),
        top_p=float(top_p),
        max_tokens=max_tokens,
    )


def clear_chat_ui() -> None:
    ui_state = ui_session_state()
    ui_state.messages = []
    ctrl = ui_state.controller
    if ctrl and hasattr(ctrl, "clear_history"):
        try:
            ctrl.clear_history()
        except Exception:
            pass


def extract_last_qa(history) -> tuple[str, str]:
    last_user, prev_assistant = "", ""
    for i in range(len(history) - 1, -1, -1):
        m = history[i]
        if hasattr(m, "type"):
            role = "user" if m.type == "human" else "assistant"
            content = m.content or ""
        else:
            role = m.get("role", "")
            content = m.get("content", "")

        if role == "user":
            last_user = content.strip()
            for j in range(i - 1, -1, -1):
                msg = history[j]
                if hasattr(msg, "type"):
                    msg_role = "assistant" if msg.type == "ai" else "user"
                    msg_content = msg.content or ""
                else:
                    msg_role = msg.get("role", "")
                    msg_content = msg.get("content", "")

                if msg_role == "assistant":
                    prev_assistant = msg_content.strip()
                    break
            break
    return prev_assistant, last_user


def format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"


def start_chating(ctrl, ui_state) -> None:
    """If not started yet, greet the user and ask the first question."""

    history = ctrl.get_history()
    if not history:

        ctrl.greet_and_open(
            settings=make_llm_settings(
                model=ui_state.model,
                temperature=ui_state.temperature,
                top_p=ui_state.top_p,
                max_tokens=160,
            ),
            language=RespondLanguage(ui_state.language),
            style=RespondStyle(ui_state.style),
        )


def get_knowledge_base_files(base_patterns: list[str]) -> list[str]:
    """Get relevant markdown files for RAG indexing."""
    files = []
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for pattern in base_patterns:
        if not os.path.isabs(pattern):
            abs_pattern = os.path.join(app_dir, pattern)
        else:
            abs_pattern = pattern
            
        files.extend(glob.glob(abs_pattern))

    return [f for f in files if os.path.exists(f)]
