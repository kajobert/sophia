import os
from crewai_tools import BaseTool

class CustomFileWriteTool(BaseTool):
    name: str = "File Write Tool"
    description: str = "Writes content to a specified file. Use this to create new files or overwrite existing ones."

    def _run(self, file_path: str, content: str) -> str:
        try:
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote {len(content)} characters to {file_path}."
        except Exception as e:
            return f"Error writing to file {file_path}: {e}"

# NOVÝ NÁSTROJ PŘIDANÝ ZDE
class CustomDirectoryListTool(BaseTool):
    name: str = "List Directory Contents Tool"
    description: str = "Lists all files and subdirectories within a specified directory."

    def _run(self, directory_path: str) -> str:
        try:
            if not os.path.isdir(directory_path):
                return f"Error: The path '{directory_path}' is not a valid directory."

            contents = os.listdir(directory_path)
            if not contents:
                return f"The directory '{directory_path}' is empty."

            return f"Contents of '{directory_path}': {', '.join(contents)}"
        except Exception as e:
            return f"Error listing directory {directory_path}: {e}"
