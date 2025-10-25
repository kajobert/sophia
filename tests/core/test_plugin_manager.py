from core.plugin_manager import PluginManager
from plugins.base_plugin import PluginType


def test_plugin_manager_loads_dummy_plugin():
    """
    Tests that the PluginManager correctly finds, loads, and registers the dummy plugin.
    """
    manager = PluginManager()
    tool_plugins = manager.get_plugins_by_type(PluginType.TOOL)
    assert len(tool_plugins) == 1
    dummy_tool = tool_plugins[0]
    assert dummy_tool.name == "dummy_tool"
    assert dummy_tool.plugin_type == PluginType.TOOL
    assert dummy_tool.version == "1.0.0"
