import os
from typing import Type
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool

SANDBOX_DIR = os.path.abspath("sandbox")

def _is_within_sandbox(path: str) -> bool:
    absolute_path = os.path.realpath(path)
    return absolute_path.startswith(SANDBOX_DIR)

class WriteFileToolInput(BaseModel):
    file_path: str = Field(..., description="The path to the file to be written, relative to the sandbox directory.")
    content: str = Field(..., description="The content to write to the file.")

class ReadFileToolInput(BaseModel):
    file_path: str = Field(..., description="The path to the file to be read, relative to the sandbox directory.")

class ListDirectoryToolInput(BaseModel):
    directory_path: str = Field(".", description="The path to the directory to list, relative to the sandbox directory.")

class WriteFileTool(BaseTool):
    name: str = "Write File"
    description: str = "Writes content to a specified file within the /sandbox directory."
    args_schema: Type[BaseModel] = WriteFileToolInput

    def execute(self, file_path: str, content: str) -> str:
        full_path = os.path.join(SANDBOX_DIR, file_path)
        if not _is_within_sandbox(full_path):
            return f"Error: Path '{file_path}' is outside the allowed /sandbox directory."
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
            return f"File '{file_path}' has been written successfully."
        except Exception as e:
            return f"Error writing to file: {e}"

class ReadFileTool(BaseTool):
    name: str = "Read File"
    description: str = "Reads the entire content of a specified file from the /sandbox directory."
    args_schema: Type[BaseModel] = ReadFileToolInput

    def execute(self, file_path: str) -> str:
        full_path = os.path.join(SANDBOX_DIR, file_path)
        if not _is_within_sandbox(full_path):
            return f"Error: Path '{file_path}' is outside the allowed /sandbox directory."
        if not os.path.exists(full_path):
            return f"Error: File '{file_path}' not found."
        try:
            with open(full_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

class ListDirectoryTool(BaseTool):
    name: str = "List Directory"
    description: str = "Lists the contents of a specified directory within the /sandbox directory."
    args_schema: Type[BaseModel] = ListDirectoryToolInput

    def execute(self, directory_path: str = ".") -> str:
        full_path = os.path.join(SANDBOX_DIR, directory_path)
        if not _is_within_sandbox(full_path):
            return f"Error: Path '{directory_path}' is outside the allowed /sandbox directory."
        if not os.path.isdir(full_path):
            return f"Error: Directory '{directory_path}' not found."
        try:
            entries = os.listdir(full_path)
            return "\\n".join(entries) if entries else "Directory is empty."
        except Exception as e:
            return f"Error listing directory: {e}"