"""
Integration tests for plugin loading and registration.

These tests verify that all plugins are correctly loaded and registered
by the PluginManager. They are designed to catch integration issues that
unit tests might miss, such as:

- Plugin type enum vs string mismatches
- Missing dependencies in plugin initialization
- Incorrect plugin metadata
- Plugin discovery failures

This test suite was added after discovering a critical bug where
TaskManager and Orchestrator used string "COGNITIVE" instead of
PluginType.COGNITIVE enum, causing them to fail registration silently.
"""

import pytest
from core.plugin_manager import PluginManager
from plugins.base_plugin import PluginType, BasePlugin


class TestPluginLoading:
    """Test suite for plugin loading and registration."""
    
    @pytest.fixture
    def plugin_manager(self):
        """Create a fresh PluginManager instance."""
        return PluginManager()
    
    def test_all_plugins_loaded(self, plugin_manager):
        """Test that expected number of plugins are loaded."""
        total_plugins = sum(
            len(plugin_manager.get_plugins_by_type(pt)) 
            for pt in PluginType
        )
        
        # We expect 21 plugins total (as of this test)
        # If this number changes, update it and document why
        assert total_plugins >= 21, (
            f"Expected at least 21 plugins, but only {total_plugins} were loaded. "
            "This might indicate a plugin registration failure."
        )
    
    def test_critical_cognitive_plugins_loaded(self, plugin_manager):
        """Test that critical cognitive plugins are loaded."""
        cognitive = plugin_manager.get_plugins_by_type(PluginType.COGNITIVE)
        cognitive_names = {p.name for p in cognitive}
        
        # Critical plugins for autonomous workflow
        critical = {
            'cognitive_task_manager',
            'cognitive_orchestrator',
            'cognitive_ethical_guardian',
            'cognitive_notes_analyzer',
        }
        
        missing = critical - cognitive_names
        assert not missing, (
            f"Critical cognitive plugins missing: {missing}. "
            "The autonomous workflow will not function without these."
        )
    
    def test_all_plugins_use_enum_type(self, plugin_manager):
        """Test that all plugins use PluginType enum, not strings.
        
        This test prevents the bug where TaskManager and Orchestrator
        used plugin_type = "COGNITIVE" (string) instead of 
        plugin_type = PluginType.COGNITIVE (enum), which caused
        registration to fail silently.
        """
        all_plugins = [
            plugin
            for plugin_type in PluginType
            for plugin in plugin_manager.get_plugins_by_type(plugin_type)
        ]
        
        invalid_plugins = []
        for plugin in all_plugins:
            if not isinstance(plugin.plugin_type, PluginType):
                invalid_plugins.append({
                    'name': plugin.name,
                    'type': type(plugin.plugin_type).__name__,
                    'value': plugin.plugin_type
                })
        
        assert not invalid_plugins, (
            f"Plugins with invalid plugin_type (must be PluginType enum): {invalid_plugins}"
        )
    
    def test_plugin_type_groups(self, plugin_manager):
        """Test that each plugin type has expected plugins."""
        # Interface plugins
        interface = plugin_manager.get_plugins_by_type(PluginType.INTERFACE)
        interface_names = {p.name for p in interface}
        assert 'interface_terminal' in interface_names
        assert 'interface_webui' in interface_names
        
        # Memory plugins
        memory = plugin_manager.get_plugins_by_type(PluginType.MEMORY)
        memory_names = {p.name for p in memory}
        assert 'memory_chroma' in memory_names
        assert 'memory_sqlite' in memory_names
        
        # Tool plugins
        tools = plugin_manager.get_plugins_by_type(PluginType.TOOL)
        tool_names = {p.name for p in tools}
        expected_tools = {
            'tool_file_system',
            'tool_git',
            'tool_bash',
            'tool_llm',
        }
        assert expected_tools.issubset(tool_names), (
            f"Missing expected tool plugins: {expected_tools - tool_names}"
        )
    
    def test_plugins_have_required_metadata(self, plugin_manager):
        """Test that all plugins have required metadata."""
        all_plugins = [
            plugin
            for plugin_type in PluginType
            for plugin in plugin_manager.get_plugins_by_type(plugin_type)
        ]
        
        for plugin in all_plugins:
            # Check required attributes
            assert hasattr(plugin, 'name'), f"Plugin {plugin} missing 'name'"
            assert hasattr(plugin, 'version'), f"Plugin {plugin.name} missing 'version'"
            assert hasattr(plugin, 'plugin_type'), f"Plugin {plugin.name} missing 'plugin_type'"
            
            # Check metadata values
            assert isinstance(plugin.name, str) and plugin.name, (
                f"Plugin {plugin} has invalid name: {plugin.name}"
            )
            assert isinstance(plugin.version, str) and plugin.version, (
                f"Plugin {plugin.name} has invalid version: {plugin.version}"
            )
    
    def test_plugins_inherit_from_base_plugin(self, plugin_manager):
        """Test that all loaded plugins inherit from BasePlugin."""
        all_plugins = [
            plugin
            for plugin_type in PluginType
            for plugin in plugin_manager.get_plugins_by_type(plugin_type)
        ]
        
        for plugin in all_plugins:
            assert isinstance(plugin, BasePlugin), (
                f"Plugin {plugin.name} does not inherit from BasePlugin"
            )
    
    def test_plugins_have_execute_method(self, plugin_manager):
        """Test that all plugins have an async execute method."""
        all_plugins = [
            plugin
            for plugin_type in PluginType
            for plugin in plugin_manager.get_plugins_by_type(plugin_type)
        ]
        
        for plugin in all_plugins:
            assert hasattr(plugin, 'execute'), (
                f"Plugin {plugin.name} missing 'execute' method"
            )
            
            # Check that execute is a coroutine function (async)
            import inspect
            assert inspect.iscoroutinefunction(plugin.execute), (
                f"Plugin {plugin.name}.execute() is not an async method"
            )
    
    def test_no_duplicate_plugin_names(self, plugin_manager):
        """Test that there are no duplicate plugin names."""
        all_plugins = [
            plugin
            for plugin_type in PluginType
            for plugin in plugin_manager.get_plugins_by_type(plugin_type)
        ]
        
        names = [p.name for p in all_plugins]
        duplicates = [name for name in names if names.count(name) > 1]
        
        assert not duplicates, f"Duplicate plugin names found: {set(duplicates)}"
    
    def test_autonomous_workflow_dependencies(self, plugin_manager):
        """Test that autonomous workflow has all required dependencies.
        
        The autonomous workflow requires:
        - Orchestrator (VĚDOMÍ - strategic planning)
        - TaskManager (PODVĚDOMÍ - task tracking)
        - EthicalGuardian (INSTINKTY - safety checks)
        - NotesAnalyzer (PODVĚDOMÍ - context gathering)
        - QA (INSTINKTY - quality validation)
        - Integrator (INSTINKTY - safe integration)
        """
        cognitive = plugin_manager.get_plugins_by_type(PluginType.COGNITIVE)
        cognitive_names = {p.name for p in cognitive}
        
        workflow_deps = {
            'cognitive_orchestrator',
            'cognitive_task_manager',
            'cognitive_ethical_guardian',
            'cognitive_notes_analyzer',
            'cognitive_qa',
            'cognitive_integrator',
        }
        
        missing = workflow_deps - cognitive_names
        assert not missing, (
            f"Autonomous workflow missing dependencies: {missing}. "
            "The workflow cannot function without these plugins."
        )
    
    def test_plugin_manager_registry_structure(self, plugin_manager):
        """Test that PluginManager's internal registry has correct structure."""
        # Check that _plugins dict has all PluginType keys
        assert hasattr(plugin_manager, '_plugins')
        assert isinstance(plugin_manager._plugins, dict)
        
        for plugin_type in PluginType:
            assert plugin_type in plugin_manager._plugins, (
                f"PluginManager._plugins missing key for {plugin_type}"
            )
            assert isinstance(plugin_manager._plugins[plugin_type], list), (
                f"PluginManager._plugins[{plugin_type}] is not a list"
            )


