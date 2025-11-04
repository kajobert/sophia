import json
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.context import SharedContext
from plugins.cognitive_planner import Planner

# --- Mock Object Factories ---


def create_mock_tool_call(function_name: str, arguments_json_str: str) -> MagicMock:
    """Creates a single mock tool_call object."""
    mock_tool_call = MagicMock()
    mock_function = MagicMock()
    mock_function.name = function_name
    mock_function.arguments = arguments_json_str
    mock_tool_call.function = mock_function
    return mock_tool_call


def create_mock_llm_message(tool_calls: list) -> MagicMock:
    """Creates a mock message object with a list of tool calls."""
    mock_message = MagicMock()
    mock_message.tool_calls = tool_calls
    # Ensure tool_calls is always a list, even if empty
    if not isinstance(mock_message.tool_calls, list):
        mock_message.tool_calls = []

    # Simulate the 'content' attribute that the new planner logic expects
    if tool_calls and tool_calls[0].function.name == "create_plan":
        # For legacy format, the content is the arguments of the create_plan call
        mock_message.content = tool_calls[0].function.arguments
    else:
        # For direct tool calls, simulate a string containing the JSON
        # with robust JSON parsing to handle malformed test data.
        content_list = []
        for call in tool_calls:
            try:
                args = json.loads(call.function.arguments)
            except json.JSONDecodeError:
                args = {}  # Default to empty dict if JSON is malformed
            content_list.append(
                {
                    "tool_name": call.function.name.split(".")[0],
                    "method_name": call.function.name.split(".")[1],
                    "arguments": args,
                }
            )
        mock_message.content = json.dumps(content_list)
    return mock_message


# --- Pytest Fixture ---


@pytest.fixture
def planner():
    """Fixture for the Planner plugin with a mocked LLM tool."""
    p = Planner()
    mock_llm_tool = AsyncMock()

    # CRITICAL FIX: Mock the synchronous method on the AsyncMock.
    # The planner's execute method iterates over this, so it must return
    # an iterable (a list), not a coroutine.
    mock_llm_tool.get_tool_definitions = MagicMock(return_value=[])

    # Setting a default return value for the mock's execute method
    mock_llm_tool.execute.return_value = SharedContext(
        "default_session",
        "default_state",
        logging.getLogger("test"),
        payload={"llm_response": create_mock_llm_message([])},
    )
    p.setup({"all_plugins": {"tool_llm": mock_llm_tool}})
    # Avoid file read errors in tests
    p.prompt_template = "Test Prompt with tools: {tool_list}"
    return p


# --- Test Cases ---


@pytest.mark.asyncio
async def test_planner_parses_legacy_create_plan_format(planner):
    """
    Tests that the planner correctly parses the old format where the plan
    is wrapped in a single 'create_plan' function call.
    """
    # Arrange
    context = SharedContext("test_legacy", "PLANNING", logging.getLogger("test"), "list files")

    plan_dict = {
        "plan": [
            {
                "tool_name": "tool_file_system",
                "method_name": "list_directory",
                "arguments": {"path": "."},
            }
        ]
    }
    plan_json_str = json.dumps(plan_dict)

    tool_call = create_mock_tool_call("create_plan", plan_json_str)
    mock_response = create_mock_llm_message([tool_call])

    planner.llm_tool.execute.return_value = SharedContext(
        "test_legacy",
        "PLANNING",
        logging.getLogger("test"),
        payload={"llm_response": mock_response},
    )

    # Act
    result_context = await planner.execute(context)

    # Assert
    assert "plan" in result_context.payload
    assert result_context.payload["plan"] == plan_dict["plan"]
    planner.llm_tool.execute.assert_called_once()


@pytest.mark.asyncio
async def test_planner_parses_direct_tool_call_list_format(planner):
    """
    Tests that the planner correctly parses the new format where the LLM
    returns a direct list of tool calls.
    """
    # Arrange
    context = SharedContext("test_direct", "PLANNING", logging.getLogger("test"), "write hello")

    tool_call_1 = create_mock_tool_call(
        "tool_file_system.write_file", '{"filepath": "hello.txt", "content": "Hello, World!"}'
    )
    tool_call_2 = create_mock_tool_call("tool_file_system.read_file", '{"filepath": "hello.txt"}')
    mock_response = create_mock_llm_message([tool_call_1, tool_call_2])

    planner.llm_tool.execute.return_value = SharedContext(
        "test_direct",
        "PLANNING",
        logging.getLogger("test"),
        payload={"llm_response": mock_response},
    )

    # Act
    result_context = await planner.execute(context)

    # Assert
    expected_plan = [
        {
            "tool_name": "tool_file_system",
            "method_name": "write_file",
            "arguments": {"filepath": "hello.txt", "content": "Hello, World!"},
        },
        {
            "tool_name": "tool_file_system",
            "method_name": "read_file",
            "arguments": {"filepath": "hello.txt"},
        },
    ]
    assert "plan" in result_context.payload
    assert result_context.payload["plan"] == expected_plan
    planner.llm_tool.execute.assert_called_once()


@pytest.mark.asyncio
async def test_planner_handles_empty_llm_response(planner):
    """
    Tests that the planner returns an empty plan if the LLM response is empty or invalid.
    """
    # Arrange
    context = SharedContext("test_empty", "PLANNING", logging.getLogger("test"), "do nothing")

    planner.llm_tool.execute.return_value = SharedContext(
        "test_empty",
        "PLANNING",
        logging.getLogger("test"),
        payload={"llm_response": None},  # Simulate a complete failure or empty response
    )

    # Act
    result_context = await planner.execute(context)

    # Assert
    assert result_context.payload["plan"] == []


@pytest.mark.asyncio
async def test_planner_handles_response_with_no_tool_calls(planner):
    """
    Tests that the planner returns an empty plan if the LLM responds but makes no tool calls.
    """
    # Arrange
    context = SharedContext("test_no_calls", "PLANNING", logging.getLogger("test"), "hello")

    mock_response = create_mock_llm_message([])  # Empty list of tool calls

    planner.llm_tool.execute.return_value = SharedContext(
        "test_no_calls",
        "PLANNING",
        logging.getLogger("test"),
        payload={"llm_response": mock_response},
    )

    # Act
    result_context = await planner.execute(context)

    # Assert
    assert result_context.payload["plan"] == []


@pytest.mark.asyncio
async def test_planner_handles_malformed_json_in_arguments(planner):
    """
    Tests robustness against JSON errors in both legacy and direct formats.
    """
    # Arrange
    context = SharedContext("test_json_error", "PLANNING", logging.getLogger("test"), "break json")

    # Simulate corrupted JSON in a direct tool call
    tool_call = create_mock_tool_call("tool_file_system.write_file", '{"filepath": "bad.txt"')
    mock_response = create_mock_llm_message([tool_call])

    planner.llm_tool.execute.return_value = SharedContext(
        "test_json_error",
        "PLANNING",
        logging.getLogger("test"),
        payload={"llm_response": mock_response},
    )

    # Act
    result_context = await planner.execute(context)

    # Assert
    # With the new robust parsing, malformed JSON should result in a plan
    # with empty arguments for the failed step.
    expected_plan = [
        {
            "tool_name": "tool_file_system",
            "method_name": "write_file",
            "arguments": {},
        }
    ]
    assert result_context.payload["plan"] == expected_plan
