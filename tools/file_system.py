import os
from typing import Type, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

# Define the absolute path for the sandbox directory to ensure security
# This makes the check robust, regardless of the current working directory.
SANDBOX_DIR = os.path.abspath("sandbox")

def _is_within_sandbox(path: str) -> bool:
    """
    Checks if the given path is securely within the sandbox directory.
    Prevents directory traversal attacks (e.g., '../../etc/passwd').
    """
    # Resolve the real, absolute path of the given path. This resolves '..' and symlinks.
    absolute_path = os.path.realpath(path)
    # Check if the resolved path starts with the sandbox directory's path
    return absolute_path.startswith(SANDBOX_DIR)

# --- Input Schemas for Tools ---

class WriteFileInput(BaseModel):
    """Input for WriteFileTool."""
    file_path: str = Field(..., description="The path to the file to be written, relative to the sandbox directory.")
    content: str = Field(..., description="The content to write into the file.")

class ReadFileInput(BaseModel):
    """Input for ReadFileTool."""
    file_path: str = Field(..., description="The path to the file to be read, relative to the sandbox directory.")

class ListDirectoryInput(BaseModel):
    """Input for ListDirectoryTool."""
    path: str = Field(..., description="The path of the directory to be listed, relative to the sandbox directory.")

# --- Tool Implementations ---

class WriteFileTool(BaseTool):
    name: str = "Write File"
    description: str = "Writes content to a specified file within the /sandbox directory. Creates parent directories if they don't exist."
    args_schema: Type[BaseModel] = WriteFileInput

    def _run(self, file_path: str, content: str) -> str:
        # Construct the full path safely within the sandbox
        full_path = os.path.join(SANDBOX_DIR, file_path)

        # Security check: Ensure the path is within the sandbox
        if not _is_within_sandbox(full_path):
            return f"Error: Path '{file_path}' is outside the allowed /sandbox directory."

        try:
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File '{file_path}' has been written successfully to the sandbox."
        except Exception as e:
            return f"Error writing file: {e}"

class ReadFileTool(BaseTool):
    name: str = "Read File"
    description: str = "Reads the content of a specified file from the /sandbox directory."
    args_schema: Type[BaseModel] = ReadFileInput

    def _run(self, file_path: str) -> str:
        # Construct the full path safely within the sandbox
        full_path = os.path.join(SANDBOX_DIR, file_path)

        # Security check
        if not _is_within_sandbox(full_path):
            return f"Error: Path '{file_path}' is outside the allowed /sandbox directory."

        if not os.path.exists(full_path):
            return f"Error: File '{file_path}' not found in the sandbox."

        if os.path.isdir(full_path):
            return f"Error: Path '{file_path}' is a directory, not a file."

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"Content of '{file_path}':\n---\n{content}"
        except Exception as e:
            return f"Error reading file: {e}"

class ListDirectoryTool(BaseTool):
    name: str = "List Directory"
    description: str = "Lists the contents of a specified directory within the /sandbox directory."
    args_schema: Type[BaseModel] = ListDirectoryInput

    def _run(self, path: str) -> str:
        # Construct the full path safely within the sandbox
        full_path = os.path.join(SANDBOX_DIR, path)

        # Security check
        if not _is_within_sandbox(full_path):
            return f"Error: Path '{path}' is outside the allowed /sandbox directory."

        if not os.path.isdir(full_path):
            return f"Error: Directory '{path}' not found in the sandbox."

        try:
            entries = os.listdir(full_path)
            # Add a trailing slash to directories for clarity
            formatted_entries = [f"{entry}/" if os.path.isdir(os.path.join(full_path, entry)) else entry for entry in entries]
            if not formatted_entries:
                return f"Directory '{path}' is empty."
            return f"Contents of '{path}':\n---\n" + "\n".join(formatted_entries)
        except Exception as e:
            return f"Error listing directory: {e}"
