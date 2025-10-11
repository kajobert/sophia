import pytest
import os
import asyncio
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
    with patch('core.mission_manager.ConversationalManager') as MockConvManager, \
         patch('core.mission_manager.PlanningServer') as MockPlanningServer, \
         patch('core.mission_manager.ReflectionServer') as MockReflectionServer, \
         patch('core.orchestrator.LongTermMemory') as MockLTM:

        # Mock ConversationalManager
        mock_conv_manager_instance = MockConvManager.return_value
        mock_conv_manager_instance.handle_task = AsyncMock(side_effect=[
            # 1. Result for the planning task
            {"status": "completed", "summary": "Plan created."},
            # 2. Result for the actual sub-task
            {"status": "completed", "summary": "Directory created.", "history": ["Step 1", "Step 2"], "touched_files": ["a.txt"]}
        ])
        mock_conv_manager_instance.generate_final_response = AsyncMock(return_value="Mission complete.")
        # Mock the worker's LTM instance which is accessed via the conv manager
        mock_ltm_instance = MockLTM.return_value
        mock_ltm_instance.add = MagicMock()
        # Create a mock worker and attach the mock LTM to it
        mock_worker = MagicMock()
        mock_worker.ltm = mock_ltm_instance
        mock_conv_manager_instance.worker = mock_worker


        # Mock PlanningServer
        mock_planning_server_instance = MockPlanningServer.return_value
        mock_planning_server_instance.get_next_executable_task.return_value = {"id": 1, "description": "Create a plan"}
        mock_planning_server_instance.get_all_tasks.return_value = [{"id": 2, "description": "Create a directory", "completed": False}]

        # Mock ReflectionServer
        mock_reflection_server_instance = MockReflectionServer.return_value
        mock_reflection_server_instance.reflect_on_recent_steps = AsyncMock(return_value="Sub-task learning.")
        # Mock the new high-level reflection method
        mock_reflection_server_instance.summarize_mission_learnings = AsyncMock(return_value="High-level mission learning.")

        # Import must be here to use the temp_project_root
        from core.mission_manager import MissionManager
        manager = MissionManager(project_root=temp_project_root)
        manager.conversational_manager = mock_conv_manager_instance
        manager.planning_server = mock_planning_server_instance
        manager.reflection_server = mock_reflection_server_instance

        # We don't need a full async init/shutdown as dependencies are mocked
        manager.initialize = AsyncMock()
        manager.shutdown = AsyncMock()
        await manager.initialize()

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

    # Start the mission
    await mission_manager.start_mission("Create `test_dir` directory.")

    # 1. Verify that the new high-level reflection server method was called correctly
    mock_reflection_server.summarize_mission_learnings.assert_called_once()
    call_args, call_kwargs = mock_reflection_server.summarize_mission_learnings.call_args
    assert call_kwargs['mission_goal'] == "Create `test_dir` directory."
    assert "MISSION GOAL: Create `test_dir` directory." in call_kwargs['history']
    assert "WORKER RESULT: Directory created." in call_kwargs['history']

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