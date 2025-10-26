import logging
from typing import Optional

from git import Repo

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


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
            self.repo = Repo(".")
            logger.info("Git tool initialized for the current repository.")
        except Exception as e:
            logger.error(f"Failed to initialize Git repository: {e}", exc_info=True)
            self.repo = None

    async def execute(self, context: SharedContext) -> SharedContext:
        """This tool is not directly executed in the main loop."""
        return context

    def get_status(self) -> str:
        """Returns the output of `git status`."""
        if not self.repo:
            return "Error: Git repository not initialized."
        return self.repo.git.status()

    def get_diff(self) -> str:
        """Returns the output of `git diff` for staged and unstaged changes."""
        if not self.repo:
            return "Error: Git repository not initialized."
        return self.repo.git.diff()

    def get_current_branch(self) -> str:
        """Returns the name of the active branch."""
        if not self.repo:
            return "Error: Git repository not initialized."
        return self.repo.active_branch.name
