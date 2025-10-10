import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from core.conversational_manager import ConversationalManager
from core.orchestrator import WorkerOrchestrator
from tui.messages import ChatMessage

# Mock response from LLM for the ConversationalManager to decide to delegate
MANAGER_LLM_RESPONSE_DELEGATE = json.dumps({
    "explanation": "The user's request is complex. I will delegate this to the worker.",
    "tool_call": {
        "tool_name": "delegate_task_to_worker",
        "kwargs": {"task": "Implement the feature."}
    }
})

# Mock response from LLM for the ConversationalManager to generate the final response
MANAGER_LLM_RESPONSE_FINAL = json.dumps({
    "explanation": "I will now generate the final response for the user.",
    "tool_call": None
})


@pytest.mark.asyncio
async def test_full_delegation_approval_workflow(monkeypatch):
    """
    Integration test for the complete delegation approval workflow using pytest and monkeypatch.
    """
    # 1. Prepare Mocks
    mock_rich_printer_post = MagicMock()
    monkeypatch.setattr("core.conversational_manager.RichPrinter._post", mock_rich_printer_post)
    monkeypatch.setattr("core.orchestrator.RichPrinter._post", mock_rich_printer_post)

    # Mock the LLM's responses
    mock_llm = AsyncMock()
    mock_llm.generate_content_async.side_effect = [
        (MANAGER_LLM_RESPONSE_DELEGATE, {}),
        (json.dumps({"explanation": "Final response", "tool_call": None}), {}),
        (json.dumps({"explanation": "Final response after approval", "tool_call": None}), {}),
    ]
    mock_llm_manager = MagicMock()
    mock_llm_manager.get_llm.return_value = mock_llm
    monkeypatch.setattr("core.conversational_manager.LLMManager", lambda project_root: mock_llm_manager)
    monkeypatch.setattr("core.orchestrator.LLMManager", lambda project_root: mock_llm_manager)


    # Mock the WorkerOrchestrator's `run` method
    mock_worker_run = AsyncMock(return_value={
        "status": "needs_delegation_approval",
        "summary": "Worker wants to delegate.",
        "tool_call": {
            "tool_name": "delegate_task_to_jules",
            "kwargs": {"task_description": "A very complex task."}
        }
    })
    # We will replace the run method on the actual worker instance later

    # Mock the MCPClient's `execute_tool` method for the final step
    mock_execute_tool = AsyncMock(return_value=json.dumps({"status": "success", "session_id": "jules-session-123"}))


    # 2. Setup Application State
    # We create a real manager and a real worker, but we will mock their methods
    manager = ConversationalManager(project_root=".")
    # This is crucial: replace the `run` method on the *instance* of the worker
    manager.worker.run = mock_worker_run
    # And also mock the execute_tool on the worker's client
    manager.worker.mcp_client.execute_tool = mock_execute_tool


    # 3. Run Test Scenario - Part 1: Proposing Delegation
    await manager.handle_user_input("Please implement this complex feature.")
    await asyncio.sleep(0.01) # Allow async tasks to complete

    # 4. Assertions - Part 1
    mock_worker_run.assert_awaited_once()

    # Check that the user was asked for permission
    mock_rich_printer_post.assert_called()
    found_ask_message = False
    for call in mock_rich_printer_post.call_args_list:
        message_obj = call.args[0]
        if isinstance(message_obj, ChatMessage) and isinstance(message_obj.content, str) and "Souhlasíte s tímto postupem?" in message_obj.content:
            found_ask_message = True
            break
    assert found_ask_message, "The message asking for delegation approval was not sent."
    assert manager.state == "AWAITING_DELEGATION_APPROVAL"


    # 5. Run Test Scenario - Part 2: User Approves
    await manager.handle_user_input("ano")
    await asyncio.sleep(0.01)

    # 6. Assertions - Part 2
    # Check that the final tool was executed with the correct arguments
    mock_execute_tool.assert_awaited_once_with(
        'delegate_task_to_jules',
        [],
        {'task_description': 'A very complex task.'},
        False
    )
    assert manager.state == "IDLE"

    # Clean up
    await manager.shutdown()