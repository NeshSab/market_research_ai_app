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
from pathlib import Path
from langsmith import Client

_logging_initialized = False


def setup_logging(trace_level: str = "info") -> None:
    """
    Configure basic application logging to file.

    Sets up file-based logging with configurable levels.

    Parameters
    ----------
    trace_level : str
        Logging detail level ("verbose" for DEBUG, others for INFO)
    """
    global _logging_initialized

    if _logging_initialized:
        return

    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    root_logger = logging.getLogger()

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(str(log_file), mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG if trace_level == "verbose" else logging.INFO)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    file_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.DEBUG if trace_level == "verbose" else logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    _logging_initialized = True

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - writing to: {log_file}")
    logger.info(f"Log level: {'DEBUG' if trace_level == 'verbose' else 'INFO'}")


def setup_langsmith(langsmith_enabled: str) -> None:
    """
    Configure LangSmith tracing.

    Initializes LangSmith client if enabled and API key is available.
    Can be called multiple times to reconfigure.

    Parameters
    ----------
    langsmith_enabled : str
        Whether to enable LangSmith tracing ("true" to enable)
    """
    logger = logging.getLogger(__name__)

    if langsmith_enabled == "true":
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        if langsmith_api_key:
            try:
                client = Client()
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
                logger.error(f"Failed to initialize LangSmith client: {e}")
        else:
            logger.warning("LangSmith enabled but LANGSMITH_API_KEY not found")
