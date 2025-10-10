import json
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
import httpx
from fastapi.testclient import TestClient

from core.conversational_manager import ConversationalManager
from mcp_servers.worker import jules_api_server

# --- Mocks for New Integration Test ---

# 1. Manager decides to delegate to worker
MANAGER_LLM_RESPONSE_DELEGATE_TO_WORKER = json.dumps({
    "explanation": "This is a complex task that requires tools. I will delegate to the Worker.",
    "tool_call": {
        "tool_name": "delegate_task_to_worker",
        "kwargs": {"task": "Use Jules to create a boba app."}
    }
})

# 2. Worker decides to list sources
WORKER_LLM_RESPONSE_LIST_SOURCES = json.dumps({
    "explanation": "To use the Jules API, I first need to know the available source. I will list them.",
    "tool_call": {"tool_name": "list_jules_sources", "kwargs": {}}
})

# 3. Worker decides to delegate to Jules
WORKER_LLM_RESPONSE_DELEGATE_TO_JULES = json.dumps({
    "explanation": "Now that I have a source, I will delegate the task to Jules.",
    "tool_call": {
        "tool_name": "delegate_task_to_jules",
        "kwargs": {
            "prompt": "Create a boba app!",
            "source": "sources/github/bobalover/boba",
            "starting_branch": "main",
            "title": "Boba App"
        }
    }
})

# 4. Manager generates final response after approval
MANAGER_LLM_RESPONSE_FINAL = json.dumps({
    "explanation": "The delegation was approved and executed successfully. I will inform the user.",
    "tool_call": None
})


@pytest.mark.asyncio
@patch('core.llm_manager.LLMManager._initialize_client', return_value=None)
@patch('core.llm_adapters.OpenRouterAdapter.generate_content_async')
@patch('core.mcp_client.MCPClient.execute_tool')
async def test_end_to_end_delegation_with_approval(mock_execute_tool, mock_llm_generate, mock_init_client):
    """
    Tests the full, correct, end-to-end workflow:
    Manager -> Worker -> list_sources -> delegate_to_jules -> HITL -> Approval -> Final Execution
    """
    # 1. Mock the multi-step LLM conversation
    mock_llm_generate.side_effect = [
        (MANAGER_LLM_RESPONSE_DELEGATE_TO_WORKER, {}),
        (WORKER_LLM_RESPONSE_LIST_SOURCES, {}),
        (WORKER_LLM_RESPONSE_DELEGATE_TO_JULES, {}),
        (MANAGER_LLM_RESPONSE_FINAL, {}),
    ]

    # 2. Mock the tool execution logic
    async def tool_executor(tool_name, args, kwargs, verbose):
        if tool_name == "list_jules_sources":
            return json.dumps({"sources": [{"name": "sources/github/bobalover/boba"}]})
        if tool_name == "delegate_task_to_jules":
            return json.dumps({"status": "success", "session_name": "sessions/12345"})
        return "Default mock response"

    mock_execute_tool.side_effect = tool_executor

    # 3. Run the test
    with patch('core.rich_printer.RichPrinter._post'):
        manager = ConversationalManager()
        manager.initialize = AsyncMock() # Prevent server start
        manager.shutdown = AsyncMock()   # Prevent server stop

        await manager.initialize()

        # Part 1: User starts the process, which should trigger the full HITL flow
        await manager.handle_user_input("Use Jules to create a boba app.")

        assert manager.state == "AWAITING_DELEGATION_APPROVAL"
        assert manager.pending_tool_call['tool_name'] == 'delegate_task_to_jules'

        # Part 2: User approves
        await manager.handle_user_input("yes")

        # The worker's internal loop makes multiple calls. The final, approved call is the one we assert.
        # Worker calls get_main_goal, then list_jules_sources. It loops, calls get_main_goal again,
        # then proposes delegation. The manager then makes the final approved call.
        # The exact count can be brittle, so we focus on finding the correct final call.

        final_delegation_call = None
        for call in mock_execute_tool.call_args_list:
            if call.args[0] == 'delegate_task_to_jules':
                final_delegation_call = call
                break

        assert final_delegation_call is not None, "Expected 'delegate_task_to_jules' to be called after approval."

        # Check the arguments of the final call
        final_kwargs = final_delegation_call.args[2]
        assert final_kwargs['prompt'] == "Create a boba app!"

        assert manager.state == "IDLE"
        await manager.shutdown()

# --- Unit Tests ---

class TestJulesApiServer:
    client = TestClient(jules_api_server.app)

    @patch('mcp_servers.worker.jules_api_server.os.getenv')
    @patch('mcp_servers.worker.jules_api_server.httpx.AsyncClient')
    def test_list_sources_success(self, MockAsyncClient, mock_getenv):
        mock_getenv.return_value = "fake-api-key"
        mock_response = MagicMock(spec=httpx.Response, status_code=200)
        mock_response.json.return_value = {"sources": ["source1"]}
        mock_response.raise_for_status.return_value = None

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        response = self.client.get("/list_jules_sources")
        assert response.status_code == 200
        assert response.json() == {"sources": ["source1"]}

    @patch('mcp_servers.worker.jules_api_server.os.getenv')
    @patch('mcp_servers.worker.jules_api_server.httpx.AsyncClient')
    def test_delegate_task_success(self, MockAsyncClient, mock_getenv):
        mock_getenv.return_value = "fake-api-key"

        mock_response = MagicMock(spec=httpx.Response, status_code=200)
        mock_response.json.return_value = {"name": "sessions/12345"}
        mock_response.raise_for_status.return_value = None

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        payload = {
            "prompt": "Test Prompt",
            "source": "test/source",
            "starting_branch": "main",
            "title": "Test Title"
        }
        response = self.client.post("/delegate_task_to_jules", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["session_name"] == "sessions/12345"

    @patch('mcp_servers.worker.jules_api_server.os.getenv')
    @patch('mcp_servers.worker.jules_api_server.httpx.AsyncClient')
    def test_delegate_task_missing_name_in_response(self, MockAsyncClient, mock_getenv):
        mock_getenv.return_value = "fake-api-key"

        mock_response = MagicMock(spec=httpx.Response, status_code=200)
        mock_response.json.return_value = {"id": "12345"}
        mock_response.raise_for_status.return_value = None

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        payload = {"prompt": "p", "source": "s", "starting_branch": "b", "title": "t"}
        response = self.client.post("/delegate_task_to_jules", json=payload)

        assert response.status_code == 502
        assert "Invalid response from Jules API: 'name' not found" in response.json()["detail"]