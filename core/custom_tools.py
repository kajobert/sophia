
import os
from crewai.tools import BaseTool

class FileEditTool(BaseTool):
    name: str = "File Edit Tool"
    description: str = "Appends content to a specified file, always starting on a new line."

    def _run(self, file_path: str, content: str) -> str:
        try:
            # Read last line to prevent duplicate appends
            last_line = None
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].rstrip('\n')
            if last_line == content:
                return f"Skipped append: last line already matches content in {file_path}."
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write('\n' + content)
            return f"Successfully appended to file: {file_path}."
        except Exception as e:
            return f"Error appending to file {file_path}: {e}"
class FileReadTool(BaseTool):
    name: str = "File Read Tool"
    description: str = "Reads content from a specified file."

    def _run(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {e}"
from crewai_tools import SerperDevTool as CrewaiSerperDevTool

class WebSearchTool(BaseTool):
    name: str = "Web Search Tool"
    description: str = "Performs a web search for a given query."
    
    def _run(self, search_query: str) -> str:
        try:
            # Správné volání s klíčovým argumentem
            results = CrewaiSerperDevTool().run(search_query=search_query)
            # Vrátíme výsledek jako text (může být JSON nebo string)
            return str(results)
        except Exception as e:
            return f"Web search failed: {e}"

class FileWriteTool(BaseTool):
    name: str = "File Write Tool"
    description: str = "Writes content to a specified file."

    def _run(self, file_path: str, content: str) -> str:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to file: {file_path}."
        except Exception as e:
            return f"Error writing to file {file_path}: {e}"