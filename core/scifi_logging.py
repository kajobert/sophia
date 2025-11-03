"""
Logging Handler for Sci-Fi Terminal Interfaces
===============================================

Redirects Python logging to colorful sci-fi terminal UI.
Shows logs in organized panels like UV/Docker installations.
"""

import logging
import time
from typing import Optional
from collections import deque
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich import box


class SciFiLoggingHandler(logging.Handler):
    """
    Custom logging handler that redirects logs to sci-fi terminal interface.
    
    Shows logs in organized panel (UV/Docker style) while keeping
    main output area clean.
    """
    
    def __init__(self, interface_plugin, max_logs: int = 10, level=logging.INFO):
        super().__init__(level)
        self.interface = interface_plugin
        self.max_logs = max_logs
        
        # Ring buffer for last N logs
        self.log_buffer = deque(maxlen=max_logs)
        
        # Rate limiting to avoid spam (UV style!)
        self._last_update = 0
        self._update_interval = 0.1  # Max 10 FPS
        
        # Color mapping for log levels
        self.level_colors = {
            'DEBUG': 'dim cyan',
            'INFO': 'cyan',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold red',
        }
        
        # Icon mapping
        self.level_icons = {
            'DEBUG': '🔍',
            'INFO': '⚙️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🚨',
        }
    
    def emit(self, record: logging.LogRecord):
        """Send log record to sci-fi interface."""
        try:
            msg = self.format(record)
            level_name = record.levelname
            
            # Extract just the important part
            if " - " in msg and "[" in msg:
                parts = msg.split(" - ")
                if len(parts) >= 4:
                    msg = parts[-1]  # Get just the message part
            
            # Skip boring technical logs
            if any(skip in msg.lower() for skip in ['plugin_name', 'extra={', 'traceback']):
                return
            
            # Add to buffer
            color = self.level_colors.get(level_name, 'white')
            icon = self.level_icons.get(level_name, 'ℹ️')
            
            # Format: [icon] message
            formatted = f"{icon} {msg}"
            self.log_buffer.append((color, formatted))
            
            # Update display with rate limiting (UV style smooth updates!)
            now = time.time()
            if now - self._last_update >= self._update_interval:
                if hasattr(self.interface, 'update_log_display'):
                    self.interface.update_log_display(self.log_buffer)
                self._last_update = now
                
        except Exception:
            self.handleError(record)
    
    def get_log_panel(self) -> Panel:
        """Create panel with last N logs (UV/Docker style)."""
        text = Text()
        
        if not self.log_buffer:
            text.append("  Waiting for activity...", style="dim cyan")
        else:
            for color, msg in self.log_buffer:
                text.append(f"  {msg}\n", style=color)
        
        return Panel(
            text,
            title="[bold cyan]⚙️ System Activity[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,  # Soft rounded corners like UV
            padding=(0, 1),
            height=self.max_logs + 2  # +2 for borders
        )


def install_scifi_logging(interface_plugin, logger_name: Optional[str] = None, max_logs: int = 10):
    """
    Install sci-fi logging handler to redirect logs to terminal UI.
    
    Args:
        interface_plugin: The sci-fi terminal interface plugin
        logger_name: Logger to hook (None = root logger)
        max_logs: Number of log lines to show in bottom panel
    """
    # Get logger
    target_logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    
    # CRITICAL: Disable ALL console handlers to prevent duplicate output!
    for handler in target_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            # Set level to ERROR so only critical stuff shows in old format
            handler.setLevel(logging.ERROR)
    
    # Add sci-fi handler for INFO and above
    handler = SciFiLoggingHandler(interface_plugin, max_logs=max_logs, level=logging.INFO)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    target_logger.addHandler(handler)
    
    # Store handler reference in interface for access
    interface_plugin._scifi_log_handler = handler
    
    return handler
