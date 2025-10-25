from core.plugin_manager import PluginManager
from plugins.base_plugin import PluginType


def test_plugin_manager_loads_interface_plugin():
    """
    Tests that the PluginManager correctly finds, loads, and registers
    the interface plugin.
    """
    manager = PluginManager()
    interface_plugins = manager.get_plugins_by_type(PluginType.INTERFACE)
    assert len(interface_plugins) == 1
    terminal_interface = interface_plugins[0]
    assert terminal_interface.name == "interface_terminal"
    assert terminal_interface.plugin_type == PluginType.INTERFACE
    assert terminal_interface.version == "1.0.0"
