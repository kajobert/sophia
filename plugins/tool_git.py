from typing import Optional, List, Dict, Any

from git import Repo

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


class GitTool(BasePlugin):
    """A tool plugin for performing basic Git operations on the repository."""

    def __init__(self):
        super().__init__()
        self.repo: Optional[Repo] = None

    @property
    def name(self) -> str:
        return "tool_git"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Initializes the Git repository object."""
        try:
            # Assumes the script is run from the root of the repository
            self.repo = Repo(".", search_parent_directories=True)
            import logging

            logging.info("Git tool initialized for the current repository.")
        except Exception as e:
            import logging

            logging.error(f"Failed to initialize Git repository: {e}", exc_info=True)
            self.repo = None

    async def execute(self, context: SharedContext) -> SharedContext:
        """This tool is not directly executed in the main loop."""
        return context

    def get_status(self, context: SharedContext) -> str:
        """Returns the output of `git status`."""
        context.logger.info("Getting git status.")
        if not self.repo:
            return "Error: Git repository not initialized."
        return self.repo.git.status()

    def get_diff(self, context: SharedContext) -> str:
        """Returns the output of `git diff` for unstaged changes."""
        context.logger.info("Getting git diff.")
        if not self.repo:
            return "Error: Git repository not initialized."
        # Passing None gets the diff of the working directory vs the index
        return self.repo.git.diff(None)

    def commit(self, context: SharedContext, message: str) -> str:
        """Commits staged changes with the given message."""
        context.logger.info(f"Committing with message: {message}")
        if not self.repo:
            return "Error: Git repository not initialized."
        try:
            return self.repo.git.commit(m=message)
        except Exception as e:
            return f"Error committing changes: {e}"

    def get_current_branch(self, context: SharedContext) -> str:
        """
        Returns the name of the active branch or the commit hash if in a detached HEAD state.
        """
        context.logger.info("Getting current git branch or commit hash.")
        if not self.repo:
            return "Error: Git repository not initialized."
        try:
            return self.repo.active_branch.name
        except TypeError:
            # This occurs in a detached HEAD state
            return self.repo.head.commit.hexsha

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Gets the definitions of the tools provided by this plugin."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_status",
                    "description": "Returns the output of `git status`.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_diff",
                    "description": (
                        "Returns the output of `git diff` for staged and " "unstaged changes."
                    ),
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_branch",
                    "description": (
                        "Returns the name of the active branch or the commit hash if "
                        "in a detached HEAD state."
                    ),
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "commit",
                    "description": "Commits staged changes with the given message.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The commit message.",
                            }
                        },
                        "required": ["message"],
                    },
                },
            },
        ]
