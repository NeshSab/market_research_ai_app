"""
Sidebar interface components for application configuration and controls.

This module provides the sidebar user interface for the market intelligence
application, including API key management, model configuration, knowledge
base management, conversation export utilities, and session controls.

The sidebar serves as the primary configuration hub for users to set up
their environment, manage data sources, and control application behavior.
It integrates with multiple services and provides comprehensive controls
for the application's functionality.

Key features:
- API key configuration and validation
- LLM model and parameter settings
- Knowledge base document management
- Conversation history export tools
- Session state management and controls
- Real-time usage and cost tracking
"""

import os
import traceback
import streamlit as st

from datetime import datetime
from ui.utils import format_duration, get_knowledge_base_files
from ui.widgets.exports import (
    export_conversation_json,
    export_conversation_csv,
    export_conversation_pdf,
)
from core.services.pricing import estimate_cost
from .state import ui_session_state, init_controller
from core.models import RespondStyle, RespondLanguage
from .events import reset_session
from core.services.pricing import PRICE_TABLE
from core.tools.web_load import web_load
from dotenv import load_dotenv

from core.services.logging_setup import setup_logging
from core.services.rag_store import (
    build_faiss_from_documents,
    add_uploaded_files_to_index,
    add_url_content_to_index,
)

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
FRED_KEY = os.getenv("FRED_API_KEY", "")
LANGSMITH_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PR_NAME = os.getenv("LANGSMITH_PROJECT", "")

DEFAULT_KB = get_knowledge_base_files(
    base_patterns=[
        "knowledge_base/playbooks/*.md",
        "knowledge_base/examplars/*.md",
        "knowledge_base/governance/*.md",
    ]
)

STYLES = [
    RespondStyle.CONCISE.value,
    RespondStyle.DETAILED.value,
]
LANGUAGES = [
    RespondLanguage.ENGLISH.value,
    RespondLanguage.SPANISH.value,
    RespondLanguage.FRENCH.value,
    RespondLanguage.GERMAN.value,
]


