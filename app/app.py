"""
Main application file for the Market Intelligence Companion Streamlit app.
"""

import sys
import os
import streamlit as st

if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = (
        "Mozilla/5.0 (compatible; MarketIntelligenceApp/1.0; Streamlit)"
    )

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.services.logging_setup import setup_logging  # noqa: E402

setup_logging("basic")

try:
    from ui.state import init_state
    from ui.sidebar import render_sidebar
    from ui.tabs import about, market_sector_overview, ai_desk
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()


TAB_RENDERERS = {
    "About": about.render,
    "Market & Sector Overview": market_sector_overview.render,
    "AI Desk": ai_desk.render,
}
TABS = ["About", "Market & Sector Overview", "AI Desk"]

APP_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(APP_DIR, "var", "faiss_index")


st.set_page_config(
    page_title="Market Intelligence Companion",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    init_state()
    with st.sidebar:
        render_sidebar(INDEX_PATH)

    st.title("Market Intelligence Companion")
    st.html(
        """
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 18px;
    }
    </style>
    """
    )

    tab_objs = st.tabs(TABS)

    for tab, name in zip(tab_objs, TABS):
        with tab:
            if name not in ["About"]:
                TAB_RENDERERS[name](INDEX_PATH)
            else:
                TAB_RENDERERS[name]()


except Exception as e:
    st.error(f"An error occurred: {e}")
