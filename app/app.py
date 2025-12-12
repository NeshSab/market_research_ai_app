"""
Minimal test version of the Market Intelligence Companion app.
This version helps diagnose deployment issues.
"""

import streamlit as st
import sys
import os

# Set USER_AGENT for cloud deployment
if not os.getenv("USER_AGENT"):
    os.environ["USER_AGENT"] = (
        "Mozilla/5.0 (compatible; MarketIntelligenceApp/1.0; Streamlit)"
    )

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="Market Intelligence Companion",
    page_icon="📊",
    layout="wide",
)

st.title("🚀 Market Intelligence Companion")
st.success("✅ App is running successfully!")

st.info("This is a minimal version to test Streamlit Cloud deployment.")

# Basic functionality test
st.subheader("Environment Test")
st.write(f"Python version: {sys.version}")
st.write(f"Current working directory: {os.getcwd()}")
st.write(f"USER_AGENT set: {bool(os.getenv('USER_AGENT'))}")

# Test imports
try:
    import streamlit as st

    st.write("✅ Core dependencies imported successfully")
except ImportError as e:
    st.error(f"❌ Import error: {e}")

st.write("---")
st.write("If you see this message, the basic app structure is working!")
st.write("Next step: Gradually add back the original functionality.")
