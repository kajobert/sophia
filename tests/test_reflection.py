import pytest
import os
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

# Sestavení správné cesty k 'core'
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.conversational_manager import ConversationalManager

# --- Testovací Fixtures ---

@pytest.fixture
def temp_project_root(tmp_path):
    """Vytvoří dočasný kořenový adresář projektu pro izolované testy."""
    (tmp_path / "prompts").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "db").mkdir()
    with open(tmp_path / "prompts/system_prompt.txt", "w") as f:
        f.write("You are a worker agent.")
    with open(tmp_path / "prompts/manager_prompt.txt", "w") as f:
        f.write("You are a manager agent.")
    with open(tmp_path / "prompts/reflection_prompt.txt", "w") as f:
        f.write("Analyze history: {task_history}. Produce one learning.")
    with open(tmp_path / "config/config.yaml", "w") as f:
        f.write("""
llm_models:
  default: 'mock_model'
  options:
    mock_model:
      adapter: 'MockLLM'
      config: {}
vector_database:
  path: 'db/test_chroma.db'
  collection_name: 'test_collection'
""")
    with open(tmp_path / ".env", "w") as f:
        f.write("OPENROUTER_API_KEY=dummy_key_for_testing\n")
    return str(tmp_path)


@pytest.fixture
async def mission_manager_with_mocks(temp_project_root):
    """
    Provides a MissionManager instance with mocked dependencies to test the
    reflection cycle in the new architecture.
    """
    # The patch needs to target where the `LLMManager` is *used*.
    # In this case, it's used inside the `ConversationalManager`.
    with patch('core.mission_manager.ConversationalManager') as MockConvManager, \
         patch('core.mission_manager.ReflectionServer') as MockReflectionServer, \
         patch('core.mission_manager.PlanningServer') as MockPlanningServer:

        # Mock the LLM used by MissionManager for planning.
        # It's accessed via `conversational_manager.llm_manager`.
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_content_async = AsyncMock(return_value=(
            json.dumps(["Create a directory"]), {}
        ))
        mock_conv_manager_instance = MockConvManager.return_value
        mock_conv_manager_instance.llm_manager.get_llm.return_value = mock_llm_instance

        # Mock the worker's LTM, accessed via conversational_manager.worker.ltm
        # We need to ensure the mock is passed through correctly.
        mock_ltm_instance = MagicMock()
        mock_conv_manager_instance.worker.ltm.add = mock_ltm_instance.add

        # Mock the handle_task method for the execution phase
        mock_conv_manager_instance.handle_task = AsyncMock(return_value={
            "status": "completed", "summary": "Directory created.", "history": [], "touched_files": ["a.txt"]
        })
        mock_conv_manager_instance.generate_final_response = AsyncMock(return_value="Mission complete.")

        # Mock ReflectionServer
        mock_reflection_server_instance = MockReflectionServer.return_value
        mock_reflection_server_instance.summarize_mission_learnings = AsyncMock(return_value="High-level mission learning.")

        # Mock ReflectionServer
        mock_planning_server_instance = MockPlanningServer.return_value

        # Mock ReflectionServer
        mock_reflection_server_instance = MockReflectionServer.return_value
        mock_reflection_server_instance.summarize_mission_learnings = AsyncMock(return_value="High-level mission learning.")

        # Import must be here to use the temp_project_root
        from core.mission_manager import MissionManager
        manager = MissionManager(project_root=temp_project_root)
        manager.conversational_manager = mock_conv_manager_instance
        manager.reflection_server = mock_reflection_server_instance
        manager.planning_server = mock_planning_server_instance # Assign the mock

        # We don't need a full async init/shutdown as dependencies are mocked
        manager.initialize = AsyncMock()
        manager.shutdown = AsyncMock()
        await manager.initialize()

        # This test no longer needs to manually set the sub_tasks, as the `_create_initial_plan` mock handles it.
        yield manager, mock_reflection_server_instance, mock_ltm_instance
        await manager.shutdown()

# --- Test Scenario ---

@pytest.mark.asyncio
async def test_final_reflection_uses_correct_method(mission_manager_with_mocks):
    """
    Verifies that after a mission is completed, the new high-level reflection
    method is called and its learning is saved to the LTM.
    """
    mission_manager, mock_reflection_server, mock_ltm = mission_manager_with_mocks

    # Start the mission, which will internally call the mocked `_create_initial_plan`
    await mission_manager.start_mission("Create `test_dir` directory.")
    # Manually set the sub_tasks after the plan has been created
    mission_manager.sub_tasks = [{"id": 1, "description": "Create a directory", "completed": False}]
    # Now run the loop
    await mission_manager._run_mission_loop()

    # 1. Verify that the new high-level reflection server method was called correctly
    mock_reflection_server.summarize_mission_learnings.assert_called_once()
    call_args, call_kwargs = mock_reflection_server.summarize_mission_learnings.call_args
    assert call_kwargs['mission_goal'] == "Create `test_dir` directory."
    history_string = call_kwargs['history']
    assert "MISSION GOAL: Create `test_dir` directory." in history_string
    assert "WORKER RESULT: Directory created." in history_string

    # 2. Verify the old, incorrect method was NOT called for the final reflection
    # (it might be called for sub-task failures, but not here)
    # In this successful run, it shouldn't be called at all.
    mock_reflection_server.reflect_on_recent_steps.assert_not_called()


    # 3. Verify that the LTM 'add' method was called with the correct data
    mock_ltm.add.assert_called_once()
    args, kwargs = mock_ltm.add.call_args
    assert "documents" in kwargs and "High-level mission learning." in kwargs["documents"][0]
    assert "metadatas" in kwargs and kwargs['metadatas'][0]['type'] == 'learning'

    print("Test passed: Final reflection uses the correct high-level method.")