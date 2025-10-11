import json
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from core.conversational_manager import ConversationalManager
from core.orchestrator import WorkerOrchestrator
from core.mcp_client import MCPClient

# --- Mocks for Integration Test ---
MANAGER_LLM_RESPONSE_TRIAGE = json.dumps({"type": "complex", "budget": 10})
MANAGER_LLM_RESPONSE_DELEGATE_TO_WORKER = json.dumps({
    "thought": "This is a complex task. I will delegate to the Worker.",
    "tool_call": {"tool_name": "delegate_task_to_worker", "kwargs": {"task": "Delegate to Jules."}}
})
WORKER_LLM_RESPONSE_DELEGATE_TO_JULES = json.dumps({
    "thought": "I need to delegate this task to the external Jules API.",
    "tool_call": {"tool_name": "delegate_task_to_jules", "kwargs": {"prompt": "Create a boba app!"}}
})
MANAGER_LLM_RESPONSE_FINAL_APPROVAL = json.dumps({
    "thought": "The delegation was approved. I will inform the user.",
    "tool_call": {"tool_name": "inform_user", "kwargs": {"message": "Delegation approved and sent to Jules."}}
})

@pytest.fixture
def mock_mcp_client():
    """Fixture to create a mock MCPClient."""
    mock_client = MagicMock(spec=MCPClient)
    mock_client.start_servers = AsyncMock()
    mock_client.shutdown_servers = AsyncMock()
    mock_client.get_tool_descriptions = AsyncMock(return_value="Mocked tool descriptions")

    async def execute_tool_side_effect(tool_name, args, kwargs, verbose):
        if tool_name == "delegate_task_to_jules":
            return json.dumps({"status": "success", "session_name": "sessions/12345"})
        return "{}" # Default empty JSON for other tools

    mock_client.execute_tool = AsyncMock(side_effect=execute_tool_side_effect)
    return mock_client

@pytest.mark.asyncio
@patch('core.conversational_manager.LLMManager')
@patch('core.conversational_manager.WorkerOrchestrator')
async def test_delegation_workflow(MockWorkerOrchestrator, MockLLMManager):
    """
    Tests the full delegation workflow from ConversationalManager to WorkerOrchestrator
    and back, ensuring the state machine and mocks work correctly.
    """
    # --- Mocks Setup ---
    # Mock LLM for ConversationalManager
    mock_manager_llm = MagicMock()
    # IMPORTANT: The mock must be an AsyncMock to be awaitable
    mock_manager_llm.generate_content_async = AsyncMock(side_effect=[
        (MANAGER_LLM_RESPONSE_TRIAGE, {}),
        (MANAGER_LLM_RESPONSE_DELEGATE_TO_WORKER, {}),
        (MANAGER_LLM_RESPONSE_FINAL_APPROVAL, {})
    ])
    MockLLMManager.return_value.get_llm.return_value = mock_manager_llm

    # Mock WorkerOrchestrator instance and its run method
    mock_worker_instance = MagicMock(spec=WorkerOrchestrator)
    mock_worker_instance.run = AsyncMock(return_value={
        "status": "needs_delegation_approval",
        "summary": "Worker wants to delegate.",
        "tool_call": json.loads(WORKER_LLM_RESPONSE_DELEGATE_TO_JULES)["tool_call"],
        "history": []
    })

    # The manager will call worker.mcp_client.execute_tool, so we need to mock this
    mock_worker_mcp_client = MagicMock(spec=MCPClient)
    mock_worker_mcp_client.execute_tool = AsyncMock(return_value=json.dumps({"status": "success"}))
    mock_worker_instance.mcp_client = mock_worker_mcp_client

    MockWorkerOrchestrator.return_value = mock_worker_instance

    # --- Test Execution ---
    manager = ConversationalManager()
    # We don't need real initialization/shutdown as services are mocked
    manager.initialize = AsyncMock()
    manager.shutdown = AsyncMock()
    await manager.initialize()

    # 1. User initiates the task
    await manager.handle_user_input("Use Jules to create a boba app.")

    # Assert that the manager delegated to the worker
    mock_worker_instance.run.assert_called_once()
    assert manager.state == "AWAITING_DELEGATION_APPROVAL"
    assert manager.pending_tool_call is not None

    # 2. User approves the delegation
    await manager.handle_user_input("yes")

    # Assert that the manager called the final tool
    # Check that the final LLM call for the manager happened
    assert mock_manager_llm.generate_content_async.call_count == 3

    # Assert state is reset
    assert manager.state == "IDLE"
    await manager.shutdown()
