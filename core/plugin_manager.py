import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Type

from plugins.base_plugin import BasePlugin, PluginType

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages the dynamic loading, validation, and registration of all plugins.

    This class scans the specified plugin directory, identifies valid plugin
    modules, and loads them into the system. It organizes plugins by their
    `PluginType` for easy retrieval and execution.

    Attributes:
        plugin_dir: The directory where plugin modules are located.
        _plugins: A dictionary mapping each `PluginType` to a list of
                  loaded plugin instances.
    """

    def __init__(self, plugin_dir: str = "plugins"):
        """
        Initializes the PluginManager and starts the plugin loading process.

        Args:
            plugin_dir: The path to the directory containing the plugins.
                        Defaults to "plugins".
        """
        self.plugin_dir = Path(plugin_dir)
        self._plugins: Dict[PluginType, List[BasePlugin]] = {pt: [] for pt in PluginType}
        self.load_plugins()

    def load_plugins(self) -> None:
        """
        Scans the plugin directory, finds, validates, and registers all valid plugins.

        It iterates over all Python files in the plugin directory, ignoring
        special files (e.g., those starting with '_'). It imports each valid
        file as a module and inspects its members to find classes that are
        subclasses of `BasePlugin`.
        """
        logger.info(f"Scanning for plugins in directory: '{self.plugin_dir}'")
        for file_path in self.plugin_dir.glob("*.py"):
            if file_path.name.startswith("_") or file_path.name == "base_plugin.py":
                continue

            module_name = f"{self.plugin_dir.name}.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, BasePlugin)
                        and obj is not BasePlugin
                        and not inspect.isabstract(obj)
                    ):
                        self._register_plugin(obj)
            except Exception as e:
                logger.error(f"Failed to load plugin from '{file_path}': {e}")

    def _register_plugin(self, plugin_class: Type[BasePlugin]) -> None:
        """
        Initializes and registers a single plugin instance.

        This method takes a plugin class, creates an instance of it, and
        adds it to the internal `_plugins` registry, categorized by its
        `plugin_type`.

        Args:
            plugin_class: The plugin class to initialize and register.
        """
        try:
            plugin_instance = plugin_class()
            plugin_type = plugin_instance.plugin_type
            self._plugins[plugin_type].append(plugin_instance)
            logger.info(
                f"Plugin '{plugin_instance.name}' (version {plugin_instance.version}) "
                f"was successfully registered as type '{plugin_type.name}'."
            )
        except Exception as e:
            logger.error(f"Error initializing plugin '{plugin_class.__name__}': {e}")

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """
        Retrieves a list of all loaded plugins of a specific type.

        Args:
            plugin_type: The type of plugins to retrieve.

        Returns:
            A list of `BasePlugin` instances of the requested type.
            Returns an empty list if no plugins of that type are found.
        """
        return self._plugins.get(plugin_type, [])
