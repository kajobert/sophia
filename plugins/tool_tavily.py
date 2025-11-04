"""A tool plugin for integrating with Tavily AI Search API."""

import logging
import os
import requests
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field, validator
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


# Pydantic models for Tavily API data validation
class TavilySearchResult(BaseModel):
    """Model for a single Tavily search result."""

    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    content: str = Field(..., description="Content/snippet from the page")
    score: float = Field(..., description="Relevance score (0.0-1.0)")
    raw_content: Optional[str] = Field(None, description="Full raw content if requested")

    @validator("score")
    def validate_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        return v


class TavilySearchResponse(BaseModel):
    """Model for Tavily search response."""

    query: str = Field(..., description="Original search query")
    results: List[TavilySearchResult] = Field(default_factory=list)
    answer: Optional[str] = Field(None, description="AI-generated answer if requested")
    images: Optional[List[str]] = Field(None, description="Related image URLs")
    response_time: Optional[float] = Field(None, description="API response time in seconds")


class TavilySearchRequest(BaseModel):
    """Model for Tavily search request parameters."""

    query: str = Field(..., min_length=1, description="Search query")
    search_depth: Optional[str] = Field(default="basic", pattern="^(basic|advanced)$")
    max_results: Optional[int] = Field(default=5, ge=1, le=20)
    include_answer: Optional[bool] = Field(default=False)
    include_raw_content: Optional[bool] = Field(default=False)
    include_images: Optional[bool] = Field(default=False)
    include_domains: Optional[List[str]] = Field(default=None, description="Whitelist domains")
    exclude_domains: Optional[List[str]] = Field(default=None, description="Blacklist domains")


# Exception classes
class TavilyAPIError(Exception):
    """Base exception for Tavily API errors."""

    pass


class TavilyAuthenticationError(TavilyAPIError):
    """Exception raised for authentication failures."""

    pass


class TavilyValidationError(TavilyAPIError):
    """Exception raised for data validation failures."""

    pass


class TavilyRateLimitError(TavilyAPIError):
    """Exception raised when rate limit is exceeded."""

    pass


