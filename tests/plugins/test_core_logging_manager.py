import logging
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from plugins.core_logging_manager import CoreLoggingManager


class TestCoreLoggingManager(unittest.TestCase):
    def setUp(self):
        self.plugin = CoreLoggingManager()
        self.session_id = "test-session-1234"
        self.log_dir = Path("logs")
        self.log_file = self.log_dir / f"session_{self.session_id}.log"

        # Clean up any previous log files
        if self.log_file.exists():
            self.log_file.unlink()

    def tearDown(self):
        # Clean up log file after test
        if self.log_file.exists():
            self.log_file.unlink()

    def test_setup_logging_creates_logger(self):
        """Test that a new logger is created for the session."""
        logger = self.plugin.setup_logging(self.session_id)
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, f"session-{self.session_id[:8]}")
        self.assertTrue(logger.propagate is False)

    def test_setup_logging_configures_file_handler(self):
        """Test that a file handler is correctly configured."""
        logger = self.plugin.setup_logging(self.session_id)
        self.assertTrue(any(isinstance(h, logging.FileHandler) for h in logger.handlers))
        self.assertTrue(self.log_file.exists())

        # Test if a log message is written to the file
        test_message = "This is a test log message."
        logger.info(test_message, extra={"plugin_name": self.plugin.name})

        with open(self.log_file, "r") as f:
            content = f.read()
            self.assertIn(test_message, content)
            self.assertIn(self.plugin.name, content)

    def test_setup_logging_configures_console_handler(self):
        """Test that a stream (console) handler is configured."""
        logger = self.plugin.setup_logging(self.session_id)
        self.assertTrue(
            any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        )


if __name__ == "__main__":
    unittest.main()
