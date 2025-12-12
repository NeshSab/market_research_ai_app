"""
Ultra-minimal Streamlit app for cloud deployment testing.
"""

import streamlit as st
import sys
import os

st.title("Hello Streamlit Cloud!")
st.write("If you can see this, the deployment is working.")

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
