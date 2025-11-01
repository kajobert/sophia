import logging
import pytest
from unittest.mock import patch
from core.logging_config import setup_logging
from core.logging_filter import SessionIdFilter
import asyncio


@pytest.mark.usefixtures()
class TestLoggingConfig:
    @pytest.fixture(autouse=True)
    def reset_logging(self):
        """Reset logging configuration before each test."""
        logging.shutdown()
        logging.root.handlers = []
        yield
        logging.shutdown()
        logging.root.handlers = []

    @patch("core.logging_config.logging.StreamHandler")
    @patch("core.logging_config.logging.handlers.RotatingFileHandler")
    def test_setup_logging_configures_handlers(self, mock_file_handler, mock_stream_handler):
        """Test that setup_logging adds the console and file handlers."""
        mock_queue = asyncio.Queue()
        setup_logging(log_queue=mock_queue)

        # The handlers are mocked, so they won't be added to the logger instance.
        # Instead, we assert that their constructors were called.
        mock_stream_handler.assert_called_once()
        mock_file_handler.assert_called_once_with(
            "logs/sophia.log", maxBytes=10 * 1024 * 1024, backupCount=5
        )

    def test_session_id_filter_adds_global_if_missing(self):
        """Test that the SessionIdFilter adds a default 'global' session_id if it's missing."""
        filter = SessionIdFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = filter.filter(record)
        assert result is True
        assert hasattr(record, "session_id")
        assert record.session_id == "global"

    def test_session_id_filter_preserves_existing_id(self):
        """Test that the SessionIdFilter does not overwrite an existing session_id."""
        filter = SessionIdFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.session_id = "existing-session-123"
        result = filter.filter(record)
        assert result is True
        assert record.session_id == "existing-session-123"
