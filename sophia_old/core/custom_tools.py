import os
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from crewai_tools import SerperDevTool as CrewaiSerperDevTool
from memory.long_term_memory import LongTermMemory

# --- State for session-based deduplication ---
_last_read_path = None
_last_write = (None, None)

# --- Tool Classes ---


class FileReadTool(BaseTool):
    name: str = "FileReadTool"
    description: str = "Reads content from a specified file."

    def _run(self, file_path: str) -> str:
        """Reads content from a specified file."""
        global _last_read_path
        if file_path == _last_read_path:
            return f"Skipped: FileReadTool already read {file_path} in this session."
        _last_read_path = file_path
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {e}"


class FileWriteToolSchema(BaseModel):
    file_path: str = Field(..., description="The path to the file to write to.")
    content: str = Field(..., description="The content to write to the file.")


class FileWriteTool(BaseTool):
    name: str = "FileWriteTool"
    description: str = (
        "Writes content to a specified file. Overwrites existing content."
    )
    args_schema: type[BaseModel] = FileWriteToolSchema

    def _run(self, file_path: str, content: str) -> str:
        """Writes content to a specified file."""
        global _last_write
        if (file_path, content) == _last_write:
            return f"Skipped: FileWriteTool already wrote same content to {file_path} in this session."
        _last_write = (file_path, content)
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to file: {file_path}."
        except Exception as e:
            return f"Error writing to file {file_path}: {e}"


class FileEditToolSchema(BaseModel):
    file_path: str = Field(..., description="The path to the file to edit.")
    content: str = Field(..., description="The content to append to the file.")


class FileEditTool(BaseTool):
    name: str = "FileEditTool"
    description: str = (
        "Appends content to a specified file, always starting on a new line."
    )
    args_schema: type[BaseModel] = FileEditToolSchema

    def _run(self, file_path: str, content: str) -> str:
        """Appends content to a specified file."""
        try:
            last_line = None
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].rstrip("\n")
            if last_line == content:
                return (
                    f"Skipped append: last line already matches content in {file_path}."
                )

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write("\n" + content)
            return f"Successfully appended to file: {file_path}."
        except Exception as e:
            return f"Error appending to file {file_path}: {e}"


class DirectoryListingTool(BaseTool):
    name: str = "DirectoryListingTool"
    description: str = "Lists the contents of a specified directory."

    def _run(self, directory_path: str = ".") -> str:
        """Lists the contents of a specified directory."""
        try:
            return str(os.listdir(directory_path))
        except FileNotFoundError:
            return f"Error: Directory '{directory_path}' not found."
        except Exception as e:
            return f"An error occurred while reading the directory: {e}"


class DirectoryCreationTool(BaseTool):
    name: str = "DirectoryCreationTool"
    description: str = "Creates a new directory at the specified path."

    def _run(self, directory_path: str) -> str:
        """Creates a new directory."""
        try:
            os.makedirs(directory_path, exist_ok=True)
            return (
                f"Directory '{directory_path}' created successfully or already exists."
            )
        except OSError as e:
            return f"Failed to create directory '{directory_path}': {e}"
        except Exception as e:
            return f"An unexpected error occurred while creating directory '{directory_path}': {e}"


class MemoryInspectionTool(BaseTool):
    name: str = "MemoryInspectionTool"
    description: str = "Displays the entire content of the long-term memory (LTM)."

    def _run(self) -> str:
        """Displays the content of the LTM."""
        try:
            import asyncio

            # Ensure there's a running event loop
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            ltm = LongTermMemory()
            all_documents = ltm.collection.get(include=["documents", "metadatas"])
            if all_documents and all_documents.get("documents"):
                formatted_output = "Long-Term Memory (LTM) Content:\n"
                for i, doc in enumerate(all_documents["documents"]):
                    metadata = all_documents["metadatas"][i]
                    formatted_output += f"--- Document {i+1} ---\n"
                    formatted_output += f"Content: {doc}\n"
                    formatted_output += f"Metadata: {metadata}\n"
                    formatted_output += "---------------------\n"
                return formatted_output
            else:
                return "Long-term memory (LTM) is empty or contains no documents."
        except Exception as e:
            return f"Error during memory inspection: {e}"


class WebSearchTool(BaseTool):
    name: str = "WebSearchTool"
    description: str = "Performs a web search for a given query using Serper."

    def _run(self, search_query: str) -> str:
        """Performs a web search."""
        try:
            # Note: CrewaiSerperDevTool is instantiated here directly
            tool = CrewaiSerperDevTool()
            return tool.run(search_query=search_query)
        except Exception as e:
            return f"Web search failed: {e}"


from memory.episodic_memory import EpisodicMemory


class EpisodicMemoryReaderTool(BaseTool):
    name: str = "EpisodicMemoryReaderTool"
    description: str = "Reads and returns all events from the episodic (SQLite) memory."

    def _run(self) -> str:
        """Reads all events from the episodic memory."""
        try:
            memory = EpisodicMemory()
            conn = memory.conn
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY timestamp DESC")
            rows = cursor.fetchall()

            if not rows:
                return "Episodic memory is empty."

            column_names = [description[0] for description in cursor.description]

            formatted_output = "Episodic Memory Content:\n---\n"
            for row in rows:
                row_dict = dict(zip(column_names, row))
                for key, value in row_dict.items():
                    formatted_output += f"{key}: {value}\n"
                formatted_output += "---\n"

            return formatted_output
        except Exception as e:
            return f"Error reading from episodic memory: {e}"
