import os
import asyncio
from typing import Type, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

# --- Custom Exceptions ---


class FileSystemError(Exception):
    """Base class for file system tool errors."""

    pass


class PathOutsideSandboxError(FileSystemError):
    """Raised when a path is outside the allowed sandbox directory."""

    pass


class FileSystemNotFoundError(FileSystemError, FileNotFoundError):
    """Raised when a file or directory is not found."""

    pass


class IsDirectoryError(FileSystemError):
    """Raised when a file operation is attempted on a directory."""

    pass


class NotDirectoryError(FileSystemError):
    """Raised when a directory operation is attempted on a file."""

    pass


# --- Tool Implementations ---

SANDBOX_DIR = os.path.abspath("sandbox")


class FileSystemBaseTool(BaseTool):
    """Base tool for file system operations with sandbox validation."""

    def _validate_path(self, file_path: str) -> str:
        """
        Validates the path and returns the full, safe path.
        Raises PathOutsideSandboxError if the path is invalid.
        """
        full_path = os.path.abspath(os.path.join(SANDBOX_DIR, file_path))

        real_path = os.path.realpath(full_path)

        if not real_path.startswith(SANDBOX_DIR):
            raise PathOutsideSandboxError(
                f"Path '{file_path}' is outside the allowed /sandbox directory."
            )

        return real_path


# --- Input Schemas for Tools ---


class WriteFileInput(BaseModel):
    """Input for WriteFileTool."""

    file_path: str = Field(
        ...,
        description="The path to the file to be written, relative to the sandbox directory.",
    )
    content: str = Field(..., description="The content to write into the file.")


class ReadFileInput(BaseModel):
    """Input for ReadFileTool."""

    file_path: str = Field(
        ...,
        description="The path to the file to be read, relative to the sandbox directory.",
    )


class ListDirectoryInput(BaseModel):
    """Input for ListDirectoryTool."""

    path: str = Field(
        ...,
        description="The path of the directory to be listed, relative to the sandbox directory.",
    )


# --- Tool Implementations ---


class WriteFileTool(FileSystemBaseTool):
    name: str = "Write File"
    description: str = "Writes content to a specified file within the /sandbox directory. Creates parent directories if they don't exist."
    args_schema: Type[BaseModel] = WriteFileInput

    def _run(self, file_path: str, content: str) -> str:
        try:
            full_path = self._validate_path(file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File '{file_path}' has been written successfully."
        except (PathOutsideSandboxError, OSError) as e:
            raise FileSystemError(f"Error writing file '{file_path}': {e}") from e

    async def _arun(self, file_path: str, content: str) -> str:
        return await asyncio.to_thread(self._run, file_path=file_path, content=content)


class ReadFileTool(FileSystemBaseTool):
    name: str = "Read File"
    description: str = (
        "Reads the content of a specified file from the /sandbox directory."
    )
    args_schema: Type[BaseModel] = ReadFileInput

    def _run(self, file_path: str) -> str:
        try:
            full_path = self._validate_path(file_path)
            if not os.path.exists(full_path):
                raise FileSystemNotFoundError(f"File '{file_path}' not found.")
            if os.path.isdir(full_path):
                raise IsDirectoryError(
                    f"Path '{file_path}' is a directory, not a file."
                )

            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except (
            PathOutsideSandboxError,
            FileSystemNotFoundError,
            IsDirectoryError,
            OSError,
        ) as e:
            raise FileSystemError(f"Error reading file '{file_path}': {e}") from e

    async def _arun(self, file_path: str) -> str:
        return await asyncio.to_thread(self._run, file_path=file_path)


class ListDirectoryTool(FileSystemBaseTool):
    name: str = "List Directory"
    description: str = (
        "Lists the contents of a specified directory within the /sandbox directory."
    )
    args_schema: Type[BaseModel] = ListDirectoryInput

    def _run(self, path: str) -> List[str]:
        try:
            full_path = self._validate_path(path)
            if not os.path.exists(full_path):
                raise FileSystemNotFoundError(f"Directory '{path}' not found.")
            if not os.path.isdir(full_path):
                raise NotDirectoryError(f"Path '{path}' is not a directory.")

            entries = os.listdir(full_path)
            formatted_entries = [
                f"{entry}/" if os.path.isdir(os.path.join(full_path, entry)) else entry
                for entry in entries
            ]
            return formatted_entries
        except (
            PathOutsideSandboxError,
            FileSystemNotFoundError,
            NotDirectoryError,
            OSError,
        ) as e:
            raise FileSystemError(f"Error listing directory '{path}': {e}") from e

    async def _arun(self, path: str) -> List[str]:
        return await asyncio.to_thread(self._run, path=path)
