# core/logging_filter.py
"""A custom logging filter to inject a session ID into log records."""

import logging


class SessionIdFilter(logging.Filter):
    """
    A logging filter that ensures a 'session_id' is present in every log record.

    This filter can be initialized with a specific session_id, or will use "global"
    as a default. It adds this session_id to all log records that don't already
    have one, preventing `KeyError` exceptions in log formatters when log messages
    originate from libraries or parts of the application that are not session-aware.
    """

    def __init__(self, session_id: str = "global"):
        """
        Initialize the filter with a session ID.

        Args:
            session_id: The session ID to inject into log records. Defaults to "global".
        """
        super().__init__()
        self.session_id = session_id

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Adds the session_id to the log record if it's missing.

        Args:
            record: The log record to be processed.

        Returns:
            Always returns True to ensure the record is processed.
        """
        if not hasattr(record, "session_id"):
            record.session_id = self.session_id  # type: ignore
        return True
