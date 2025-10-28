import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from core.kernel import Kernel
from core.context import SharedContext
from plugins.base_plugin import BasePlugin, PluginType
from plugins.tool_file_system import FileSystemTool

@pytest.mark.asyncio
@patch('core.plugin_manager.PluginManager.load_plugins', MagicMock(return_value=None))
async def test_end_to_end_tool_call_with_repair_loop(caplog):
    """
    Tests the Kernel's validation and repair loop by mocking the plugin
    ecosystem and controlling the data flow through the consciousness loop.
    """
    caplog.set_level(logging.INFO)
    mock_logger = logging.getLogger("test_logger")

    # --- 1. Mocks & Real Instances Setup ---
    # Mock Interface Plugin
    mock_interface = AsyncMock(spec=BasePlugin)
    mock_interface.name = "mock_interface"
    mock_interface.plugin_type = PluginType.INTERFACE
    input_context = SharedContext("test", "LISTENING", mock_logger, user_input="list files in /")
    mock_interface.execute.return_value = input_context # Corrected: Return context directly

    # Mock LLM Tool (for repair)
    mock_llm_tool_for_repair = AsyncMock(spec=BasePlugin)
    mock_llm_tool_for_repair.name = "tool_llm"
    mock_llm_tool_for_repair.plugin_type = PluginType.TOOL
    repaired_args_str = '{"path": "/"}'
    async def llm_repair_side_effect(context, *args, **kwargs):
        if "ATTENTION" in context.user_input:
            return SharedContext("test", "EXECUTING", mock_logger, payload={"llm_response": repaired_args_str})
        pytest.fail("The repair LLM mock was called for a non-repair task.")
    mock_llm_tool_for_repair.execute.side_effect = llm_repair_side_effect

    # Mock Planner that returns a faulty plan
    mock_planner = AsyncMock(spec=BasePlugin)
    mock_planner.name = "cognitive_planner"
    mock_planner.plugin_type = PluginType.COGNITIVE
    faulty_plan = [{"tool_name": "tool_file_system", "method_name": "list_directory", "arguments": {"path": 123}}] # Invalid arg type
    async def mock_planner_execute(context):
        context.payload['plan'] = faulty_plan
        # Log the "raw thought" for the test assertion
        logging.getLogger("test_logger").info(f"Raw LLM response received in planner: {faulty_plan}")
        return context
    mock_planner.execute.side_effect = mock_planner_execute

    # Real File System Tool (the target of the tool call)
    fs_tool = FileSystemTool()
    fs_tool.setup({"sandbox_dir": "test_sandbox"})
    fs_tool.list_directory = MagicMock(return_value=["file1.txt", "other.txt"])

    # --- 2. Kernel and PluginManager Setup ---
    kernel = Kernel()
    mock_plugin_manager = MagicMock()

    # Configure the mock manager to return our controlled set of plugins
    all_plugins = [mock_interface, mock_planner, mock_llm_tool_for_repair, fs_tool]
    def get_plugins_side_effect(plugin_type):
        return [p for p in all_plugins if p.plugin_type == plugin_type]
    mock_plugin_manager.get_plugins_by_type.side_effect = get_plugins_side_effect

    kernel.plugin_manager = mock_plugin_manager

    # --- 3. Run a single iteration of the consciousness loop ---
    async def single_run_loop():
        original_wait = asyncio.wait
        async def single_wait(tasks, **kwargs):
            done, pending = await original_wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            kernel.is_running = False
            return done, pending

        with patch('asyncio.wait', single_wait):
            await kernel.consciousness_loop()

    try:
        await asyncio.wait_for(single_run_loop(), timeout=5)
    except asyncio.TimeoutError:
        pytest.fail("The test timed out, suggesting the loop did not exit as expected.")

    # --- 4. Assertions ---
    assert any("Raw LLM response received in planner" in record.message for record in caplog.records)
    assert any("Validation failed for step 1" in record.message for record in caplog.records)

    repair_call = mock_llm_tool_for_repair.execute.call_args
    assert repair_call is not None, "The LLM tool was not called to make a repair."
    repair_context = repair_call.args[0]
    assert "ATTENTION: The tool call JSON failed validation" in repair_context.user_input

    assert any("SECOND-PHASE LOG: Validated plan step 1" in record.message and "'path': '/'" in record.message for record in caplog.records)
    fs_tool.list_directory.assert_called_once_with(path="/")
