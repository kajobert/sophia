import pytest
import json
from unittest.mock import MagicMock
from agents.planner_agent import PlannerAgent
from core.context import SharedContext

# --- Test Fixtures ---


@pytest.fixture
def mock_llm_adapter():
    """Creates a mock LLM adapter for testing."""
    return MagicMock()


@pytest.fixture
def planner(mock_llm_adapter):
    """Creates a PlannerAgent instance with a mocked LLM."""
    return PlannerAgent(llm=mock_llm_adapter)


# --- Test Cases ---


def test_successful_plan_generation(planner, mock_llm_adapter):
    """
    Tests that the planner successfully generates and validates a plan on the first attempt.
    """
    # Arrange
    valid_plan_json = json.dumps(
        [
            {
                "step_id": 1,
                "description": "List files",
                "tool_name": "ListDirectoryTool",
                "parameters": {"path": "."},
            }
        ]
    )
    mock_llm_adapter.invoke.return_value = f"```json\n{valid_plan_json}\n```"
    context = SharedContext(
        original_prompt="List all files.", session_id="test_session"
    )

    # Act
    result_context = planner.run_task(context)

    # Assert
    mock_llm_adapter.invoke.assert_called_once()
    assert result_context.payload["plan"] is not None
    assert len(result_context.payload["plan"]) == 1
    assert result_context.payload["plan"][0]["tool_name"] == "ListDirectoryTool"
    assert result_context.feedback is None


def test_retry_on_invalid_json(planner, mock_llm_adapter):
    """
    Tests that the planner retries if the LLM returns invalid JSON, then succeeds.
    """
    # Arrange
    invalid_json = '{"step_id": 1, "description": "missing quotes and comma"}'
    valid_plan_json = json.dumps(
        [{"step_id": 1, "description": "fixed", "tool_name": "Tool", "parameters": {}}]
    )

    # Set the mock to return invalid JSON first, then valid JSON
    mock_llm_adapter.invoke.side_effect = [
        invalid_json,
        f"```json\n{valid_plan_json}\n```",
    ]
    context = SharedContext(original_prompt="Do something.", session_id="test_session")

    # Act
    result_context = planner.run_task(context)

    # Assert
    assert mock_llm_adapter.invoke.call_count == 2
    assert result_context.payload["plan"] is not None
    assert result_context.payload["plan"][0]["description"] == "fixed"


def test_retry_on_empty_response(planner, mock_llm_adapter):
    """
    Tests that the planner retries if the LLM returns an empty string, which was a previous failure point.
    """
    # Arrange
    valid_plan_json = json.dumps(
        [{"step_id": 1, "description": "valid", "tool_name": "Tool", "parameters": {}}]
    )
    mock_llm_adapter.invoke.side_effect = [
        "",
        "  ",
        valid_plan_json,
    ]  # Test empty and whitespace-only responses
    context = SharedContext(original_prompt="Do something.", session_id="test_session")

    # Act
    result_context = planner.run_task(context)

    # Assert
    assert mock_llm_adapter.invoke.call_count == 3
    assert result_context.payload["plan"] is not None


def test_failure_after_max_retries(planner, mock_llm_adapter):
    """
    Tests that the planner fails gracefully after exhausting all retries.
    """
    # Arrange
    mock_llm_adapter.invoke.return_value = "this is not json"
    context = SharedContext(
        original_prompt="This will fail.", session_id="test_session"
    )

    # Act
    result_context = planner.run_task(context)

    # Assert
    assert mock_llm_adapter.invoke.call_count == PlannerAgent.MAX_RETRIES
    assert result_context.payload["plan"] is None
    assert "failed to generate a valid JSON plan" in result_context.feedback


def test_impossible_task_handling(planner, mock_llm_adapter):
    """
    Tests that the planner correctly handles an impossible task by returning an empty plan.
    The prompt instructs the LLM to return `[]` for such tasks.
    """
    # Arrange
    mock_llm_adapter.invoke.return_value = "[]"
    context = SharedContext(
        original_prompt="What is the weather in Prague?", session_id="test_session"
    )

    # Act
    result_context = planner.run_task(context)

    # Assert
    mock_llm_adapter.invoke.assert_called_once()
    assert result_context.payload["plan"] == []
    assert "outside my capabilities" in result_context.feedback
