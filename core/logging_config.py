import asyncio
import logging
import logging.handlers
import sys

from pythonjsonlogger import jsonlogger

from core.logging_filter import SessionIdFilter


def setup_logging(log_queue: "asyncio.Queue" = None):
    """
    Configure logging system (IDEMPOTENT).
    Safe to call multiple times - clears and rebuilds handlers.
    """
    # 1. Clear ALL existing handlers first
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    
    # 2. Clear any existing filters
    root_logger.filters.clear()
    
    # 3. Reset logging level
    root_logger.setLevel(logging.INFO)

    # 4. Add the global SessionIdFilter
    session_id_filter = SessionIdFilter()
    root_logger.addFilter(session_id_filter)

    # 5. Console handler (for human readability) - SIMPLE format without session_id
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(name)s: %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # 6. File handler (JSON format for machine readability) - with session_id if available
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

    # 7. Attach handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # 8. Handle queue if provided (for async logging)
    if log_queue:
        queue_handler = logging.handlers.QueueHandler(log_queue)
        root_logger.addHandler(queue_handler)
    
    # 9. Log successful configuration
    logger = logging.getLogger(__name__)
    logger.info("✅ Logging configured (idempotent setup)")