def render_sidebar(index_path: str) -> None:
    ui_state = ui_session_state()

    st.markdown("## User Acknowledgment")
    ui_state.user_understanding = st.checkbox(
        "I understand this is **not** financial advice.",
        value=ui_state.user_understanding,
        help=(
            "This application provides market context, research tools, and "
            "educational explanations — not personalized investment advice."
        ),
    )

    if not ui_state.user_understanding:
        st.warning("Please acknowledge before using the analysis tools.")
    st.markdown("# Settings")
    with st.expander("🔑 API Keys"):
        api = OPENAI_KEY or st.text_input(
            "OpenAI API key (required)",
            type="password",
            help="Stored only in your session.",
            value=ui_state.api_key or "",
        )
        fred = FRED_KEY or st.text_input(
            "FRED API key (required)",
            type="password",
            help="Needed for CPI/UST10Y live pulls. App works without it.",
            value=ui_state.fred_key or "",
        )
        langsmith_key = LANGSMITH_KEY or st.text_input(
            "LangSmith API key (optional)",
            type="password",
            help="For tracing and observability of LLM calls.",
            value=ui_state.langsmith_key or "",
        )
        langsmith_project_name = LANGSMITH_PR_NAME or st.text_input(
            "LangChain Project Name",
            help=("Specify the LangChain project name for tracing. "),
            value=ui_state.langsmith_project or "",
        )

    if st.button("Initialize", type="primary", use_container_width=True):
        if not ui_state.user_understanding:
            st.error("Please acknowledge the user understanding first.")
        else:
            try:
                ui_state.api_key = api.strip()
                ui_state.fred_key = fred.strip()
                ui_state.langsmith_key = langsmith_key.strip()
                ui_state.langsmith_project = langsmith_project_name.strip()

                if not ui_state.api_key or not ui_state.fred_key:
                    st.error("OpenAI and FRED API keys are required.")
                    st.stop()
                os.environ["OPENAI_API_KEY"] = ui_state.api_key
                ui_state.api_key_set = True
                init_controller()

                if ui_state.fred_key:
                    os.environ["FRED_API_KEY"] = ui_state.fred_key

                os.makedirs("var", exist_ok=True)
                if not os.path.exists(index_path):
                    build_faiss_from_documents(DEFAULT_KB, index_path)

                if ui_state.langsmith_key and ui_state.langsmith_key.strip():
                    os.environ["LANGSMITH_API_KEY"] = ui_state.langsmith_key
                    ui_state.langsmith_enabled = "true"
                    os.environ["LANGSMITH_PROJECT"] = ui_state.langsmith_project
                    os.environ["LANGSMITH_TRACING"] = "true"

                setup_logging(ui_state.langsmith_enabled, ui_state.trace_level)

                st.success("Initialized.")
            except Exception as e:
                st.error(f"Initialization failed: {e}")
                traceback.print_exc()

    if ui_state.api_key_set:
        ctrl = ui_state.controller
        if ctrl.get_history():
            st.subheader("Model")
            ui_state.model = st.selectbox(
                "OpenAI model",
                list(PRICE_TABLE.keys()),
                index=(
                    list(PRICE_TABLE.keys()).index(ui_state.model)
                    if ui_state.model in PRICE_TABLE
                    else 0
                ),
                help="Used for analysis and summaries.",
            )
            st.subheader("Web Search")
            ui_state.enable_web_search = st.checkbox(
                "Enable Web Search",
                value=ui_state.enable_web_search,
                help="Allow AI to search approved financial news sources",
            )
            if ui_state.enable_web_search:
                if not os.getenv("USER_AGENT"):
                    os.environ["USER_AGENT"] = (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 "
                        "Safari/537.36"
                    )

            st.subheader("Generation Controls")
            c1, c2 = st.columns(2)
            ui_state.temperature = c1.slider(
                "Creativity", 0.0, 1.0, ui_state.temperature, 0.05
            )
            ui_state.top_p = c2.slider(
                "Response diversity", 0.0, 1.0, ui_state.top_p, 0.05
            )
            ui_state.style = st.radio(
                "Response style",
                STYLES,
                index=STYLES.index(ui_state.style),
                horizontal=True,
            )
            ui_state.language = st.selectbox(
                "Language", LANGUAGES, index=LANGUAGES.index(ui_state.language)
            )
            st.divider()

            st.subheader("📚 Knowledge Base (RAG)")
            st.caption(
                "Optionally add custom docs, e.g. financial quarterly report, "
                + "to the knowledge base."
            )

            uploaded = st.file_uploader(
                "Add docs (.md/.txt/.pdf)",
                type=["md", "txt", "pdf"],
                accept_multiple_files=True,
                key=f"file_uploader_{ui_state.file_uploader_key}",
            )
            if uploaded:
                st.info(
                    f"📁 {len(uploaded)} document(s) uploaded and ready to process."
                )

                if st.button("Add to Knowledge Base", type="primary"):
                    with st.spinner(f"Adding {len(uploaded)} document(s)..."):
                        try:
                            abs_index_path = os.path.abspath(index_path)
                            success = add_uploaded_files_to_index(
                                uploaded, abs_index_path
                            )
                            
                            if success:
                                st.success(
                                    f"✅ Successfully added {len(uploaded)} "
                                    f"document(s) to knowledge base!"
                                )
                                st.info(
                                    "📚 The documents are now searchable in AI Desk."
                                )
                            else:
                                st.warning(
                                    "⚠️ Some documents may not have been processed."
                                )

                            ui_state.file_uploader_key += 1
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Failed to add documents: {e}")
                            st.code(traceback.format_exc())

            st.markdown("**Or add content from URL:**")
            url_input = st.text_input(
                "Enter URL",
                placeholder="https://example.com/article",
                help="Add web content directly to knowledge base",
                key=f"web_uploader_{ui_state.web_uploader_key}",
            )

            if url_input.strip():
                if st.button("Add to Knowledge Base", type="secondary"):
                    with st.spinner(f"Loading content from {url_input}..."):
                        try:
                            content = web_load.invoke({"link": url_input.strip()})
                            if content and content != "No content loaded":
                                abs_index_path = os.path.abspath(index_path)
                                success = add_url_content_to_index(
                                    url_input.strip(), content, abs_index_path
                                )
                                
                                if success:
                                    st.success(
                                        "✅ Successfully added URL content "
                                        "to knowledge base!"
                                    )
                                    st.info(
                                        "📚 The web content is now searchable "
                                        "in AI Desk."
                                    )
                                else:
                                    st.warning(
                                        "⚠️ URL content may not have been "
                                        "processed correctly."
                                    )
                            else:
                                st.error("❌ No content could be loaded from this URL")

                        except Exception as e:
                            st.error(f"❌ Failed to add URL content: {e}")
                            st.code(traceback.format_exc())

                        ui_state.web_uploader_key += 1
                        st.rerun()

            st.divider()

            with st.expander("💰 Usage & Cost", expanded=False):

                if ctrl and ctrl.state.model_usage:
                    st.metric("Total Session Cost", f"${ctrl.state.total_cost:.4f}")
                    now_ts = datetime.now().timestamp()
                    session_secs = now_ts - float(ui_state.session_start_ts or now_ts)
                    st.metric("Session Time", format_duration(session_secs))

                    st.markdown("**Per Model Usage:**")
                    for model, usage in ctrl.state.model_usage.items():
                        tokens_in = usage["tokens_in"]
                        tokens_out = usage["tokens_out"]
                        cost = estimate_cost(model, tokens_in, tokens_out)

                        with st.container():
                            st.markdown(f"**{model}**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("In", f"{tokens_in:,}")
                            with col2:
                                st.metric("Out", f"{tokens_out:,}")
                            col3, _ = st.columns(2)
                            with col3:
                                st.metric("Cost", f"${cost:.4f}")
                else:
                    st.info("No usage data yet")

            st.divider()
            history = ctrl.get_history()
            if history and len(history) > 0:
                st.subheader("📄 Export Conversation")
                export_format = st.selectbox(
                    "Choose format:",
                    ["JSON", "CSV", "PDF"],
                    help="Export your conversation in different formats",
                )

                if st.button("Export Conversation", use_container_width=True):
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"conversation_export_{timestamp}"

                        if export_format == "JSON":
                            data = export_conversation_json(history)
                            st.download_button(
                                label="📥 Download JSON",
                                data=data,
                                file_name=f"{filename}.json",
                                mime="application/json",
                                use_container_width=True,
                            )
                        elif export_format == "CSV":
                            data = export_conversation_csv(history)
                            st.download_button(
                                label="📥 Download CSV",
                                data=data,
                                file_name=f"{filename}.csv",
                                mime="text/csv",
                                use_container_width=True,
                            )
                        elif export_format == "PDF":
                            data = export_conversation_pdf(history)
                            st.download_button(
                                label="📥 Download PDF",
                                data=data,
                                file_name=f"{filename}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                            )
                        st.success(f"✅ {export_format} export ready for download!")
                    except Exception as e:
                        st.error(f"Export failed: {str(e)}")

            st.divider()
            
            st.subheader("📋 Export Logs")
            if st.button("Export App Logs", use_container_width=True):
                try:
                    log_file_path = "logs/app.log"
                    if os.path.exists(log_file_path):
                        with open(log_file_path, 'r', encoding='utf-8') as f:
                            log_content = f.read()
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"app_logs_{timestamp}.log"
                        
                        st.download_button(
                            label="📥 Download Logs",
                            data=log_content,
                            file_name=filename,
                            mime="text/plain",
                            use_container_width=True,
                        )
                        st.success("✅ Log file ready for download!")
                    else:
                        st.warning(
                            "⚠️ No log file found. Try using the app first "
                            "to generate logs."
                        )
                except Exception as e:
                    st.error(f"Failed to export logs: {str(e)}")

            st.divider()
            if st.button("Reset session", type="primary", use_container_width=True):
                reset_session()
                st.rerun()

            langsmith_status = "on" if ui_state.langsmith_enabled == "true" else "off"
            st.caption(f"LangSmith: **{langsmith_status}**")