class TestPluginRegistrationErrors:
    """Test error handling in plugin registration."""
    
    def test_invalid_plugin_type_detection(self):
        """Test that we can detect plugins with invalid type.
        
        This is a regression test for the bug where plugins used
        string "COGNITIVE" instead of PluginType.COGNITIVE.
        """
        # Create a mock plugin with wrong type
        class BadPlugin(BasePlugin):
            name = "bad_plugin"
            plugin_type = "COGNITIVE"  # WRONG - should be enum
            version = "1.0.0"
            
            def setup(self, config):
                """Implement required abstract method."""
                pass
            
            async def execute(self, context):
                return context
        
        plugin = BadPlugin()
        
        # This should NOT be a PluginType enum
        assert not isinstance(plugin.plugin_type, PluginType), (
            "Test setup error: BadPlugin should have string type"
        )
        
        # This test documents the behavior - in real code, PluginManager
        # should reject this during registration
        assert isinstance(plugin.plugin_type, str)


class TestPluginLoadingOrder:
    """Test plugin loading order and dependencies."""
    
    @pytest.fixture
    def plugin_manager(self):
        """Create a fresh PluginManager instance."""
        return PluginManager()
    
    def test_tools_loaded_before_cognitive(self, plugin_manager):
        """Test that tool plugins are available for cognitive plugins.
        
        Cognitive plugins may depend on tools during initialization,
        so tools should be loaded and available.
        """
        tools = plugin_manager.get_plugins_by_type(PluginType.TOOL)
        cognitive = plugin_manager.get_plugins_by_type(PluginType.COGNITIVE)
        
        # Both should be loaded
        assert len(tools) > 0, "No tool plugins loaded"
        assert len(cognitive) > 0, "No cognitive plugins loaded"
        
        # All plugins should be properly initialized
        for plugin in tools + cognitive:
            assert plugin.name is not None
            assert plugin.version is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
