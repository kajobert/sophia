import logging
from pathlib import Path
from typing import List, Optional
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class DocReader(BasePlugin):
    """A cognitive plugin for reading and understanding the project's documentation."""

    def __init__(self):
        super().__init__()
        self.docs_path: Optional[Path] = None

    @property
    def name(self) -> str:
        return "cognitive_doc_reader"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Sets up the path to the documentation directory."""
        docs_dir = config.get("docs_dir", "docs")
        self.docs_path = Path(docs_dir).resolve()
        if not self.docs_path.is_dir():
            logger.warning(
                "Documentation directory not found at '%s'. " "This plugin may not work.",
                self.docs_path,
            )
        else:
            logger.info(
                "Doc reader tool initialized. Documentation root is at" " '%s'",
                self.docs_path,
            )

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        This plugin is not directly executed; its methods are called by other
        cognitive processes.
        """
        return context

    def read_document(self, doc_path: str) -> str:
        """
        Reads the content of a specific document file within the /docs directory.
        The path should be relative to the /docs directory
        (e.g., "en/03_TECHNICAL_ARCHITECTURE.md").
        """
        if not self.docs_path:
            return "Error: Documentation directory not configured."
        try:
            # For security, ensure the path is relative and does not traverse up
            safe_path = (self.docs_path / doc_path).resolve()
            if self.docs_path not in safe_path.parents and safe_path != self.docs_path:
                raise PermissionError("Accessing files outside the docs directory is forbidden.")
            return safe_path.read_text(encoding="utf-8")
        except (FileNotFoundError, PermissionError) as e:
            return f"Error reading document '{doc_path}': {e}"
        except Exception as e:
            logger.error(f"Unexpected error reading document '{doc_path}': {e}", exc_info=True)
            return f"An unexpected error occurred while reading '{doc_path}'."

    def list_all_documents(self) -> List[str]:
        """
        Lists all Markdown documents within the /docs directory, returning their
        relative paths.
        """
        if not self.docs_path or not self.docs_path.is_dir():
            return ["Error: Documentation directory not found."]
        all_files = self.docs_path.rglob("*.md")
        # Return paths relative to the docs directory
        return [str(f.relative_to(self.docs_path)) for f in all_files]
