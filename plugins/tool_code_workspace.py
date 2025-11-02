# plugins/tool_code_workspace.py
"""A tool plugin for reading code from the workspace (not sandboxed)."""

import logging
from pathlib import Path
from typing import Any, Dict

from core.context import SharedContext
from plugins.base_plugin import BasePlugin, PluginType

logger = logging.getLogger(__name__)


class CodeWorkspaceTool(BasePlugin):
    """
    A tool plugin for reading code and documentation from the project workspace.
    
    This plugin allows read-only access to specific workspace directories
    like plugins/, docs/, config/ for code analysis and learning purposes.
    Write operations are still restricted to the sandbox.
    """

    def __init__(self) -> None:
        """Initializes the CodeWorkspaceTool."""
        super().__init__()
        self.project_root: Path | None = None
        self.allowed_read_paths = ["plugins", "docs", "config", "core", "tests"]

    @property
    def name(self) -> str:
        """Gets the name of the plugin."""
        return "tool_code_workspace"

    @property
    def plugin_type(self) -> PluginType:
        """Gets the type of the plugin."""
        return PluginType.TOOL

    @property
    def version(self) -> str:
        """Gets the version of the plugin."""
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """
        Sets up the workspace root directory.

        Args:
            config: A dictionary containing the configuration for the plugin.
        """
        # Default to current directory
        self.project_root = Path.cwd().resolve()
        logger.info(
            "Code workspace tool initialized. Project root: '%s'", 
            self.project_root,
            extra={"plugin_name": self.name}
        )

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        This tool is not directly executed in the main loop.
        Its methods are called by cognitive plugins.
        """
        return context

    def _is_allowed_path(self, user_path: str) -> bool:
        """
        Check if the path is in an allowed directory.
        
        Args:
            user_path: The path to check
            
        Returns:
            True if path is allowed for reading
        """
        path = Path(user_path)
        # Check if path starts with any allowed directory
        for allowed in self.allowed_read_paths:
            if str(path).startswith(allowed + "/") or str(path) == allowed:
                return True
        return False

    def _get_safe_path(self, user_path: str) -> Path:
        """
        Resolves a user-provided path and ensures it's in an allowed location.

        Args:
            user_path: The path provided by the user (relative to project root)

        Returns:
            The resolved, safe path

        Raises:
            PermissionError: If the path is not in an allowed directory
            ValueError: If the project root hasn't been configured
        """
        if self.project_root is None:
            raise ValueError("Project root has not been configured via setup().")

        # Normalize the path
        path = Path(user_path)
        
        # Check if it's allowed
        if not self._is_allowed_path(str(path)):
            raise PermissionError(
                f"Path '{user_path}' is not in allowed directories: {self.allowed_read_paths}"
            )

        # Resolve to absolute path
        safe_path = (self.project_root / path).resolve()

        # Ensure it's actually within project root
        if self.project_root not in safe_path.parents and safe_path != self.project_root:
            raise PermissionError(f"Path '{safe_path}' is outside the project root.")

        return safe_path

    def list_directory(self, context: SharedContext, path: str = "plugins") -> list[str]:
        """
        Lists files and directories in an allowed workspace directory.

        Args:
            context: The shared context for the session
            path: The path to list, relative to project root (default: "plugins")

        Returns:
            A list of file and directory names

        Raises:
            PermissionError: If path is not in allowed directories
            NotADirectoryError: If the path is not a directory
        """
        safe_path = self._get_safe_path(path)
        context.logger.info(
            "Listing directory: %s", safe_path,
            extra={"plugin_name": self.name}
        )
        
        if not safe_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {safe_path}")

        items = [item.name for item in safe_path.iterdir()]
        return items

    def read_file(self, context: SharedContext, path: str) -> str:
        """
        Reads the content of a file in an allowed workspace directory.

        Args:
            context: The shared context for the session
            path: The path to the file, relative to project root

        Returns:
            The content of the file

        Raises:
            PermissionError: If path is not in allowed directories
            FileNotFoundError: If the file doesn't exist
        """
        safe_path = self._get_safe_path(path)
        context.logger.info(
            "Reading file: %s", safe_path,
            extra={"plugin_name": self.name}
        )
        
        if not safe_path.is_file():
            raise FileNotFoundError(f"File not found: {safe_path}")

        return safe_path.read_text(encoding="utf-8")

    def file_exists(self, context: SharedContext, path: str) -> bool:
        """
        Checks if a file exists in an allowed workspace directory.

        Args:
            context: The shared context for the session
            path: The path to check, relative to project root

        Returns:
            True if file exists, False otherwise
        """
        try:
            safe_path = self._get_safe_path(path)
            return safe_path.exists()
        except (PermissionError, ValueError):
            return False
