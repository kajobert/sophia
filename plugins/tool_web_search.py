from typing import List, Dict, Any, Optional

from googleapiclient.discovery import build
from pydantic import BaseModel, Field

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


class SearchArgs(BaseModel):
    """Pydantic model for arguments of the search tool."""
    query: str = Field(..., description="The search query.")
    num_results: Optional[int] = Field(5, description="The number of results to return.")


class WebSearchTool(BasePlugin):
    """A tool plugin for performing Google searches."""

    def __init__(self):
        super().__init__()
        self.api_key: str = ""
        self.cse_id: str = ""
        self.service = None

    @property
    def name(self) -> str:
        return "tool_web_search"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Initializes the Google Custom Search API client."""
        self.api_key = config.get("google_api_key", "")
        self.cse_id = config.get("google_cse_id", "")

        import logging
        if not self.api_key or not self.cse_id:
            logging.warning(
                "Google API key or CSE ID is not configured. Web search will not be available."
            )
            return

        try:
            self.service = build("customsearch", "v1", developerKey=self.api_key)
            logging.info("Web search tool initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Google Search API client: {e}", exc_info=True)

    async def execute(self, context: SharedContext) -> SharedContext:
        """This tool is not directly executed in the main loop."""
        return context

    def search(self, context: SharedContext, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a web search and returns a list of results.

        Args:
            context: The shared context for the session, providing the logger.
            query: The search query.
            num_results: The number of results to return.

        Returns:
            A list of dictionaries, where each dictionary represents a search result
            containing 'title', 'link', and 'snippet'.
        """
        if not self.service:
            context.logger.error("Web search tool is not configured.")
            return [{"error": "Web search is not configured."}]

        try:
            context.logger.info(f"Performing web search for: '{query}'")
            result = self.service.cse().list(q=query, cx=self.cse_id, num=num_results).execute()
            items = result.get("items", [])
            return [
                {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                }
                for item in items
            ]
        except Exception as e:
            context.logger.error(f"An error occurred during web search: {e}", exc_info=True)
            return [{"error": str(e)}]

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Gets the definitions of the tools provided by this plugin."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Performs a web search and returns a list of results.",
                    "parameters": SearchArgs.model_json_schema(),
                },
            }
        ]
