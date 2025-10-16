"""
Unit tests for the Proactive NomadOrchestratorV2.

This file tests the new, simplified state machine architecture.
"""

import pytest
import asyncio
import json
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from core.nomad_orchestrator_v2 import NomadOrchestratorV2, MissionState

# ==================== MOCK INFRASTRUCTURE ====================

class MockLLMManager:
    """A simplified mock for the LLMManager."""
    def __init__(self):
        self.responses = []
        self.call_history = []
        self._llm_model = AsyncMock()
        self._llm_model.generate_content_async.side_effect = self._generate_response
    
    def set_responses(self, *responses):
        """Set a queue of responses for the LLM to return."""
        self.responses = list(responses)
        self.call_history = []

    async def _generate_response(self, prompt: str):
        """Generates a response from the queue."""
        self.call_history.append(prompt)
        if not self.responses:
            raise Exception("MockLLMManager ran out of responses")
        
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response

        return response, {"usage": {"total_tokens": 100}}

    def get_llm(self, name: str) -> AsyncMock:
        """Returns the mock LLM model."""
        return self._llm_model

class MockMCPClient:
    """A mock for the MCPClient to simulate tool execution."""
    def __init__(self):
        self.tool_results = {}
        self.fail_on_tool = None
        self.call_history = []

    def set_tool_result(self, tool_name: str, result: Any):
        """Set the result for a specific tool."""
        self.tool_results[tool_name] = result

    def set_tool_to_fail(self, tool_name: str, error: Exception):
        """Make a specific tool raise an exception."""
        self.fail_on_tool = (tool_name, error)
        
    async def start_servers(self): pass
    async def shutdown(self): pass
    
    async def execute_tool(self, tool_name, args, kwargs, verbose=False):
        """Mock tool execution."""
        self.call_history.append({"tool_name": tool_name, "args": args, "kwargs": kwargs})
        
        if self.fail_on_tool and self.fail_on_tool[0] == tool_name:
            raise self.fail_on_tool[1]

        return self.tool_results.get(tool_name, f"Mock result for {tool_name}")


# ==================== FIXTURES ====================

