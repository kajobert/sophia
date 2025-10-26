import asyncio
from unittest.mock import MagicMock, AsyncMock
import pytest
from core.kernel import Kernel
from plugins.base_plugin import PluginType


import logging
from core.context import SharedContext
from plugins.base_plugin import BasePlugin

@pytest.mark.asyncio
async def test_kernel_uses_interface_plugin():
    """
    Tests that the Kernel calls the `execute` method on a loaded interface
    plugin.
    """
    kernel = Kernel()

    # Replace the actual plugin with a mock to track its calls
    mock_plugin = MagicMock()
    mock_plugin.execute = AsyncMock(return_value=SharedContext(
        session_id="test",
        current_state="LISTENING",
        user_input="",
        logger=logging.getLogger()
    ))

    # Manually insert the mock plugin into the plugin manager
    kernel.plugin_manager._plugins[PluginType.INTERFACE] = [mock_plugin]

    # Run the loop for a very short time and then cancel it
    main_task = asyncio.create_task(kernel.consciousness_loop())
    await asyncio.sleep(0.01)
    main_task.cancel()

    # Wait for the task to finish and verify that the `execute` method was called
    try:
        await main_task
    except asyncio.CancelledError:
        pass  # Expected termination

    mock_plugin.execute.assert_called_once()

@pytest.mark.asyncio
async def test_kernel_planning_and_executing_phases():
    """Test that the Kernel correctly runs the PLANNING and EXECUTING phases."""
    kernel = Kernel()

    # Mock plugins
    mock_interface = AsyncMock(spec=BasePlugin)
    mock_planner = AsyncMock(spec=BasePlugin)
    mock_tool = MagicMock()

    # Simulate interface returning user input
    mock_interface.execute.return_value = SharedContext(
        session_id="test", current_state="LISTENING", user_input="test input", logger=logging.getLogger()
    )

    # Simulate planner returning a plan
    plan = [{"tool_name": "mock_tool", "method_name": "do_something", "arguments": {"arg1": "value1"}}]
    mock_planner.execute.return_value = SharedContext(
        session_id="test", current_state="PLANNING", user_input="test input", logger=logging.getLogger(), payload={"plan": plan}
    )

    # Configure the mock tool
    mock_tool.name = "mock_tool"
    mock_tool.do_something.return_value = "done"

    # Configure plugin manager
    def get_plugins_by_type(plugin_type):
        if plugin_type == PluginType.INTERFACE:
            return [mock_interface]
        if plugin_type == PluginType.COGNITIVE:
            # Important: Give the planner a name so the Kernel can find it
            mock_planner.name = "cognitive_planner"
            return [mock_planner]
        if plugin_type == PluginType.TOOL:
            return [mock_tool]
        return []

    kernel.plugin_manager.get_plugins_by_type = MagicMock(side_effect=get_plugins_by_type)

    # Run the loop briefly to process one cycle
    loop_task = asyncio.create_task(kernel.consciousness_loop())
    await asyncio.sleep(0.1)  # Allow one loop iteration
    loop_task.cancel()
    try:
        await loop_task
    except asyncio.CancelledError:
        pass

    # Assertions
    mock_interface.execute.assert_called_once()
    mock_planner.execute.assert_called_once()
    mock_tool.do_something.assert_called_once_with(arg1="value1")
