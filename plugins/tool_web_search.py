import logging
from typing import List, Dict, Any
from googleapiclient.discovery import build
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


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

        if not self.api_key or not self.cse_id:
            logger.warning(
                "Google API key or CSE ID is not configured. Web search will not be available."
            )
            return

        try:
            self.service = build("customsearch", "v1", developerKey=self.api_key)
            logger.info("Web search tool initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Google Search API client: {e}", exc_info=True)

    async def execute(self, context: SharedContext) -> SharedContext:
        """This tool is not directly executed in the main loop."""
        return context

    def search(
        self, *, context: SharedContext, query: str, num_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Performs a web search and returns a list of results.

        Args:
            context: The shared context, providing access to the logger.
            query: The search query.
            num_results: The number of results to return.

        Returns:
            A list of dictionaries, where each dictionary represents a search result
            containing 'title', 'link', 'snippet'.
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
