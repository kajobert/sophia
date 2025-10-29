import unittest
import json
from unittest.mock import MagicMock, AsyncMock

from core.context import SharedContext
from plugins.cognitive_planner import Planner
from plugins.tool_llm import LLMTool


class MockLLMResponse:
    def __init__(self, tool_calls):
        self.tool_calls = tool_calls


class MockToolCall:
    def __init__(self, name, arguments):
        self.function = MagicMock()
        self.function.name = name
        self.function.arguments = arguments


class TestCognitivePlanner(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.planner = Planner()
        file_system_mock = MagicMock()
        file_system_mock.get_tool_definitions.return_value = [
            {
                "function": {
                    "name": "list_directory",
                    "description": "Lists files in a directory.",
                }
            }
        ]
        llm_mock = AsyncMock(spec=LLMTool)

        self.planner.setup(
            {
                "plugins": {
                    "tool_file_system": file_system_mock,
                    "tool_llm": llm_mock,
                }
            }
        )
        self.context = SharedContext(
            session_id="test-session",
            user_input="list files",
            logger=MagicMock(),
            current_state="PLANNING",
        )

    async def test_direct_tool_calls_scenario(self):
        """Tests parsing when the LLM returns a direct list of tool calls."""
        mock_tool_calls = [
            MockToolCall(
                "tool_file_system.list_directory", '{"path": "."}'
            ),
            MockToolCall("tool_file_system.write_file", '{"path": "test.txt", "content": "hello"}'),
        ]
        self.planner.llm_tool.execute.return_value = SharedContext(
            session_id=self.context.session_id,
            current_state="PLANNING",
            logger=self.context.logger,
            payload={"llm_response": MockLLMResponse(mock_tool_calls)},
        )

        result_context = await self.planner.execute(self.context)
        plan = result_context.payload.get("plan")

        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0]["tool_name"], "tool_file_system")
        self.assertEqual(plan[0]["method_name"], "list_directory")
        self.assertEqual(plan[0]["arguments"], {"path": "."})
        self.assertEqual(plan[1]["arguments"], {"path": "test.txt", "content": "hello"})

    async def test_create_plan_scenario(self):
        """Tests parsing when the LLM wraps the plan in a 'create_plan' call."""
        plan_data = {
            "plan": [
                {
                    "tool_name": "tool_file_system",
                    "method_name": "read_file",
                    "arguments": {"path": "document.txt"},
                }
            ]
        }
        mock_tool_calls = [
            MockToolCall("create_plan", json.dumps(plan_data))
        ]
        self.planner.llm_tool.execute.return_value = SharedContext(
            session_id=self.context.session_id,
            current_state="PLANNING",
            logger=self.context.logger,
            payload={"llm_response": MockLLMResponse(mock_tool_calls)},
        )

        result_context = await self.planner.execute(self.context)
        plan = result_context.payload.get("plan")

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["tool_name"], "tool_file_system")
        self.assertEqual(plan[0]["method_name"], "read_file")

    async def test_robust_argument_parsing(self):
        """Tests that argument parsing handles various edge cases gracefully."""
        mock_tool_calls = [
            MockToolCall("tool_file_system.write_file", '{"path": "a.txt", "content": null}'),
            MockToolCall("tool_file_system.write_file", '{"path": "b.txt"}'),
            MockToolCall("tool_file_system.write_file", ''),
            MockToolCall("tool_file_system.write_file", '{"malformed": json}'),
        ]
        self.planner.llm_tool.execute.return_value = SharedContext(
            session_id=self.context.session_id,
            current_state="PLANNING",
            logger=self.context.logger,
            payload={"llm_response": MockLLMResponse(mock_tool_calls)},
        )

        result_context = await self.planner.execute(self.context)
        plan = result_context.payload.get("plan")

        self.assertEqual(len(plan), 4)
        self.assertEqual(plan[0]["arguments"], {"path": "a.txt", "content": None})
        self.assertEqual(plan[1]["arguments"], {"path": "b.txt"})
        self.assertEqual(plan[2]["arguments"], {})
        self.assertEqual(plan[3]["arguments"], {})


if __name__ == "__main__":
    unittest.main()