@pytest.fixture
def mock_config_path(tmp_path):
    """Creates a mock config directory and returns the path."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text("llm:\n  default: mock-model")
    return tmp_path

@pytest.fixture
def orchestrator(mock_config_path):
    """Provides a fully mocked NomadOrchestratorV2 instance."""
    with patch('core.nomad_orchestrator_v2.LLMManager', autospec=True) as MockLLMManager_class, \
         patch('core.nomad_orchestrator_v2.MCPClient', autospec=True) as MockMCPClient_class:
        
        # Configure the mock classes to return our custom mock instances
        mock_llm_instance = MockLLMManager()
        MockLLMManager_class.return_value = mock_llm_instance
        
        mock_mcp_instance = MockMCPClient()
        MockMCPClient_class.return_value = mock_mcp_instance

        orch = NomadOrchestratorV2(project_root=str(mock_config_path), max_iterations=10)
        
        # Attach our custom mocks for easier access in tests.
        # The real attributes were already replaced during __init__ thanks to the patch.
        orch.mock_llm_manager = mock_llm_instance
        orch.mock_mcp_client = mock_mcp_instance
        
        yield orch

# ==================== TEST CASES ====================

class TestProactiveOrchestrator:
    """Tests for the proactive state machine in NomadOrchestratorV2."""

    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator):
        """Test that the orchestrator initializes correctly."""
        assert orchestrator.current_state == MissionState.THINKING
        assert orchestrator.mission_goal == ""
        assert not orchestrator.history

    @pytest.mark.asyncio
    async def test_simple_success_flow(self, orchestrator):
        """
        Test a simple mission: THINKING -> EXECUTING_TOOL -> THINKING -> MISSION_COMPLETE
        """
        mission = "List the files in the current directory."
        
        # 1. First THINKING state -> LLM returns list_files tool call
        list_files_call = json.dumps({"tool_name": "list_files", "kwargs": {"path": "."}})
        
        # 2. After tool execution -> LLM decides mission is complete
        mission_complete_call = json.dumps({"tool_name": "mission_complete"})

        orchestrator.mock_llm_manager.set_responses(list_files_call, mission_complete_call)
        orchestrator.mock_mcp_client.set_tool_result("list_files", "file1.txt\ndir1/")

        # Execute
        await orchestrator.execute_mission(mission)

        # Assertions
        assert orchestrator.current_state == MissionState.MISSION_COMPLETE
        assert len(orchestrator.history) == 3
        assert orchestrator.history[0]["role"] == "assistant"
        assert "list_files" in orchestrator.history[0]["content"]
        assert orchestrator.history[1]["role"] == "tool"
        assert "file1.txt" in orchestrator.history[1]["content"]
        assert orchestrator.history[2]["role"] == "assistant"
        assert "mission_complete" in orchestrator.history[2]["content"]

        # Verify mocks were called
        assert len(orchestrator.mock_llm_manager.call_history) == 2
        assert len(orchestrator.mock_mcp_client.call_history) == 1
        assert orchestrator.mock_mcp_client.call_history[0]["tool_name"] == "list_files"

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery_flow(self, orchestrator):
        """
        Test the error handling flow:
        THINKING -> EXECUTE (fails) -> HANDLING_ERROR -> EXECUTE (succeeds) -> COMPLETE
        """
        mission = "Read the non_existent_file.txt file."

        # 1. First THINKING state -> LLM tries to read a file that doesn't exist
        read_file_call = json.dumps({"tool_name": "read_file", "kwargs": {"filepath": "non_existent_file.txt"}})
        
        # 2. HANDLING_ERROR state -> LLM proposes a corrective action (e.g., list files first)
        list_files_call = json.dumps({"tool_name": "list_files", "kwargs": {"path": "."}})
        
        # 3. After listing files -> LLM decides mission is complete (for simplicity)
        mission_complete_call = json.dumps({"tool_name": "mission_complete"})

        orchestrator.mock_llm_manager.set_responses(read_file_call, list_files_call, mission_complete_call)
        
        # Setup MCP mock
        orchestrator.mock_mcp_client.set_tool_to_fail("read_file", FileNotFoundError("File not found"))
        orchestrator.mock_mcp_client.set_tool_result("list_files", "some_other_file.txt")

        # Execute
        await orchestrator.execute_mission(mission)

        # Assertions
        assert orchestrator.current_state == MissionState.MISSION_COMPLETE
        assert len(orchestrator.mock_llm_manager.call_history) == 3
        assert len(orchestrator.mock_mcp_client.call_history) == 2

        # Verify the flow in history
        assert "read_file" in orchestrator.history[0]["content"]
        assert "Error executing tool read_file" in orchestrator.history[1]["content"]
        assert "list_files" in orchestrator.history[2]["content"]
        assert "some_other_file.txt" in orchestrator.history[3]["content"]
        assert "mission_complete" in orchestrator.history[4]["content"]

    @pytest.mark.asyncio
    async def test_mission_aborts_on_max_iterations(self, orchestrator):
        """Test that the mission loop terminates after max_iterations."""
        orchestrator.max_iterations = 2
        
        list_files_call = json.dumps({"tool_name": "list_files"})
        orchestrator.mock_llm_manager.set_responses(list_files_call, list_files_call, list_files_call)
        orchestrator.mock_mcp_client.set_tool_result("list_files", "a_file.txt")

        await orchestrator.execute_mission("Loop forever")

        assert orchestrator.current_state != MissionState.MISSION_COMPLETE
        # The loop runs for 2 iterations.
        # Iteration 1: THINKING (1 LLM call) -> EXECUTING_TOOL
        # Iteration 2: EXECUTING_TOOL (1 tool call) -> THINKING
        # Loop terminates because iteration (2) >= max_iterations (2)
        assert len(orchestrator.mock_llm_manager.call_history) == 1
        assert len(orchestrator.mock_mcp_client.call_history) == 1

    @pytest.mark.asyncio
    async def test_initial_context_is_added_to_history(self, orchestrator):
        """Test that initial_context is correctly added to the history."""
        mission = "Fix the bug."
        error_log = "Traceback:\n  File 'main.py', line 10, in <module>\n    raise ValueError('Boom!')"
        
        mission_complete_call = json.dumps({"tool_name": "mission_complete"})
        orchestrator.mock_llm_manager.set_responses(mission_complete_call)

        await orchestrator.execute_mission(mission, initial_context=error_log)

        assert len(orchestrator.history) == 2
        assert orchestrator.history[0]["role"] == "system"
        assert "Traceback" in orchestrator.history[0]["content"]
        assert "Boom!" in orchestrator.history[0]["content"]
        assert "mission_complete" in orchestrator.history[1]["content"]