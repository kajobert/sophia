import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from core.kernel import Kernel
from plugins.base_plugin import PluginType

# Configure logging for tests
logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Dynamic replanning is currently being refactored and this test is unstable.")
@pytest.mark.asyncio
async def test_kernel_dynamic_replanning_on_failure():
    """
    Integration test to verify the Dynamic Cognitive Engine's replanning loop.
    This test simulates a multi-step plan where the first step fails, and
    verifies that the Kernel discards the old plan and invokes the planner
    to create a new one.
    """
    # --- Mocks and Fixtures ---
    mock_planner = MagicMock(name="CognitivePlanner")
    mock_failing_tool = MagicMock(name="FailingTool")
    mock_successful_tool = MagicMock(name="SuccessfulTool")

    # --- Plan Definitions ---
    initial_failing_plan = [
        {"tool_name": "failing_tool", "method_name": "doomed_to_fail", "arguments": {"arg": "value"}},
        {"tool_name": "successful_tool", "method_name": "should_not_be_called", "arguments": {}},
    ]
    corrected_successful_plan = [
        {"tool_name": "successful_tool", "method_name": "run_successfully", "arguments": {"arg": "corrected"}},
    ]

    # --- Mock Behaviors ---
    # The planner's execute method is async, so it needs to be an AsyncMock
    mock_planner.execute = AsyncMock(
        side_effect=[
            MagicMock(payload={"plan": initial_failing_plan}),
            MagicMock(payload={"plan": corrected_successful_plan}),
        ]
    )
    mock_planner.name = "cognitive_planner"

    failing_method = AsyncMock(side_effect=ValueError("This was designed to fail"))
    mock_failing_tool.name = "failing_tool"
    mock_failing_tool.doomed_to_fail = failing_method
    mock_failing_tool.get_tool_definitions.return_value = [{"function": {"name": "doomed_to_fail", "parameters": {"properties": {"arg": {"type": "string"}}}}}]

    successful_method = AsyncMock(return_value="Success")
    mock_successful_tool.name = "successful_tool"
    mock_successful_tool.run_successfully = successful_method
    mock_successful_tool.get_tool_definitions.return_value = [{"function": {"name": "run_successfully", "parameters": {"properties": {"arg": {"type": "string"}}}}}]

    # --- Test Setup ---
    with patch("core.kernel.PluginManager") as mock_plugin_manager_constructor:
        mock_plugin_manager = mock_plugin_manager_constructor.return_value
        # Configure the mock to return specific plugins for the CORE type, and none for others.
        def get_plugins_by_type_side_effect(plugin_type):
            if plugin_type == PluginType.CORE:
                return [mock_planner, mock_failing_tool, mock_successful_tool]
            return []
        mock_plugin_manager.get_plugins_by_type.side_effect = get_plugins_by_type_side_effect

        kernel = Kernel()
        await kernel.initialize()

        # --- Test Execution ---
        # Run the consciousness loop as a background task
        loop_task = asyncio.create_task(kernel.consciousness_loop(single_run_input="start"))

        # Give the loop time to run through the failure and replanning cycle.
        await asyncio.sleep(2.0)

        # --- Assertions ---
        # 1. Assert that the planner was called twice.
        assert mock_planner.execute.call_count == 2, "Planner should be called once for the initial plan, and a second time after failure."

        # 2. Assert that the failing tool's method was attempted.
        failing_method.assert_awaited_once()

        # 3. Assert that the method from the corrected plan was attempted.
        successful_method.assert_awaited_once()

        # 4. Assert that the second step of the initial failing plan was never attempted.
        assert mock_successful_tool.should_not_be_called.call_count == 0, "The second step of a failing plan should be discarded."

        logger.info("Test successful: Kernel correctly initiated replanning.")

        # Clean up the background task
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass
