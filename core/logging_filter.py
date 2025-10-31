# core/logging_filter.py
"""A custom logging filter to inject a session ID into log records."""

import logging


class SessionIdFilter(logging.Filter):
    """
    A logging filter that ensures a 'session_id' is present in every log record.

    This filter checks if a 'session_id' attribute exists on the log record.
    If it does not, it adds a default value of "global" to the record. This
    prevents `KeyError` exceptions in the log formatter when log messages
    originate from libraries or parts of the application that are not
    session-aware.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Adds a default session_id to the log record if it's missing.

        Args:
            record: The log record to be processed.

        Returns:
            Always returns True to ensure the record is processed.
        """
        if not hasattr(record, "session_id"):
            record.session_id = "global"  # type: ignore
        return True
