


import os
import json
import requests
from crewai.tools import BaseTool

# --- Helper Function to read config ---
def get_tool_config():
    with open('tool_config.json', 'r') as f:
        return json.load(f)

# --- Nástroje upravené pro čtení z configu ---


class WebSearchTool(BaseTool):
    name: str = "Web Search Tool"
    description: str = "Performs a web search using the Serper.dev API based on the query in tool_config.json."

    def __init__(self):
        super().__init__(name="Web Search Tool", description="Performs a web search using the Serper.dev API based on the query in tool_config.json.")

    def _run(self, *args, **kwargs) -> str:
        try:
            config = get_tool_config()
            search_query = config.get('search_query')
            api_key = os.getenv("SERPER_API_KEY")

            if not search_query:
                return "Error: 'search_query' not found in tool_config.json."
            if not api_key:
                return "Error: SERPER_API_KEY not found in environment variables."

            url = "https://google.serper.dev/search"
            payload = json.dumps({"q": search_query})
            headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
            
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status() # Raise an exception for bad status codes
            
            results = response.json()
            # Zpracujeme a vrátíme jen nejdůležitější informace
            snippets = [item.get('snippet', '') for item in results.get('organic', [])]
            return "Search results: " + " | ".join(snippets[:5])

        except Exception as e:
            return f"Error during web search: {e}"


class CreateReportTool(BaseTool):
    def __init__(self):
        super().__init__(name="Create Report Tool", description="Creates a new report file with specified content.")

    def _run(self, *args, **kwargs) -> str:
        content_to_write = ""
        if 'content' in kwargs:
            content_to_write = kwargs['content']
        elif args:
            content_to_write = args[0]
        else:
            return "Error: No content provided to write."

        if isinstance(content_to_write, dict):
            content_to_write = content_to_write.get('content') or content_to_write.get('text') or str(content_to_write)
        
        config = get_tool_config()
        file_path = config.get('report_file_path')
        if not file_path:
            return "Error: 'report_file_path' not found in tool_config.json."
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(content_to_write))
            return f"Successfully created report file: {file_path}."
        except Exception as e:
            return f"Error creating file {file_path}: {e}"
