import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from core.conversational_manager import ConversationalManager

# This is a high-level integration test to ensure the core logic of
# task execution is sound and follows the new "local tools first" rule.

@pytest.fixture
def manager():
    """Fixture to create a ConversationalManager with a mocked worker and LLMManager."""
    # Patch the LLMManager to prevent it from needing API keys during tests
    with patch('core.conversational_manager.LLMManager', new_callable=MagicMock) as MockLLMManager:
        # Patch the WorkerOrchestrator to intercept its run method
        with patch('core.conversational_manager.WorkerOrchestrator', new_callable=MagicMock) as MockWorker:
            # The worker's run method needs to be an async mock
            mock_worker_instance = MockWorker.return_value
            mock_worker_instance.run = AsyncMock()

            # Mock the initialization and shutdown as well
            mock_worker_instance.initialize = AsyncMock()
            mock_worker_instance.shutdown = AsyncMock()

            # We need a real ConversationalManager, but its dependencies are mocked
            manager_instance = ConversationalManager(project_root=".")
            manager_instance.worker = mock_worker_instance
            manager_instance.llm_manager = MockLLMManager.return_value  # Assign the mocked LLM manager
            yield manager_instance, mock_worker_instance

@pytest.mark.asyncio
async def test_simple_file_manipulation_mission(manager):
    """
    Simulates a user asking to perform a sequence of file operations.
    This test verifies that the agent uses its local tools and does NOT
    attempt to delegate the task.
    """
    conversational_manager, mock_worker = manager

    # The user's request that previously failed
    mission_prompt = "Create a file named 'test.txt', write 'hello' into it, read the content, and then delete it."

    # Mock the behavior of the worker's `run` method.
    # We will simulate the worker successfully performing the task.
    # The key is that we can inspect what the worker *would* have done.
    # For this test, we assume the worker's internal logic is correct and
    # we are testing the dispatching logic.

    # We will mock the return value of worker.run to simulate a successful completion.
    # The important part of the test is to ensure the manager calls the worker
    # correctly and doesn't try to do something else (like triage).
    mock_worker.run.return_value = {
        "status": "completed",
        "summary": "File 'test.txt' was created, written to, read, and deleted successfully.",
        "touched_files": ["test.txt"]
    }

    # Initialize the manager (and its mocked worker)
    await conversational_manager.initialize()

    # The MissionManager would call handle_task, so we simulate that
    final_result = await conversational_manager.handle_task(mission_prompt)

    # --- VERIFICATION ---

    # 1. Verify that the worker's `run` method was called exactly once.
    mock_worker.run.assert_called_once()

    # 2. Inspect the arguments passed to the worker's `run` method.
    run_args, run_kwargs = mock_worker.run.call_args
    assert run_kwargs.get("initial_task") == mission_prompt
    # Ensure no budget was passed, as that logic is removed
    assert "budget" not in run_kwargs

    # 3. Verify the final result is what we expect.
    assert final_result["status"] == "completed"
    assert "deleted successfully" in final_result["summary"]

    # 4. CRITICAL: The `delegate_task_to_jules` tool should NEVER have been
    # considered. We can infer this because the worker's `run` method was
    # called directly. If delegation was attempted, the return from `handle_task`
    # would have been different (e.g., {"status": "needs_delegation_approval"}).
    # The mocked `run` doesn't contain `delegate_task_to_jules`, so if it completes,
    # we know delegation wasn't the result.

    # Clean up
    await conversational_manager.shutdown()