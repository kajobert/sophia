# plugins/tool_file_system.py
"""A tool plugin for interacting with the local file system in a sandboxed way."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.context import SharedContext
from plugins.base_plugin import BasePlugin, PluginType

logger = logging.getLogger(__name__)


class ListDirectoryArgs(BaseModel):
    """Pydantic model for arguments of the list_directory tool."""

    path: Optional[str] = Field(
        ".",
        description=(
            "Lists files and directories inside the designated 'sandbox/' folder. "
            "All paths are relative to this sandbox. Defaults to the sandbox root '.'"
        ),
    )


class ReadFileArgs(BaseModel):
    """Pydantic model for arguments of the read_file tool."""

    path: str = Field(
        ..., description="The path to the file to read, relative to the sandbox root."
    )


class WriteFileArgs(BaseModel):
    """Pydantic model for arguments of the write_file tool."""

    path: str = Field(
        ..., description="The path to the file to write, relative to the sandbox root."
    )
    content: str = Field(..., description="The content to write to the file.")


class AppendToFileArgs(BaseModel):
    """Pydantic model for arguments of the append_to_file tool."""

    path: str = Field(
        ..., description="The path to the file to append to, relative to the sandbox root."
    )
    content: str = Field(..., description="The content to append to the file.")


class DeleteFileArgs(BaseModel):
    """Pydantic model for arguments of the delete_file tool."""

    path: str = Field(
        ..., description="The path to the file to delete, relative to the sandbox root."
    )


class FileSystemTool(BasePlugin):
    """
    A tool plugin providing safe, sandboxed file system operations.

    This plugin allows other parts of the system to read, write, and list
    files within a designated "sandbox" directory. It is designed to prevent
    any file operations outside of this directory, providing a secure way

    """

    def __init__(self) -> None:
        """Initializes the FileSystemTool."""
        super().__init__()
        self.sandbox_path: Path | None = None

    @property
    def name(self) -> str:
        """Gets the name of the plugin."""
        return "tool_file_system"

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
        Sets up the sandboxed directory for file operations.

        Args:
            config: A dictionary containing the configuration for the plugin.
                    It is expected to have a "sandbox_dir" key.
        """
        sandbox_dir = config.get("sandbox_dir", "sandbox")
        self.sandbox_path = Path(sandbox_dir).resolve()
        self.sandbox_path.mkdir(parents=True, exist_ok=True)
        logger.info("File system tool initialized. Sandbox is at '%s'", self.sandbox_path)

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        This tool is not directly executed in the main loop.

        Its methods are designed to be called by other cognitive plugins that
        can formulate tool commands based on the user's intent.
        """
        return context

    def _get_safe_path(self, user_path: str) -> Path:
        """
        Resolves a user-provided path and ensures it is within the sandbox.

        Args:
            user_path: The path provided by the user.

        Returns:
            The resolved, safe path within the sandbox.

        Raises:
            PermissionError: If the path is outside the allowed sandbox.
            ValueError: If the sandbox path has not been configured.
        """
        if self.sandbox_path is None:
            raise ValueError("Sandbox path has not been configured via setup().")

        path = Path(os.path.normpath(user_path))
        if path.is_absolute():
            path = Path(str(path)[1:])

        safe_path = (self.sandbox_path / path).resolve()

        if self.sandbox_path not in safe_path.parents and safe_path != self.sandbox_path:
            raise PermissionError(f"Path '{safe_path}' is outside the allowed sandbox.")

        return safe_path

    def read_file(self, context: SharedContext, path: str) -> str:
        """
        Reads the content of a file within the sandbox.

        Args:
            context: The shared context for the session, providing the logger.
            path: The path to the file to read, relative to the sandbox root.

        Returns:
            The content of the file.

        Raises:
            FileNotFoundError: If the file does not exist at the specified path.
        """
        safe_path = self._get_safe_path(path)
        context.logger.info("Reading file: %s", safe_path)
        if not safe_path.is_file():
            raise FileNotFoundError(f"File not found: {safe_path}")
        return safe_path.read_text(encoding="utf-8")

    def write_file(self, context: SharedContext, path: str, content: str) -> str:
        """
        Writes content to a file within the sandbox.

        Args:
            context: The shared context for the session, providing the logger.
            path: The path to the file to write, relative to the sandbox root.
            content: The content to write to the file.

        Returns:
            A success message.
        """
        safe_path = self._get_safe_path(path)
        context.logger.info("Writing to file: %s", safe_path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} bytes to {path}"

    def append_to_file(self, context: SharedContext, path: str, content: str) -> str:
        """
        Appends content to a file within the sandbox.

        Args:
            context: The shared context for the session, providing the logger.
            path: The path to the file to append to, relative to the sandbox root.
            content: The content to append to the file.

        Returns:
            A success message.
        """
        safe_path = self._get_safe_path(path)
        context.logger.info("Appending to file: %s", safe_path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        with safe_path.open("a", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully appended {len(content)} bytes to {path}"

    def delete_file(self, context: SharedContext, path: str) -> str:
        """
        Deletes a file within the sandbox.

        Args:
            context: The shared context for the session, providing the logger.
            path: The path to the file to delete, relative to the sandbox root.

        Returns:
            A success message.
        """
        safe_path = self._get_safe_path(path)
        context.logger.info("Deleting file: %s", safe_path)
        if not safe_path.is_file():
            raise FileNotFoundError(f"File not found: {safe_path}")
        safe_path.unlink()
        return f"Successfully deleted {path}"

    def list_directory(self, context: SharedContext, path: str = ".") -> List[str]:
        """
        Lists the contents of a directory within the sandbox.

        Args:
            context: The shared context for the session, providing the logger.
            path: The path to the directory to list, relative to the sandbox.

        Returns:
            A list of the names of the files and directories.

        Raises:
            NotADirectoryError: If the path is not a directory.
        """
        safe_path = self._get_safe_path(path)
        context.logger.info("Listing directory: %s", safe_path)
        if not safe_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {safe_path}")
        return [p.name for p in safe_path.iterdir()]

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Gets the definitions of the tools provided by this plugin.

        Returns:
            A list of tool definitions, where each definition is a dictionary
            that conforms to the OpenAPI JSON Schema specification.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "Lists the contents of a directory within the sandbox.",
                    "parameters": ListDirectoryArgs.model_json_schema(),
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Reads the content of a file within the sandbox.",
                    "parameters": ReadFileArgs.model_json_schema(),
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Writes content to a file within the sandbox, overwriting it if it exists.",
                    "parameters": WriteFileArgs.model_json_schema(),
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "append_to_file",
                    "description": "Appends content to the end of a file within the sandbox.",
                    "parameters": AppendToFileArgs.model_json_schema(),
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_file",
                    "description": "Deletes a file within the sandbox.",
                    "parameters": DeleteFileArgs.model_json_schema(),
                },
            },
        ]
