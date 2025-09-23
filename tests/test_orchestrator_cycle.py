import pytest
from unittest.mock import MagicMock, patch
from core.orchestrator import Orchestrator
from core.context import SharedContext

@pytest.fixture
def mock_llm():
    """Fixture to create a mock LLM object."""
    return MagicMock()

@pytest.fixture
def orchestrator(mock_llm):
    """Fixture to create an Orchestrator with a mocked LLM and tools."""
    # We patch the _load_tools to prevent file system access and control the toolset
    with patch.object(Orchestrator, '_load_tools', return_value={}):
        orc = Orchestrator(llm=mock_llm)
        # Manually add mocked tools that we can control
        orc.tools = {
            "ListDirectoryTool": MagicMock(),
            "WriteFileTool": MagicMock(),
            "ReadFileTool": MagicMock(),
        }
        yield orc

@pytest.mark.asyncio
async def test_successful_plan_execution(orchestrator, mock_llm):
    """
    Tests the orchestrator's ability to execute a valid plan without errors.
    """
    # Arrange
    initial_plan = [
        {"step_id": 1, "description": "List files", "tool_name": "ListDirectoryTool", "parameters": {"path": "/"}},
        {"step_id": 2, "description": "Write a file", "tool_name": "WriteFileTool", "parameters": {"file_path": "test.txt", "content": "hello"}}
    ]

    context = SharedContext(
        session_id="test_session",
        original_prompt="test prompt",
        current_plan=initial_plan
    )

    # Configure the mock tools' execute methods
    orchestrator.tools['ListDirectoryTool'].execute.return_value = ["file1.txt", "file2.txt"]
    orchestrator.tools['WriteFileTool'].execute.return_value = "File 'test.txt' has been written successfully."

    # Act
    result_context = await orchestrator.execute_plan(context)

    # Assert
    assert result_context.feedback == "Plan executed successfully."
    assert len(result_context.step_history) == 2
    assert result_context.step_history[0]['output']['status'] == 'success'
    assert result_context.step_history[1]['output']['status'] == 'success'
    orchestrator.tools['ListDirectoryTool'].execute.assert_called_once_with(path="/")
    orchestrator.tools['WriteFileTool'].execute.assert_called_once_with(file_path="test.txt", content="hello")

import asyncio

@pytest.mark.asyncio
async def test_plan_execution_with_failure_and_repair(orchestrator, mock_llm):
    """
    Tests the orchestrator's cognitive cycle: failure, re-planning, and successful execution of the new plan.
    """
    # Arrange
    failing_plan = [
        {"step_id": 1, "description": "This step will fail", "tool_name": "ReadFileTool", "parameters": {"file_path": "non_existent_file.txt"}}
    ]

    corrected_plan = [
        {"step_id": 1, "description": "Write a file first", "tool_name": "WriteFileTool", "parameters": {"file_path": "new_file.txt", "content": "I exist now"}},
        {"step_id": 2, "description": "Now read the file", "tool_name": "ReadFileTool", "parameters": {"file_path": "new_file.txt"}}
    ]

    context = SharedContext(
        session_id="test_session_repair",
        original_prompt="test prompt for repair",
        current_plan=failing_plan
    )

    # Mock the new async planner to return the corrected plan
    mock_planner = MagicMock()
    repaired_context = SharedContext(session_id="repaired", original_prompt="")
    repaired_context.payload['plan'] = corrected_plan

    future = asyncio.Future()
    future.set_result(repaired_context)
    mock_planner.generate_plan.return_value = future
    orchestrator.planner = mock_planner

    # Configure the mock tools' execute methods for the scenario
    orchestrator.tools['ReadFileTool'].execute.side_effect = [
        FileNotFoundError("File not found"),  # First call fails
        "I exist now"  # Second call succeeds
    ]
    orchestrator.tools['WriteFileTool'].execute.return_value = "File 'new_file.txt' has been written successfully."

    # Act
    result_context = await orchestrator.execute_plan(context)

    # Assert
    assert result_context.feedback == "Plan executed successfully."
    assert len(result_context.step_history) == 2  # History of the *successful* plan

    # Check that the planner was called for repair
    mock_planner.generate_plan.assert_called_once()

    # Check tool calls
    assert orchestrator.tools['ReadFileTool'].execute.call_count == 2
    orchestrator.tools['WriteFileTool'].execute.assert_called_once_with(file_path="new_file.txt", content="I exist now")

    # Check the final successful history
    assert result_context.step_history[0]['tool_name'] == 'WriteFileTool'
    assert result_context.step_history[0]['output']['status'] == 'success'
    assert result_context.step_history[1]['tool_name'] == 'ReadFileTool'
    assert result_context.step_history[1]['output']['status'] == 'success'
