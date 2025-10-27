import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import AsyncMock, MagicMock
from plugins.cognitive_planner import Planner
from core.context import SharedContext
import logging
import json

@pytest.fixture
def planner():
    """Fixture to create a Planner instance."""
    return Planner()

@pytest.fixture
def shared_context():
    """Fixture to create a SharedContext instance."""
    return SharedContext(
        session_id="test_session",
        current_state="LISTENING",
        logger=logging.getLogger("test_logger"),
        user_input="Test user input",
    )

@pytest.mark.asyncio
async def test_planner_execute_success(planner, shared_context):
    """Test that the planner generates a plan successfully."""
    # Arrange
    mock_llm_tool = AsyncMock()
    mock_llm_response = json.dumps([
        {
            "tool_name": "tool_file_system",
            "method_name": "read_file",
            "arguments": {"path": "hello.txt"},
        }
    ])

    # Create a mock context to be returned by the mocked LLM tool
    mock_llm_context = SharedContext(session_id="test_session", current_state="PLANNING", logger=logging.getLogger())
    mock_llm_context.payload = {"llm_response": mock_llm_response}
    mock_llm_tool.execute.return_value = mock_llm_context

    config = {"tool_llm": mock_llm_tool}
    planner.setup(config)

    # Act
    result_context = await planner.execute(shared_context)

    # Assert
    mock_llm_tool.execute.assert_called_once()
    assert "plan" in result_context.payload
    assert len(result_context.payload["plan"]) == 1
    assert result_context.payload["plan"][0]["tool_name"] == "tool_file_system"

@pytest.mark.asyncio
async def test_planner_execute_json_decode_error(planner, shared_context):
    """Test that the planner handles a JSON decode error gracefully."""
    # Arrange
    mock_llm_tool = AsyncMock()
    mock_llm_response = "invalid json"

    mock_llm_context = SharedContext(session_id="test_session", current_state="PLANNING", logger=logging.getLogger())
    mock_llm_context.payload = {"llm_response": mock_llm_response}
    mock_llm_tool.execute.return_value = mock_llm_context

    config = {"tool_llm": mock_llm_tool}
    planner.setup(config)

    # Act
    result_context = await planner.execute(shared_context)

    # Assert
    mock_llm_tool.execute.assert_called_once()
    assert "plan" in result_context.payload
    assert result_context.payload["plan"] == []

@pytest.mark.asyncio
async def test_planner_no_user_input(planner, shared_context):
    """Test that the planner returns the context without modification if there is no user input."""
    # Arrange
    shared_context.user_input = None
    mock_llm_tool = AsyncMock()
    config = {"tool_llm": mock_llm_tool}
    planner.setup(config)

    # Act
    result_context = await planner.execute(shared_context)

    # Assert
    mock_llm_tool.execute.assert_not_called()
    assert "plan" not in result_context.payload
