import logging
from pathlib import Path
from typing import List, Optional

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class DependencyAnalyzer(BasePlugin):
    """A cognitive plugin for analyzing the project's software dependencies."""

    def __init__(self):
        super().__init__()
        self.root_path: Optional[Path] = None

    @property
    def name(self) -> str:
        return "cognitive_dependency_analyzer"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Sets up the path to the project's root directory."""
        # We assume the script runs from the root, so "." is the project root.
        self.root_path = Path(".").resolve()
        logger.info(
            "Dependency analyzer initialized. Project root is at" " '%s'",
            self.root_path,
        )

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        This plugin is not directly executed; its methods are called by other
        cognitive processes.
        """
        return context

    def list_dependencies(self, file: str = "requirements.in") -> List[str]:
        """
        Reads a requirements file (e.g., requirements.in, requirements-dev.in)
        and returns a list of dependencies.
        """
        if not self.root_path:
            return ["Error: Project root not configured."]

        try:
            req_file_path = self.root_path / file
            if not req_file_path.is_file():
                raise FileNotFoundError(f"Requirement file not found: {req_file_path}")

            with open(req_file_path, "r", encoding="utf-8") as f:
                # Filter out comments and empty lines
                dependencies = [
                    line.strip() for line in f if line.strip() and not line.strip().startswith("#")
                ]
            return dependencies
        except FileNotFoundError as e:
            logger.error(f"Error reading dependency file '{file}': {e}", exc_info=True)
            return [f"Error: Requirement file not found: '{file}'"]
        except Exception as e:
            logger.error(f"Error reading dependency file '{file}': {e}", exc_info=True)
            return [f"Error: Could not read file '{file}'."]