class TavilyAPITool(BasePlugin):
    """
    A tool plugin for interacting with Tavily AI Search API.

    Tavily provides AI-optimized search results with features like:
    - Deep web search with relevance scoring
    - AI-generated answers
    - Raw content extraction
    - Image search
    - Domain filtering

    API Documentation: https://docs.tavily.com/
    Base URL: https://api.tavily.com
    """

    BASE_URL = "https://api.tavily.com"

    def __init__(self) -> None:
        """Initializes the Tavily API Tool."""
        super().__init__()
        self.api_key: str = ""
        self.headers: Dict[str, str] = {}

    @property
    def name(self) -> str:
        """Gets the name of the plugin."""
        return "tool_tavily"

    @property
    def plugin_type(self) -> PluginType:
        """Gets the type of the plugin."""
        return PluginType.TOOL

    @property
    def version(self) -> str:
        """Gets the version of the plugin."""
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """
        Sets up the Tavily API client with authentication.

        Args:
            config: A dictionary containing the configuration for the plugin.
                   Expected keys: 'tavily_api_key' (can use ${ENV_VAR} syntax)
        """
        # Get API key from config (supports ${ENV_VAR} syntax)
        api_key_config = config.get("tavily_api_key", "")

        # If config contains ${ENV_VAR}, load from environment
        if api_key_config.startswith("${") and api_key_config.endswith("}"):
            env_var_name = api_key_config[2:-1]  # Extract variable name
            self.api_key = os.getenv(env_var_name, "")
        else:
            self.api_key = api_key_config

        if not self.api_key:
            logger.warning(
                "Tavily API key is not configured. Tavily search will not be available.",
                extra={"plugin_name": self.name},
            )
            return

        self.headers = {"Content-Type": "application/json"}

        logger.info("Tavily API tool initialized successfully.", extra={"plugin_name": self.name})

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        This tool is not directly executed in the main loop.
        Its methods are called by cognitive plugins.
        """
        return context

    def get_tool_definitions(self) -> list[dict]:
        """
        Returns tool definitions for the planner to understand available methods.

        Returns:
            List of tool definition dictionaries
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Performs an AI-optimized web search using Tavily. Returns highly relevant results with optional AI-generated answers.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query"},
                            "search_depth": {
                                "type": "string",
                                "description": "Search depth: 'basic' (fast) or 'advanced' (thorough)",
                                "enum": ["basic", "advanced"],
                                "default": "basic",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results (1-20)",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20,
                            },
                            "include_answer": {
                                "type": "boolean",
                                "description": "Whether to include AI-generated answer",
                                "default": False,
                            },
                            "include_raw_content": {
                                "type": "boolean",
                                "description": "Whether to include full page content",
                                "default": False,
                            },
                            "include_images": {
                                "type": "boolean",
                                "description": "Whether to include related images",
                                "default": False,
                            },
                            "include_domains": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Whitelist of domains to search (optional)",
                                "default": None,
                            },
                            "exclude_domains": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Blacklist of domains to exclude (optional)",
                                "default": None,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "extract",
                    "description": "Extracts clean content from a list of URLs using Tavily.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "urls": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of URLs to extract content from",
                            }
                        },
                        "required": ["urls"],
                    },
                },
            },
        ]

    def _make_request(
        self, context: SharedContext, endpoint: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Makes a request to the Tavily API.

        Args:
            context: The shared context for logging
            endpoint: API endpoint (relative to BASE_URL)
            data: Request body data

        Returns:
            The JSON response from the API

        Raises:
            TavilyAuthenticationError: If authentication fails
            TavilyRateLimitError: If rate limit is exceeded
            TavilyAPIError: If the API returns an error
        """
        if not self.api_key:
            raise TavilyAuthenticationError("Tavily API key is not configured.")

        url = f"{self.BASE_URL}/{endpoint}"

        # Add API key to request data
        data["api_key"] = self.api_key

        try:
            context.logger.info(
                f"Making POST request to Tavily API: {endpoint}", extra={"plugin_name": self.name}
            )

            response = requests.post(url=url, headers=self.headers, json=data, timeout=30)

            # Handle authentication errors
            if response.status_code == 401:
                raise TavilyAuthenticationError("Invalid API key.")
            elif response.status_code == 403:
                raise TavilyAuthenticationError("Access forbidden. Check API permissions.")
            elif response.status_code == 429:
                raise TavilyRateLimitError("Rate limit exceeded. Please try again later.")

            # Handle other errors
            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            raise TavilyAPIError(f"Request to {endpoint} timed out.")
        except requests.exceptions.ConnectionError as e:
            raise TavilyAPIError(f"Connection error: {str(e)}")
        except requests.exceptions.HTTPError:
            raise TavilyAPIError(f"HTTP error {response.status_code}: {response.text}")
        except Exception as e:
            context.logger.error(
                f"Unexpected error in Tavily API request: {e}",
                exc_info=True,
                extra={"plugin_name": self.name},
            )
            raise TavilyAPIError(f"Unexpected error: {str(e)}")

    def search(
        self,
        context: SharedContext,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> TavilySearchResponse:
        """
        Performs an AI-optimized web search using Tavily.

        Args:
            context: The shared context for the session
            query: The search query
            search_depth: 'basic' (fast) or 'advanced' (thorough)
            max_results: Maximum number of results (1-20)
            include_answer: Whether to include AI-generated answer
            include_raw_content: Whether to include full page content
            include_images: Whether to include related images
            include_domains: Whitelist of domains to search
            exclude_domains: Blacklist of domains to exclude

        Returns:
            TavilySearchResponse with validated search results

        Raises:
            TavilyValidationError: If input parameters are invalid

        Example:
            >>> results = tavily.search(
            ...     context=context,
            ...     query="Python async programming best practices",
            ...     search_depth="advanced",
            ...     max_results=10,
            ...     include_answer=True
            ... )
            >>> print(results.answer)  # AI-generated answer
            >>> for result in results.results:
            ...     print(f"{result.title}: {result.url}")
        """
        # Validate input using Pydantic
        try:
            request = TavilySearchRequest(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                include_images=include_images,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
            )
        except Exception as e:
            raise TavilyValidationError(f"Invalid search parameters: {e}")

        # Build request data
        data: Dict[str, Any] = {
            "query": request.query,
            "search_depth": request.search_depth,
            "max_results": request.max_results,
            "include_answer": request.include_answer,
            "include_raw_content": request.include_raw_content,
            "include_images": request.include_images,
        }

        if request.include_domains:
            data["include_domains"] = request.include_domains
        if request.exclude_domains:
            data["exclude_domains"] = request.exclude_domains

        response = self._make_request(context, "search", data)

        try:
            return TavilySearchResponse(**response)
        except Exception as e:
            raise TavilyValidationError(f"Invalid search response: {e}")

    def extract(self, context: SharedContext, urls: List[str]) -> Dict[str, Any]:
        """
        Extracts clean content from a list of URLs.

        Args:
            context: The shared context for the session
            urls: List of URLs to extract content from

        Returns:
            Dictionary containing extracted content for each URL

        Example:
            >>> content = tavily.extract(
            ...     context=context,
            ...     urls=["https://example.com/article"]
            ... )
            >>> print(content["results"][0]["raw_content"])
        """
        if not urls:
            raise TavilyValidationError("URLs list cannot be empty")

        data = {"urls": urls}
        return self._make_request(context, "extract", data)
