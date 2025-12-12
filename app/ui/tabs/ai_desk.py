"""
AI Desk tab interface for interactive market intelligence conversations.

This module provides the main conversational interface for the market
intelligence assistant, handling user interactions, message formatting,
and chat flow management. It integrates with the underlying LLM services
and tools to provide comprehensive market analysis capabilities.

Key features:
- Interactive chat interface with conversation history
- LLM response formatting and tool usage display
- API key validation and session state management
- Real-time market intelligence conversations
- Professional message formatting and display
"""

import streamlit as st
import re

from ui.state import ui_session_state
from ui.utils import make_llm_settings, start_chating
from core.models import RespondLanguage, RespondStyle


def format_llm_response(response: str, tools_used: list) -> str:
    """
    Format LLM response text for display in the chat interface.

    Applies text formatting, escapes special characters, and adds
    tool usage information to the response.

    Parameters
    ----------
    response : str
        Raw LLM response text
    tools_used : list
        List of tools used during response generation

    Returns
    -------
    str
        Formatted response text ready for display
    """
    response = response.replace("$", "\\$")
    response = re.sub(r"\*\*([^*]+)\*\*", r"**\1**", response)
    response = re.sub(r"  +", " ", response)

    if tools_used:
        tools_str = ", ".join(tools_used)
        response += f"\n\n---\n**Tools used:** {tools_str}"

    return response


def render(index_path: str) -> None:
    ui_state = ui_session_state()
    if not ui_state.api_key_set:
        st.info("Please initialize API keys in the sidebar first.")
        return

    st.header("🤖 AI Desk")
    st.caption(
        "Your AI-powered market intelligence assistant. Ask questions about "
        + "market trends, sectors, and companies."
    )

    ctrl = ui_state.controller
    if ctrl is None:
        st.warning("Please initialize the session in the sidebar.")
        return

    if not ctrl.get_history() and not ui_state.greeting_in_progress:
        ui_state.greeting_in_progress = True
        start_chating(ctrl, ui_state)
        ui_state.greeting_in_progress = False
        st.rerun()

    ctrl = ui_state.controller
    transcript = st.container(height=500, border=True)
    with transcript:
        history = (
            ctrl.get_history()
            if (ctrl and hasattr(ctrl, "get_history"))
            else ui_state.messages
        )
        for m in history or []:
            if hasattr(m, "type"):
                role = "user" if m.type == "human" else "assistant"
                content = m.content
            else:
                role = m.get("role", "assistant")
                content = m.get("content", "")

            with st.chat_message(role):
                if role == "assistant":
                    tools_used = ui_state.last_tools_used
                    cleaned_response = format_llm_response(content, tools_used)
                    st.markdown(cleaned_response)
                else:
                    st.markdown(content)

    user_text = st.chat_input("Type your query…")
    if user_text and user_text.strip():
        with st.spinner("Thinking..."):
            try:
                reply, meta = ctrl.ai_desk_chat(
                    settings=make_llm_settings(
                        model=ui_state.model,
                        temperature=ui_state.temperature,
                        top_p=ui_state.top_p,
                        max_tokens=2048,
                    ),
                    language=RespondLanguage(ui_state.language),
                    style=RespondStyle(ui_state.style),
                    user_text=user_text.strip(),
                    use_web_search=ui_state.enable_web_search,
                )
                ui_state.last_tools_used = meta.get("tools_used", [])
            except Exception as e:
                error_str = str(e)
                st.error(f"Error processing your request: {error_str}")
                error_msg = f"Sorry, I encountered an error: {error_str}"
                ctrl.llm_client.add_user_message_to_session(
                    ctrl.session_id, user_text.strip()
                )
                ctrl.llm_client.add_ai_message_to_session(ctrl.session_id, error_msg)

        st.rerun()
