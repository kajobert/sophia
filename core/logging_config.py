import asyncio
import logging
import logging.handlers
import sys

from pythonjsonlogger import jsonlogger

from core.logging_filter import SessionIdFilter


def setup_logging(log_queue: "asyncio.Queue"):
    """Configures the root logger for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Add the global filter to all handlers
    session_id_filter = SessionIdFilter()
    root_logger.addFilter(session_id_filter)

    # Console handler (for human readability)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - [%(session_id)s] - %(name)s: %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # File handler (JSON format for machine readability)
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/sophia.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(session_id)s %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Queue handler (for real-time streaming)
    # The implementation for this will be part of a future `interface_logstream` plugin.

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
