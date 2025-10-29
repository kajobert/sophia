import inspect
import logging
from pathlib import Path
from typing import List, Dict
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.plugin_manager import PluginManager
from typing import Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CodeReader(BasePlugin):
    """A cognitive plugin for reading and understanding the project's own source code."""

    def __init__(self):
        super().__init__()
        self.plugin_manager: PluginManager = None

    @property
    def name(self) -> str:
        return "cognitive_code_reader"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """This plugin requires access to the PluginManager to list other plugins."""
        # A proper dependency injection system will handle this in the future.
        # For now, we will pass it in a less elegant way.
        plugin_manager = config.get("plugin_manager")
        if isinstance(plugin_manager, PluginManager):
            self.plugin_manager = plugin_manager
        logger.info("Code reader tool initialized.")

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        This plugin is not directly executed; its methods are called by other
        cognitive processes.
        """
        return context

    def list_plugins(self) -> Dict[str, List[str]]:
        """Lists all registered plugins, grouped by type."""
        if not self.plugin_manager:
            return {"error": ["PluginManager not available."]}

        plugin_map: Dict[str, List[str]] = {}
        for plugin_type in PluginType:
            plugins = self.plugin_manager.get_plugins_by_type(plugin_type)
            plugin_map[plugin_type.name] = [p.name for p in plugins]
        return plugin_map

    def get_plugin_source(self, plugin_name: str) -> str:
        """
        Retrieves the full source code of a specified plugin file.

        Security Note: In a real-world scenario, this would need sandboxing.
        For this project, we assume the agent has the right to read its own code.
        """
        if not self.plugin_manager:
            return "Error: PluginManager not available."

        for plugin_type in PluginType:
            for plugin in self.plugin_manager.get_plugins_by_type(plugin_type):
                if plugin.name == plugin_name:
                    try:
                        source_file = inspect.getfile(plugin.__class__)
                        return Path(source_file).read_text(encoding="utf-8")
                    except (TypeError, FileNotFoundError) as e:
                        return f"Error retrieving source for '{plugin_name}': {e}"

        return f"Error: Plugin with name '{plugin_name}' not found."
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Gets the definitions of the tools provided by this plugin."""

        class ListPluginsArgs(BaseModel):
            pass

        return [
            {
                "type": "function",
                "function": {
                    "name": "list_plugins",
                    "description": "Lists all registered plugins, grouped by their type.",
                    "parameters": ListPluginsArgs.model_json_schema(),
                },
            }
        ]
