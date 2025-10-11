import json
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
import httpx
from fastapi.testclient import TestClient

from core.conversational_manager import ConversationalManager
from mcp_servers.worker import jules_api_server

# --- Mocks for Integration Test ---
MANAGER_LLM_RESPONSE_TRIAGE = json.dumps({
    "type": "complex",
    "budget": 10
})
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
# Updated mock to include optional parameters
WORKER_LLM_RESPONSE_DELEGATE_TO_JULES_FULL = json.dumps({
    "explanation": "Now that I have a source, I will delegate the task to Jules with specific options.",
    "tool_call": {
        "tool_name": "delegate_task_to_jules",
        "kwargs": {
            "prompt": "Create a boba app!",
            "source": "sources/github/bobalover/boba",
            "starting_branch": "main",
            "title": "Boba App",
            "requirePlanApproval": True,
            "automationMode": "AUTO_CREATE_PR"
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
async def test_end_to_end_delegation_with_optional_params(mock_execute_tool, mock_llm_generate, mock_init_client):
    mock_llm_generate.side_effect = [
        (MANAGER_LLM_RESPONSE_TRIAGE, {}), # New triage step
        (MANAGER_LLM_RESPONSE_DELEGATE_TO_WORKER, {}),
        (WORKER_LLM_RESPONSE_LIST_SOURCES, {}),
        (WORKER_LLM_RESPONSE_DELEGATE_TO_JULES_FULL, {}),
        (MANAGER_LLM_RESPONSE_FINAL, {}),
    ]
    async def tool_executor(tool_name, args, kwargs, verbose=False):
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

        # Assert that the optional parameters made it to the final tool call
        final_kwargs = final_delegation_call.args[2]
        assert final_kwargs['prompt'] == "Create a boba app!"
        assert final_kwargs['requirePlanApproval'] is True
        assert final_kwargs['automationMode'] == "AUTO_CREATE_PR"

        assert manager.state == "IDLE"
        await manager.shutdown()
