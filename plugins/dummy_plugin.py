from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


class DummyTool(BasePlugin):
    """A test plugin to verify the functionality of the PluginManager."""

    @property
    def name(self) -> str:
        """The name of the plugin."""
        return "dummy_tool"

    @property
    def plugin_type(self) -> PluginType:
        """The type of the plugin."""
        return PluginType.TOOL

    @property
    def version(self) -> str:
        """The version of the plugin."""
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Plugin setup."""
        pass

    async def execute(self, context: SharedContext) -> SharedContext:
        """Plugin execution."""
        return context
