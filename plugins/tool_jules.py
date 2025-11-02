"""A tool plugin for integrating with Google's Jules API."""

import logging
import os
import requests
from typing import Any, Dict, Optional
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class JulesAPIError(Exception):
    """Base exception for Jules API errors."""
    pass


class JulesAuthenticationError(JulesAPIError):
    """Exception raised for authentication failures."""
    pass


class JulesAPITool(BasePlugin):
    """
    A tool plugin for interacting with Google's Jules API.
    
    Jules is Google's AI-powered coding assistant API that can create
    complete applications, modify code, and work with GitHub repositories.
    
    API Documentation: https://developers.google.com/jules/api
    Base URL: https://jules.googleapis.com/v1alpha
    """

    BASE_URL = "https://jules.googleapis.com/v1alpha"

    def __init__(self) -> None:
        """Initializes the Jules API Tool."""
        super().__init__()
        self.api_key: str = ""
        self.headers: Dict[str, str] = {}

    @property
    def name(self) -> str:
        """Gets the name of the plugin."""
        return "tool_jules"

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
        Sets up the Jules API client with authentication.

        Args:
            config: A dictionary containing the configuration for the plugin.
                   Expected keys: 'jules_api_key' (can use ${ENV_VAR} syntax)
        """
        # Get API key from config (supports ${ENV_VAR} syntax)
        api_key_config = config.get("jules_api_key", "")
        
        # If config contains ${ENV_VAR}, load from environment
        if api_key_config.startswith("${") and api_key_config.endswith("}"):
            env_var_name = api_key_config[2:-1]  # Extract variable name
            self.api_key = os.getenv(env_var_name, "")
        else:
            self.api_key = api_key_config

        if not self.api_key:
            logger.warning(
                "Jules API key is not configured. Jules API will not be available.",
                extra={"plugin_name": self.name}
            )
            return

        self.headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key
        }
        
        logger.info(
            "Jules API tool initialized successfully.",
            extra={"plugin_name": self.name}
        )

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
                    "name": "tool_jules.list_sessions",
                    "description": "Lists all Jules coding sessions for the authenticated user.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tool_jules.list_sources",
                    "description": "Lists all available source repositories that can be used with Jules.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tool_jules.create_session",
                    "description": "Creates a new Jules coding session with specified parameters.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The task description for Jules (e.g., 'Create a Flask hello world app')"
                            },
                            "source": {
                                "type": "string",
                                "description": "Source repository in format 'sources/github/{owner}/{repo}'"
                            },
                            "branch": {
                                "type": "string",
                                "description": "Branch name (default: 'main')",
                                "default": "main"
                            },
                            "title": {
                                "type": "string",
                                "description": "Session title (optional)"
                            },
                            "auto_pr": {
                                "type": "boolean",
                                "description": "Whether to automatically create a pull request (default: false)",
                                "default": False
                            }
                        },
                        "required": ["prompt", "source"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tool_jules.get_session",
                    "description": "Gets details about a specific Jules session.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "The ID of the session to retrieve"
                            }
                        },
                        "required": ["session_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "tool_jules.send_message",
                    "description": "Sends a follow-up message to an existing Jules session.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "The ID of the session"
                            },
                            "prompt": {
                                "type": "string",
                                "description": "The follow-up instruction or question"
                            }
                        },
                        "required": ["session_id", "prompt"]
                    }
                }
            }
        ]

    def _make_request(
        self,
        context: SharedContext,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Makes a request to the Jules API.

        Args:
            context: The shared context for logging
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to BASE_URL)
            data: Optional request body data

        Returns:
            The JSON response from the API

        Raises:
            JulesAuthenticationError: If authentication fails
            JulesAPIError: If the API returns an error
        """
        if not self.api_key:
            raise JulesAuthenticationError("Jules API key is not configured.")

        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            context.logger.info(
                f"Making {method} request to Jules API: {endpoint}",
                extra={"plugin_name": self.name}
            )
            
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise JulesAuthenticationError("Invalid API key.")
            elif response.status_code == 403:
                raise JulesAuthenticationError("Access forbidden. Check API permissions.")
            
            # Handle other errors
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise JulesAPIError(f"Request to {endpoint} timed out.")
        except requests.exceptions.ConnectionError as e:
            raise JulesAPIError(f"Connection error: {str(e)}")
        except requests.exceptions.HTTPError as e:
            raise JulesAPIError(f"HTTP error {response.status_code}: {response.text}")
        except Exception as e:
            context.logger.error(
                f"Unexpected error in Jules API request: {e}",
                exc_info=True,
                extra={"plugin_name": self.name}
            )
            raise JulesAPIError(f"Unexpected error: {str(e)}")

    def list_sources(self, context: SharedContext) -> Dict[str, Any]:
        """
        Lists available sources (repositories) for Jules.

        Args:
            context: The shared context for the session

        Returns:
            Dictionary containing list of available sources

        Example:
            >>> sources = jules_tool.list_sources(context)
            >>> print(sources)
        """
        return self._make_request(context, "GET", "sources")

    def create_session(
        self,
        context: SharedContext,
        prompt: str,
        source: str,
        branch: str = "main",
        title: str = "",
        auto_pr: bool = False
    ) -> Dict[str, Any]:
        """
        Creates a new Jules coding session.

        Args:
            context: The shared context for the session
            prompt: The task description for Jules
            source: Source repository (format: "sources/github/{owner}/{repo}")
            branch: Branch name (default: "main")
            title: Session title (optional)
            auto_pr: Whether to automatically create a PR (default: False)

        Returns:
            Dictionary containing session information including session ID

        Example:
            >>> session = jules_tool.create_session(
            ...     context=context,
            ...     prompt="Add dark mode support",
            ...     source="sources/github/myorg/myapp",
            ...     title="Dark Mode Implementation",
            ...     auto_pr=True
            ... )
            >>> session_id = session["name"].split("/")[1]
        """
        data: Dict[str, Any] = {
            "prompt": prompt,
            "sourceContext": {
                "source": source,
                "githubRepoContext": {
                    "startingBranch": branch
                }
            }
        }

        if title:
            data["title"] = title

        if auto_pr:
            data["automationMode"] = "AUTO_CREATE_PR"

        return self._make_request(context, "POST", "sessions", data=data)

    def get_session(
        self,
        context: SharedContext,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Gets details about a specific session.

        Args:
            context: The shared context for the session
            session_id: The ID of the session to retrieve

        Returns:
            Dictionary containing session details

        Example:
            >>> session = jules_tool.get_session(context, "abc123")
            >>> print(session["state"])  # ACTIVE, COMPLETED, etc.
        """
        return self._make_request(context, "GET", f"sessions/{session_id}")

    def list_sessions(self, context: SharedContext) -> Dict[str, Any]:
        """
        Lists all Jules sessions.

        Args:
            context: The shared context for the session

        Returns:
            Dictionary containing list of sessions

        Example:
            >>> sessions = jules_tool.list_sessions(context)
            >>> for session in sessions.get("sessions", []):
            ...     print(session["name"], session["state"])
        """
        return self._make_request(context, "GET", "sessions")

    def send_message(
        self,
        context: SharedContext,
        session_id: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Sends a follow-up message to an existing session.

        Args:
            context: The shared context for the session
            session_id: The ID of the session
            prompt: The follow-up instruction or question

        Returns:
            Dictionary containing the response

        Example:
            >>> response = jules_tool.send_message(
            ...     context=context,
            ...     session_id="abc123",
            ...     prompt="Also add error logging"
            ... )
        """
        data = {"prompt": prompt}
        return self._make_request(
            context,
            "POST",
            f"sessions/{session_id}:sendMessage",
            data=data
        )

    def get_activity(
        self,
        context: SharedContext,
        session_id: str,
        activity_id: str
    ) -> Dict[str, Any]:
        """
        Gets details about a specific activity within a session.

        Args:
            context: The shared context for the session
            session_id: The ID of the session
            activity_id: The ID of the activity

        Returns:
            Dictionary containing activity details

        Example:
            >>> activity = jules_tool.get_activity(
            ...     context=context,
            ...     session_id="abc123",
            ...     activity_id="xyz789"
            ... )
        """
        return self._make_request(
            context,
            "GET",
            f"sessions/{session_id}/activities/{activity_id}"
        )
