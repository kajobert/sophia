# core/logging_config.py
import logging
import sys
from logging import Formatter, LogRecord
from typing import Literal

import colorlog


class SafeFormatter(Formatter):
    """A custom formatter that ensures 'session_id' is present in the log record."""

    def format(self, record: LogRecord) -> str:
        if not hasattr(record, "session_id"):
            record.session_id = "N/A"
        return super().format(record)


class SafeColorFormatter(colorlog.ColoredFormatter):
    """A custom color formatter that ensures 'session_id' is present."""

    def format(self, record: LogRecord) -> str:
        if not hasattr(record, "session_id"):
            record.session_id = "N/A"
        return super().format(record)


def get_logging_config(
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    log_file: str = "logs/app.log",
) -> dict:
    """
    Get the logging configuration dictionary.

    Args:
        log_level: The logging level to set for the application.
        log_file: The file path to save the logs.

    Returns:
        A dictionary with the logging configuration.
    """
    # Ensure log level is a valid string
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "()": SafeFormatter,
                "format": (
                    "%(asctime)s - %(levelname)s - [%(session_id)s] - " "%(name)s - %(message)s"
                ),
            },
            "colored": {
                "()": SafeColorFormatter,
                "format": (
                    "%(log_color)s%(asctime)s - %(levelname)s - [%(session_id)s] - "
                    "%(name)s - %(message)s"
                ),
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "colored",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "standard",
                "filename": log_file,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "root": {"handlers": ["console", "file"], "level": log_level},
    }


def setup_logging(
    default_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    log_file: str = "logs/app.log",
) -> None:
    """
    Set up the logging for the application.

    Args:
        default_level: The default logging level.
        log_file: The path to the log file.
    """
    import logging.config
    import os

    try:
        # Ensure the logs directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        config = get_logging_config(log_level=default_level, log_file=log_file)
        logging.config.dictConfig(config)
        logging.info("Logging configured successfully.")
    except Exception as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Error setting up logging from config: {e}", exc_info=True)
