"""A tool plugin for integrating with Google's Jules API."""

import logging
import os
import requests
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field, HttpUrl, validator
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


# Pydantic models for Jules API data validation
class JulesSession(BaseModel):
    """Model for a Jules coding session."""
    name: str = Field(..., description="Session ID in format 'sessions/{id}'")
    title: Optional[str] = Field(None, description="Session title")
    prompt: Optional[str] = Field(None, description="Initial task prompt")
    state: Optional[str] = Field(None, description="Session state (ACTIVE, COMPLETED, etc.)")
    create_time: Optional[str] = Field(None, description="ISO timestamp of creation")
    update_time: Optional[str] = Field(None, description="ISO timestamp of last update")
    
    @validator('name')
    def validate_session_name(cls, v):
        if not v.startswith('sessions/'):
            raise ValueError("Session name must start with 'sessions/'")
        return v


class JulesSource(BaseModel):
    """Model for a Jules source repository."""
    name: str = Field(..., description="Source ID in format 'sources/github/{owner}/{repo}'")
    display_name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="Repository description")


class JulesActivity(BaseModel):
    """Model for a Jules activity within a session."""
    name: str = Field(..., description="Activity ID")
    type: Optional[str] = Field(None, description="Activity type")
    state: Optional[str] = Field(None, description="Activity state")
    create_time: Optional[str] = Field(None, description="ISO timestamp")


class JulesSessionList(BaseModel):
    """Model for list of sessions response."""
    sessions: List[JulesSession] = Field(default_factory=list)
    next_page_token: Optional[str] = None


class JulesSourceList(BaseModel):
    """Model for list of sources response."""
    sources: List[JulesSource] = Field(default_factory=list)


class CreateSessionRequest(BaseModel):
    """Model for create session request."""
    prompt: str = Field(..., min_length=1, description="Task description")
    source: str = Field(..., pattern=r"^sources/github/[\w-]+/[\w-]+$")
    branch: str = Field(default="main")
    title: Optional[str] = None
    auto_pr: bool = Field(default=False)


# Exception classes
class JulesAPIError(Exception):
    """Base exception for Jules API errors."""
    pass


class JulesAuthenticationError(JulesAPIError):
    """Exception raised for authentication failures."""
    pass


class JulesValidationError(JulesAPIError):
    """Exception raised for data validation failures."""
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
                    "name": "list_sessions",
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
                    "name": "list_sources",
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
                    "name": "create_session",
                    "description": "Creates a new Jules coding session. ⚠️ LIMIT: 100 sessions per day. Check usage with list_sessions() first!",
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
                    "name": "get_session",
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
                    "name": "send_message",
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

    def list_sources(self, context: SharedContext) -> JulesSourceList:
        """
        Lists available sources (repositories) for Jules.

        Args:
            context: The shared context for the session

        Returns:
            JulesSourceList containing validated source data

        Example:
            >>> sources = jules_tool.list_sources(context)
            >>> for source in sources.sources:
            ...     print(source.name, source.display_name)
        """
        response = self._make_request(context, "GET", "sources")
        try:
            return JulesSourceList(**response)
        except Exception as e:
            raise JulesValidationError(f"Invalid sources response: {e}")

    def create_session(
        self,
        context: SharedContext,
        prompt: str,
        source: str,
        branch: str = "main",
        title: str = "",
        auto_pr: bool = False
    ) -> JulesSession:
        """
        Creates a new Jules coding session with Pydantic validation.
        
        ⚠️ IMPORTANT: Daily limit of 100 sessions! Use list_sessions() to check usage first.

        Args:
            context: The shared context for the session
            prompt: The task description for Jules
            source: Source repository (format: "sources/github/{owner}/{repo}")
            branch: Branch name (default: "main")
            title: Session title (optional)
            auto_pr: Whether to automatically create a PR (default: False)

        Returns:
            JulesSession with validated session data

        Raises:
            JulesValidationError: If input parameters are invalid

        Example:
            >>> # Check daily usage first
            >>> sessions = jules_tool.list_sessions(context)
            >>> if len(sessions.sessions) >= 95:
            ...     context.logger.warning("Approaching daily limit!")
            >>> 
            >>> session = jules_tool.create_session(
            ...     context=context,
            ...     prompt="Add dark mode support",
            ...     source="sources/github/myorg/myapp",
            ...     title="Dark Mode Implementation",
            ...     auto_pr=True
            ... )
            >>> session_id = session.name.split("/")[1]
        """
        # Validate input using Pydantic
        try:
            request = CreateSessionRequest(
                prompt=prompt,
                source=source,
                branch=branch,
                title=title,
                auto_pr=auto_pr
            )
        except Exception as e:
            raise JulesValidationError(f"Invalid session parameters: {e}")

        # Log warning about daily limits
        context.logger.info(
            "⚠️ Creating Jules session (Daily limit: 100 sessions). Consider checking usage with list_sessions() first.",
            extra={"plugin_name": self.name}
        )
        
        data: Dict[str, Any] = {
            "prompt": request.prompt,
            "sourceContext": {
                "source": request.source,
                "githubRepoContext": {
                    "startingBranch": request.branch
                }
            }
        }

        if request.title:
            data["title"] = request.title

        if request.auto_pr:
            data["automationMode"] = "AUTO_CREATE_PR"

        response = self._make_request(context, "POST", "sessions", data=data)
        
        try:
            return JulesSession(**response)
        except Exception as e:
            raise JulesValidationError(f"Invalid session response: {e}")

    def get_session(
        self,
        context: SharedContext,
        session_id: str
    ) -> JulesSession:
        """
        Gets details about a specific session with Pydantic validation.

        Args:
            context: The shared context for the session
            session_id: The ID of the session to retrieve (can include 'sessions/' prefix)

        Returns:
            JulesSession with validated session data

        Example:
            >>> session = jules_tool.get_session(context, "abc123")
            >>> print(session.state)  # ACTIVE, COMPLETED, etc.
            >>> print(session.title)
        """
        # Handle both formats: "sessions/123" and "123"
        if session_id.startswith("sessions/"):
            endpoint = session_id
        else:
            endpoint = f"sessions/{session_id}"
            
        response = self._make_request(context, "GET", endpoint)
        try:
            return JulesSession(**response)
        except Exception as e:
            raise JulesValidationError(f"Invalid session response: {e}")

    def list_sessions(self, context: SharedContext) -> JulesSessionList:
        """
        Lists all Jules sessions with Pydantic validation.

        Args:
            context: The shared context for the session

        Returns:
            JulesSessionList containing validated session data

        Example:
            >>> sessions = jules_tool.list_sessions(context)
            >>> for session in sessions.sessions:
            ...     print(session.name, session.state, session.title)
        """
        response = self._make_request(context, "GET", "sessions")
        try:
            return JulesSessionList(**response)
        except Exception as e:
            raise JulesValidationError(f"Invalid sessions response: {e}")

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
