"""
Main application file for the Market Intelligence Companion Streamlit app.
"""

import sys
import os
import streamlit as st
import traceback
import logging

if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = (
        "Mozilla/5.0 (compatible; MarketIntelligenceApp/1.0; Streamlit)"
    )

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ui.state import init_state
    from ui.sidebar import render_sidebar
    from ui.tabs import about, market_sector_overview, ai_desk

    logger.info("Successfully imported all modules")
except ImportError as e:
    logger.error(f"Import error: {e}")
    st.error(f"Import error: {e}")
    st.stop()


TAB_RENDERERS = {
    "About": about.render,
    "Market & Sector Overview": market_sector_overview.render,
    "AI Desk": ai_desk.render,
}
TABS = ["About", "Market & Sector Overview", "AI Desk"]
INDEX_PATH = "var/faiss_index"


st.set_page_config(
    page_title="Market Intelligence Companion",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

logger.info("Starting Market Intelligence Companion app")

try:
    logger.info("Initializing app state")
    init_state()

    logger.info("Rendering sidebar")
    with st.sidebar:
        render_sidebar(INDEX_PATH)

    logger.info("Rendering main content")
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

    logger.info("App loaded successfully")

except Exception as e:
    logger.error(f"Application error: {str(e)}", exc_info=True)
    st.error(f"An error occurred: {e}")
    st.code(traceback.format_exc())
