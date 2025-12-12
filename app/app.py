"""
Main application file for the Market Intelligence Companion Streamlit app.
"""

import streamlit as st
import traceback

from ui.state import init_state
from ui.sidebar import render_sidebar
from ui.tabs import about, market_sector_overview, ai_desk


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
try:
    init_state()

    with st.sidebar:
        render_sidebar(INDEX_PATH)

    st.title("Market Intelligence Companion")
    st.html(
        """
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p { font-size: 18px; }
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
    st.code(traceback.format_exc())
