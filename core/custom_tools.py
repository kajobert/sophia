
import os
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool as CrewaiSerperDevTool, FileReadTool as CrewaiFileReadTool

# Wrapper pro SerperDevTool
class SerperDevTool(BaseTool):
    name: str = "Web Search Tool"
    description: str = "Performs a web search using the Serper.dev service."

    def _run(self, **kwargs) -> str:
        # Accept both 'search_query' and 'query' for compatibility
        search_query = kwargs.get('search_query') or kwargs.get('query')
        if not search_query:
            return "Error: 'search_query' or 'query' argument is required."
        return CrewaiSerperDevTool().run(search_query)

# Wrapper pro FileReadTool
class FileReadTool(BaseTool):
    name: str = "File Read Tool"
    description: str = "Reads the content of a specified file."

    def _run(self, **kwargs) -> str:
        # Accept both 'file_path' and 'path' for compatibility
        file_path = kwargs.get('file_path') or kwargs.get('path')
        if not file_path:
            return "Error: 'file_path' or 'path' argument is required."
        return CrewaiFileReadTool().run(file_path)

# Naše existující custom nástroje
class CustomFileWriteTool(BaseTool):
    name: str = "Create File Tool"
    description: str = "Creates a new file with specified content."

    def _run(self, **kwargs) -> str:
        # Accept both 'file_path' and 'path' for compatibility
        file_path = kwargs.get('file_path') or kwargs.get('path')
        content = kwargs.get('content')
        if not file_path or content is None:
            return "Error: 'file_path'/'path' and 'content' arguments are required."
        try:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully created file {file_path}."
        except Exception as e:
            return f"Error creating file {file_path}: {e}"

class CustomDirectoryListTool(BaseTool):
    name: str = "List Directory Contents Tool"
    description: str = "Lists contents of a directory."

    def _run(self, **kwargs) -> str:
        # Accept both 'directory_path' and 'path' for compatibility
        directory_path = kwargs.get('directory_path') or kwargs.get('path')
        if not directory_path:
            return "Error: 'directory_path' or 'path' argument is required."
        try:
            return f"Contents of '{directory_path}': {', '.join(os.listdir(directory_path))}"
        except Exception as e:
            return f"Error listing directory {directory_path}: {e}"

class CustomFilePatchTool(BaseTool):
    name: str = "Append to File Tool"
    description: str = "Appends content to the end of a file."

    def _run(self, **kwargs) -> str:
        # Accept both 'file_path' and 'path' for compatibility
        file_path = kwargs.get('file_path') or kwargs.get('path')
        content = kwargs.get('content')
        if not file_path or content is None:
            return "Error: 'file_path'/'path' and 'content' arguments are required."
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write('\n' + content)
            return f"Successfully appended content to {file_path}."
        except Exception as e:
            return f"Error appending to file {file_path}: {e}"
