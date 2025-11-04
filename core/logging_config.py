import asyncio
import logging
import logging.handlers
import sys

from pythonjsonlogger import jsonlogger

from core.logging_filter import SessionIdFilter


def setup_logging(log_queue: "asyncio.Queue" = None):
    """Configures the root logger for the application."""
    root_logger = logging.getLogger()
    
    # Skip if already configured (prevent duplicate handlers)
    if root_logger.handlers:
        return
    
    root_logger.setLevel(logging.INFO)

    # Add the global filter to all handlers FIRST (before any plugins log)
    session_id_filter = SessionIdFilter()
    root_logger.addFilter(session_id_filter)

    # Console handler (for human readability) - SIMPLE format without session_id
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(name)s: %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # File handler (JSON format for machine readability) - with session_id if available
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/sophia.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    # Custom formatter that handles missing session_id gracefully
    class SafeJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, log_record, record, message_dict):
            super().add_fields(log_record, record, message_dict)
            # Add session_id only if it exists
            if hasattr(record, 'session_id'):
                log_record['session_id'] = record.session_id
    
    file_formatter = SafeJsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Queue handler (for real-time streaming)
    # The implementation for this will be part of a future `interface_logstream` plugin.

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
