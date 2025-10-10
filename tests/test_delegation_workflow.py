import json
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
import httpx
from fastapi.testclient import TestClient

from core.conversational_manager import ConversationalManager
from mcp_servers.worker import jules_api_server

# --- Mocks for Integration Test ---
MANAGER_LLM_RESPONSE_DELEGATE_TO_WORKER = json.dumps({
    "explanation": "This is a complex task that requires tools. I will delegate to the Worker.",
    "tool_call": {
        "tool_name": "delegate_task_to_worker",
        "kwargs": {"task": "Use Jules to create a boba app."}
    }
})
WORKER_LLM_RESPONSE_LIST_SOURCES = json.dumps({
    "explanation": "To use the Jules API, I first need to know the available source. I will list them.",
    "tool_call": {"tool_name": "list_jules_sources", "kwargs": {}}
})
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
MANAGER_LLM_RESPONSE_FINAL = json.dumps({
    "explanation": "The delegation was approved and executed successfully. I will inform the user.",
    "tool_call": None
})

# --- Integration Test ---
@pytest.mark.asyncio
@patch('core.llm_manager.LLMManager._initialize_client', return_value=None)
@patch('core.llm_adapters.OpenRouterAdapter.generate_content_async')
@patch('core.mcp_client.MCPClient.execute_tool')
async def test_end_to_end_delegation_with_approval(mock_execute_tool, mock_llm_generate, mock_init_client):
    mock_llm_generate.side_effect = [
        (MANAGER_LLM_RESPONSE_DELEGATE_TO_WORKER, {}),
        (WORKER_LLM_RESPONSE_LIST_SOURCES, {}),
        (WORKER_LLM_RESPONSE_DELEGATE_TO_JULES, {}),
        (MANAGER_LLM_RESPONSE_FINAL, {}),
    ]
    async def tool_executor(tool_name, args, kwargs, verbose):
        if tool_name == "list_jules_sources":
            return json.dumps({"sources": [{"name": "sources/github/bobalover/boba"}]})
        if tool_name == "delegate_task_to_jules":
            return json.dumps({"status": "success", "session_name": "sessions/12345"})
        return "Default mock response"
    mock_execute_tool.side_effect = tool_executor

    with patch('core.rich_printer.RichPrinter._post'):
        manager = ConversationalManager()
        manager.initialize = AsyncMock()
        manager.shutdown = AsyncMock()
        await manager.initialize()

        await manager.handle_user_input("Use Jules to create a boba app.")
        assert manager.state == "AWAITING_DELEGATION_APPROVAL"

        await manager.handle_user_input("yes")
        final_delegation_call = next((c for c in mock_execute_tool.call_args_list if c.args[0] == 'delegate_task_to_jules'), None)
        assert final_delegation_call is not None
        assert final_delegation_call.args[2]['prompt'] == "Create a boba app!"
        assert manager.state == "IDLE"
        await manager.shutdown()

# --- Unit Tests ---
class TestJulesApiServer:
    client = TestClient(jules_api_server.app)

    MOCK_CONFIG = {
        "jules_api": {
            "base_url": "https://test.jules.api",
            "list_sources_timeout": 5.0,
            "delegate_task_timeout": 10.0
        }
    }

    @patch('mcp_servers.worker.jules_api_server.load_config')
    @patch('mcp_servers.worker.jules_api_server.os.getenv')
    @patch('mcp_servers.worker.jules_api_server.httpx.AsyncClient')
    def test_list_sources_success(self, MockAsyncClient, mock_getenv, mock_load_config):
        mock_load_config.return_value = self.MOCK_CONFIG
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

        mock_client_instance.get.assert_called_once()
        # Correctly check the positional argument for the URL
        assert mock_client_instance.get.call_args.args[0] == "https://test.jules.api/sources"
        assert mock_client_instance.get.call_args.kwargs['timeout'] == 5.0

    @patch('mcp_servers.worker.jules_api_server.load_config')
    @patch('mcp_servers.worker.jules_api_server.os.getenv')
    @patch('mcp_servers.worker.jules_api_server.httpx.AsyncClient')
    def test_delegate_task_success(self, MockAsyncClient, mock_getenv, mock_load_config):
        mock_load_config.return_value = self.MOCK_CONFIG
        mock_getenv.return_value = "fake-api-key"

        mock_response = MagicMock(spec=httpx.Response, status_code=200)
        mock_response.json.return_value = {"name": "sessions/12345"}
        mock_response.raise_for_status.return_value = None

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        MockAsyncClient.return_value.__aenter__.return_value = mock_client_instance

        payload = {"prompt": "p", "source": "s", "starting_branch": "b", "title": "t"}
        response = self.client.post("/delegate_task_to_jules", json=payload)

        assert response.status_code == 200
        assert response.json()["session_name"] == "sessions/12345"

        mock_client_instance.post.assert_called_once()
        # Correctly check the positional argument for the URL
        assert mock_client_instance.post.call_args.args[0] == "https://test.jules.api/sessions"
        assert mock_client_instance.post.call_args.kwargs['timeout'] == 10.0