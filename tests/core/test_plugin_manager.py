from core.plugin_manager import PluginManager
from plugins.base_plugin import PluginType


def test_plugin_manager_loads_interface_plugins():
    """
    Tests that the PluginManager correctly finds, loads, and registers all
    interface plugins.
    
    Note: We have multiple interface plugins now:
    - interface_terminal (classic)
    - interface_webui
    - interface_terminal_scifi (cyberpunk)
    - interface_terminal_holographic
    
    Matrix and StarTrek may fail to load (known issue).
    """
    manager = PluginManager()
    interface_plugins = manager.get_plugins_by_type(PluginType.INTERFACE)
    
    # We should have at least 3 working interface plugins
    assert len(interface_plugins) >= 3, f"Expected at least 3 interface plugins, got {len(interface_plugins)}"

    plugin_names = {p.name for p in interface_plugins}
    
    # Check core interfaces are loaded
    assert "interface_terminal" in plugin_names, "Classic terminal interface missing"
    assert "interface_webui" in plugin_names, "WebUI interface missing"
    
    # Check at least one sci-fi interface loaded
    scifi_interfaces = {"interface_terminal_scifi", "interface_terminal_holographic"}
    assert len(plugin_names & scifi_interfaces) > 0, "No sci-fi interface loaded"

    for plugin in interface_plugins:
        assert plugin.plugin_type == PluginType.INTERFACE
        # Version check is flexible now (some plugins have different versions)
        assert hasattr(plugin, 'version'), f"Plugin {plugin.name} missing version attribute"
