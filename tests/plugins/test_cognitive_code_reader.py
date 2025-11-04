import pytest
from plugins.cognitive_code_reader import CodeReader
from core.plugin_manager import PluginManager


@pytest.fixture
def code_reader_plugin():
    """Fixture to provide a CodeReader instance with a mock PluginManager."""
    reader = CodeReader()
    # Create a mock PluginManager that has at least one known plugin (e.g., the reader itself)
    mock_manager = PluginManager()
    # Manually inject the mock manager into the plugin for testing
    reader.setup({"plugin_manager": mock_manager})
    return reader


def test_code_reader_list_plugins(code_reader_plugin):
    """Tests that the plugin can list all available plugins."""
    plugin_list = code_reader_plugin.list_plugins()
    assert "TOOL" in plugin_list
    assert "MEMORY" in plugin_list
    # Check if some of the plugins we've created so far are listed
    assert "tool_llm" in plugin_list["TOOL"]
    assert "memory_sqlite" in plugin_list["MEMORY"]


def test_code_reader_get_source_success(code_reader_plugin):
    """Tests retrieving the source code of an existing plugin."""
    # We test by asking for the source code of a known, simple plugin
    source_code = code_reader_plugin.get_plugin_source("interface_terminal")
    assert "class TerminalInterface(BasePlugin):" in source_code
    assert "def execute(self, context: SharedContext)" in source_code


def test_code_reader_get_source_not_found(code_reader_plugin):
    """Tests the behavior when asking for a non-existent plugin."""
    result = code_reader_plugin.get_plugin_source("non_existent_plugin")
    assert "Error: Plugin with name 'non_existent_plugin' not found" in result
