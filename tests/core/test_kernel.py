import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock

import pytest

from core.context import SharedContext
from core.kernel import Kernel
from plugins.base_plugin import BasePlugin, PluginType


@pytest.mark.asyncio
async def test_kernel_uses_interface_plugin():
    """
    Tests that the Kernel calls the `execute` method on a loaded interface
    plugin.
    """
    kernel = Kernel()

    # --- Mocks ---
    mock_interface = AsyncMock(spec=BasePlugin)
    mock_interface.name = "mock_interface"
    # This side effect will block until the test cancels the loop,
    # ensuring the execute method is called exactly once.
    unblock_event = asyncio.Event()
    mock_interface.execute.side_effect = unblock_event.wait

    # --- Kernel Setup ---
    def get_plugins_by_type(plugin_type):
        if plugin_type == PluginType.INTERFACE:
            return [mock_interface]
        return []

    kernel.plugin_manager.get_plugins_by_type = MagicMock(side_effect=get_plugins_by_type)
    await kernel.initialize()

    # --- Run & Assert ---
    task = asyncio.create_task(kernel.consciousness_loop())
    await asyncio.sleep(0.01)  # Give time for the loop to start and call execute

    mock_interface.execute.assert_called_once()

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_kernel_planning_and_executing_phases():
    """Test that the Kernel correctly runs the PLANNING and EXECUTING phases."""
    kernel = Kernel()

    # --- Mocks ---
    mock_interface = AsyncMock(spec=BasePlugin)
    mock_planner = AsyncMock(spec=BasePlugin)
    mock_tool = MagicMock()

    mock_interface.name = "mock_interface"
    # Provide input on the first call, then idle on subsequent calls.
    has_provided_input = False

    async def interface_side_effect(context):
        nonlocal has_provided_input
        if not has_provided_input:
            has_provided_input = True
            context.user_input = "test input"
            return context
        await asyncio.sleep(0.2)  # Idle to allow cancellation
        return context

    mock_interface.execute.side_effect = interface_side_effect

    plan = [
        {
            "tool_name": "mock_tool",
            "method_name": "do_something",
            "arguments": {"arg1": "value1"},
        }
    ]
    mock_planner.name = "cognitive_planner"
    mock_logger = MagicMock()
    mock_logger.level = logging.INFO
    mock_planner.execute.return_value = SharedContext(
        session_id="test",
        payload={"plan": plan},
        current_state="PLANNING",
        logger=mock_logger,
        user_input="test input",
    )

    mock_tool.name = "mock_tool"
    mock_tool.do_something.return_value = "done"
    mock_tool.get_tool_definitions.return_value = [
        {
            "function": {
                "name": "do_something",
                "parameters": {
                    "type": "object",
                    "properties": {"arg1": {"type": "string"}},
                    "required": ["arg1"],
                },
            }
        }
    ]

    # --- Kernel Setup ---
    def get_plugins_by_type(ptype):
        if ptype == PluginType.INTERFACE:
            return [mock_interface]
        if ptype == PluginType.COGNITIVE:
            return [mock_planner]
        if ptype == PluginType.TOOL:
            return [mock_tool]
        return []

    kernel.plugin_manager.get_plugins_by_type = MagicMock(side_effect=get_plugins_by_type)
    await kernel.initialize()

    # --- Run & Assert ---
    task = asyncio.create_task(kernel.consciousness_loop())
    await asyncio.sleep(0.1)  # Allow one full cycle
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    mock_planner.execute.assert_called_once()
    mock_tool.do_something.assert_called_once_with(arg1="value1")


@pytest.mark.asyncio
async def test_kernel_handles_multi_step_chained_plan():
    """Tests that the Kernel can execute a multi-step plan with chained results."""
    kernel = Kernel()

    # --- Mocks ---
    mock_interface = AsyncMock(spec=BasePlugin)
    mock_planner = AsyncMock(spec=BasePlugin)
    mock_lister = MagicMock()
    mock_writer = MagicMock()

    mock_interface.name = "mock_interface"
    # Provide input on the first call, then idle.
    has_provided_input = False

    async def interface_side_effect(context):
        nonlocal has_provided_input
        if not has_provided_input:
            has_provided_input = True
            context.user_input = "List and write"
            return context
        await asyncio.sleep(0.2)  # Idle to allow cancellation
        return context

    mock_interface.execute.side_effect = interface_side_effect

    plan = [
        {"tool_name": "lister", "method_name": "list_items", "arguments": {}},
        {
            "tool_name": "writer",
            "method_name": "write_items",
            "arguments": {"file": "out.txt", "content": "$result.step_1"},
        },
    ]
    mock_planner.name = "cognitive_planner"
    mock_logger = MagicMock()
    mock_logger.level = logging.INFO
    mock_planner.execute.return_value = SharedContext(
        session_id="test",
        logger=mock_logger,
        payload={"plan": plan},
        current_state="PLANNING",
        user_input="List and write",
    )

    plugin_list = '["item1", "item2"]'
    mock_lister.name = "lister"
    mock_lister.list_items.return_value = plugin_list
    mock_lister.get_tool_definitions.return_value = [
        {
            "function": {
                "name": "list_items",
                "parameters": {"type": "object", "properties": {}},
            }
        }
    ]

    mock_writer.name = "writer"
    mock_writer.write_items.return_value = "OK"
    mock_writer.get_tool_definitions.return_value = [
        {
            "function": {
                "name": "write_items",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["file", "content"],
                },
            }
        }
    ]

    # --- Kernel Setup ---
    def get_plugins_by_type(ptype):
        if ptype == PluginType.INTERFACE:
            return [mock_interface]
        if ptype == PluginType.COGNITIVE:
            return [mock_planner]
        if ptype == PluginType.TOOL:
            return [mock_lister, mock_writer]
        return []

    kernel.plugin_manager.get_plugins_by_type = MagicMock(side_effect=get_plugins_by_type)
    await kernel.initialize()

    # --- Run & Assert ---
    task = asyncio.create_task(kernel.consciousness_loop())
    await asyncio.sleep(0.1)  # Allow one full cycle
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    mock_lister.list_items.assert_called_once_with()
    mock_writer.write_items.assert_called_once_with(file="out.txt", content=plugin_list)
