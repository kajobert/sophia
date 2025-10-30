import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

# ANSI escape codes for colors
COLORS = {
    "WARNING": "\033[93m",
    "INFO": "\033[92m",
    "DEBUG": "\033[94m",
    "CRITICAL": "\033[91m",
    "ERROR": "\033[91m",
    "ENDC": "\033[0m",
}


class ColoredFormatter(logging.Formatter):
    """A custom formatter to add colors to log messages."""

    def format(self, record):
        levelname = record.levelname
        if levelname in COLORS:
            # Color the plugin name part of the log format
            record.plugin_name_colored = f"{COLORS[levelname]}{record.plugin_name}{COLORS['ENDC']}"
            record.levelname_colored = f"{COLORS[levelname]}{levelname}{COLORS['ENDC']}"
        else:
            record.plugin_name_colored = record.plugin_name
            record.levelname_colored = levelname

        # Standard formatting call
        return super().format(record)


class CoreLoggingManager(BasePlugin):
    """A core plugin for centralized logging management."""

    @property
    def name(self) -> str:
        return "core_logging_manager"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.CORE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """This plugin has no external dependencies to set up."""
        pass

    async def execute(self, context: SharedContext) -> SharedContext:
        """This plugin is not meant to be executed directly."""
        return context

    def setup_logging(self, session_id: str) -> logging.Logger:
        """
        Configures the root logger for file and console output for a specific
        session.
        """
        # Create a logger specific to this session
        session_logger = logging.getLogger(f"session-{session_id[:8]}")
        session_logger.setLevel(logging.INFO)

        # Prevent propagation to the root logger to avoid duplicate messages
        session_logger.propagate = False

        # --- File Handler ---
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"session_{session_id}.log"

        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(plugin_name)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

        # --- Console Handler ---
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            "%(asctime)s - %(levelname_colored)s - [%(plugin_name_colored)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)

        # Clear existing handlers and add the new ones
        if session_logger.hasHandlers():
            session_logger.handlers.clear()

        session_logger.addHandler(file_handler)
        session_logger.addHandler(console_handler)

        session_logger.info(
            "Logging configured for session %s.",
            session_id,
            extra={"plugin_name": self.name},
        )
        return session_logger
