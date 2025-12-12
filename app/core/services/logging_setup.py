"""
Application logging configuration and setup.

This module provides centralized logging configuration for the market
intelligence application. It handles both standard Python logging
to files and optional LangSmith tracing for LLM interactions.

Features:
- File-based logging with configurable levels
- LangSmith integration for LLM tracing
- Automatic log directory creation
- Structured log formatting with timestamps
"""

import logging
import os
from langsmith import Client


def setup_logging(langsmith_enabled: str, trace_level: str) -> None:
    """
    Configure application logging and optional LangSmith tracing.

    Sets up file-based logging with configurable levels and initializes
    LangSmith client if enabled and API key is available.

    Parameters
    ----------
    langsmith_enabled : str
        Whether to enable LangSmith tracing ("true" to enable)
    trace_level : str
        Logging detail level ("verbose" for DEBUG, others for INFO)
    """
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/app.log",
        level=logging.DEBUG if trace_level == "verbose" else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if langsmith_enabled == "true":
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        if langsmith_api_key:
            try:
                client = Client()
                logger = logging.getLogger(__name__)

                logger.info("LangSmith client initialized successfully")
                project_name = os.getenv("LANGSMITH_PROJECT")
                if project_name:
                    logger.info(
                        f"LangSmith tracing enabled for project: {project_name}"
                    )
                else:
                    logger.info("LangSmith tracing enabled (default project)")

                if client:
                    logger.debug("LangSmith client is ready for tracing")

            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to initialize LangSmith client: {e}")
        else:
            logger = logging.getLogger(__name__)
            logger.warning("LangSmith enabled but LANGSMITH_API_KEY not found")
