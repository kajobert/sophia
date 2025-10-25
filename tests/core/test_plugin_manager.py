from core.plugin_manager import PluginManager
from plugins.base_plugin import PluginType


def test_plugin_manager_loads_interface_plugins():
    """
    Tests that the PluginManager correctly finds, loads, and registers all
    interface plugins.
    """
    manager = PluginManager()
    interface_plugins = manager.get_plugins_by_type(PluginType.INTERFACE)
    assert len(interface_plugins) == 2

    plugin_names = {p.name for p in interface_plugins}
    assert "interface_terminal" in plugin_names
    assert "interface_webui" in plugin_names

    for plugin in interface_plugins:
        assert plugin.plugin_type == PluginType.INTERFACE
        assert plugin.version == "1.0.0"
