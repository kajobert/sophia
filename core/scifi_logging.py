"""
Logging Handler for Sci-Fi Terminal Interfaces
===============================================

Redirects Python logging to colorful sci-fi terminal UI.
"""

import logging
from typing import Optional


class SciFiLoggingHandler(logging.Handler):
    """
    Custom logging handler that redirects logs to sci-fi terminal interface.
    
    Instead of boring text logs, shows:
    - Cyberpunk: Colorful cyan/magenta/yellow messages
    - Matrix: Green monochrome messages
    - Star Trek: Orange/blue LCARS messages
    """
    
    def __init__(self, interface_plugin, level=logging.INFO):
        super().__init__(level)
        self.interface = interface_plugin
        
        # Color mapping for log levels
        self.level_colors = {
            'DEBUG': ('dim', '🔍'),
            'INFO': ('cyan', 'ℹ️'),
            'WARNING': ('yellow', '⚠️'),
            'ERROR': ('red', '❌'),
            'CRITICAL': ('bold red', '🚨'),
        }
    
    def emit(self, record: logging.LogRecord):
        """Send log record to sci-fi interface."""
        try:
            msg = self.format(record)
            level_name = record.levelname
            
            # Extract just the important part (remove session IDs, timestamps if already formatted)
            if " - " in msg and "[" in msg:
                # Format: "2025-11-03 21:24:44,231 - [INFO] - [session-id] - session-xxx: Actual message"
                parts = msg.split(" - ")
                if len(parts) >= 4:
                    msg = parts[-1]  # Get just the message part
            
            # Skip boring technical logs
            if any(skip in msg.lower() for skip in ['plugin_name', 'extra={', 'traceback']):
                return
            
            # Send to interface based on type
            interface_name = self.interface.name if hasattr(self.interface, 'name') else 'unknown'
            
            if 'cyberpunk' in interface_name or 'scifi' in interface_name:
                self._emit_cyberpunk(level_name, msg)
            elif 'matrix' in interface_name:
                self._emit_matrix(level_name, msg)
            elif 'startrek' in interface_name:
                self._emit_startrek(level_name, msg)
            else:
                # Fallback to console
                self.interface.console.print(f"[dim]{level_name}:[/] {msg}")
                
        except Exception:
            self.handleError(record)
    
    def _emit_cyberpunk(self, level: str, msg: str):
        """Emit log in Cyberpunk style."""
        color, emoji = self.level_colors.get(level, ('white', 'ℹ️'))
        
        # Show only important messages
        if level in ['WARNING', 'ERROR', 'CRITICAL']:
            self.interface.console.print(f"[{color}]{emoji} {msg}[/]")
        elif 'User input' in msg or 'response' in msg.lower() or 'plan' in msg.lower():
            # Show important activity
            self.interface.console.print(f"[dim cyan]⚙️  {msg}[/]")
    
    def _emit_matrix(self, level: str, msg: str):
        """Emit log in Matrix style."""
        if level in ['WARNING', 'ERROR', 'CRITICAL']:
            self.interface.console.print(f"[bold green]⚠ {msg}[/]")
        elif 'User input' in msg or 'response' in msg.lower():
            self.interface.console.print(f"[color(34)]> {msg}[/]")
    
    def _emit_startrek(self, level: str, msg: str):
        """Emit log in Star Trek LCARS style."""
        if level in ['WARNING', 'ERROR', 'CRITICAL']:
            self.interface.console.print(f"[red]🚨 RED ALERT: {msg}[/]")
        elif 'User input' in msg or 'response' in msg.lower():
            self.interface.console.print(f"[blue]▸ COMPUTER: {msg}[/]")


def install_scifi_logging(interface_plugin, logger_name: Optional[str] = None):
    """
    Install sci-fi logging handler to redirect logs to terminal UI.
    
    Args:
        interface_plugin: The sci-fi terminal interface plugin
        logger_name: Logger to hook (None = root logger)
    """
    # Get logger
    target_logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    
    # CRITICAL: Disable ALL console handlers to prevent duplicate output!
    for handler in target_logger.handlers[:]:  # Copy list to avoid modification during iteration
        if isinstance(handler, logging.StreamHandler):
            # Set level to ERROR so only critical stuff shows in old format
            handler.setLevel(logging.ERROR)
    
    # Add sci-fi handler for INFO and above
    handler = SciFiLoggingHandler(interface_plugin, level=logging.INFO)
    formatter = logging.Formatter('%(message)s')  # Simple format, colors come from handler
    handler.setFormatter(formatter)
    target_logger.addHandler(handler)
    
    return handler
