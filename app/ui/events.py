"""
UI event handlers and session management utilities.

This module provides event handling functions for the Streamlit UI,
including session management, state resets, and user interaction
processing.

Key functionality:
- Session state management and cleanup
- Complete application reset capabilities
- Event logging and tracking
- UI state synchronization utilities
"""

import streamlit as st
import logging


def reset_session() -> None:
    """
    Perform complete session reset and application restart.

    Clears all session state including API keys, settings, and
    user data. Forces application rerun to provide fresh start.
    """
    st.session_state.clear()
    logging.info("Session state cleared for complete reset.")
    st.rerun()
