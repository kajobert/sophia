import pytest
from unittest.mock import MagicMock, patch

from core.neocortex import Neocortex
from core.cognitive_layers import ReptilianBrain, MammalianBrain
from core.memory_systems import ShortTermMemory
from agents.planner_agent import PlannerAgent
from core.context import SharedContext

# --- Fixtures ---


@pytest.fixture
def mock_reptilian_brain():
    brain = MagicMock(spec=ReptilianBrain)
    brain.process_input.return_value = {"original_input": "test", "safety_passed": True}
    return brain


@pytest.fixture
def mock_mammalian_brain():
    brain = MagicMock(spec=MammalianBrain)
    brain.process_input.side_effect = lambda data: {**data, "relevant_memories": []}
    return brain


@pytest.fixture
def mock_stm():
    """Mocks the ShortTermMemory, using a simple dict as an in-memory store."""
    memory = MagicMock(spec=ShortTermMemory)
    _store = {}

    def save_state(session_id, state):
        _store[session_id] = state

    def load_state(session_id):
        return _store.get(session_id)

    memory.save_state.side_effect = save_state
    memory.load_state.side_effect = load_state
    return memory


@pytest.fixture
def mock_planner():
    planner = MagicMock(spec=PlannerAgent)
    # Default behavior: return a simple plan
    plan_context = SharedContext(session_id="test_session", original_prompt="test")
    plan_context.payload["plan"] = [
        {"step_id": 1, "tool_name": "MockTool", "parameters": {}}
    ]
    planner.run_task.return_value = plan_context
    return planner


@pytest.fixture
def neocortex(mock_reptilian_brain, mock_mammalian_brain, mock_stm, mock_planner):
    """Fixture to create a Neocortex instance with mocked dependencies."""
    with patch.object(Neocortex, "_load_tools", return_value={"MockTool": MagicMock()}):
        nctx = Neocortex(
            reptilian_brain=mock_reptilian_brain,
            mammalian_brain=mock_mammalian_brain,
            short_term_memory=mock_stm,
            planner=mock_planner,
        )
        # Configure the mock tool to succeed by default
        nctx.tools["MockTool"].execute.return_value = "Success"
        yield nctx


# --- Test Cases ---


@pytest.mark.asyncio
async def test_process_input_and_successful_execution(
    neocortex, mock_reptilian_brain, mock_mammalian_brain, mock_planner, mock_stm
):
    """
    Tests the full flow from receiving input to successful plan execution.
    """
    session_id = "session1"
    user_input = "Do a simple task."

    # Act
    await neocortex.process_input(session_id, user_input)

    # Assert
    # 1. Cognitive layers were called
    mock_reptilian_brain.process_input.assert_called_once_with(user_input)
    mock_mammalian_brain.process_input.assert_called_once()

    # 2. Planner was called
    mock_planner.run_task.assert_called_once()

    # 3. State was saved
    mock_stm.save_state.assert_called()
    final_state = mock_stm.load_state(session_id)
    assert final_state is not None

    # 4. Tool was executed
    neocortex.tools["MockTool"].execute.assert_called_once_with()

    # 5. History shows success
    assert len(final_state["step_history"]) == 1
    assert final_state["step_history"][0]["output"]["status"] == "success"


@pytest.mark.asyncio
async def test_execution_with_failure_and_repair(neocortex, mock_planner, mock_stm):
    """
    Tests that the Neocortex can handle a tool failure, trigger the planner
    for a new plan, and execute the new plan successfully.
    """
    session_id = "session2"
    user_input = "This will fail then succeed."

    # --- Arrange ---
    # 1. Configure the mock tool to fail once, then succeed
    neocortex.tools["MockTool"].execute.side_effect = [
        Exception("Tool failed!"),
        "Success on the second try",
    ]

    # 2. Configure the planner
    # The initial plan that will fail
    initial_plan_ctx = SharedContext(session_id=session_id, original_prompt=user_input)
    initial_plan_ctx.payload["plan"] = [
        {
            "step_id": 1,
            "tool_name": "MockTool",
            "description": "This will fail",
            "parameters": {},
        }
    ]

    # The repaired plan that will succeed
    repaired_plan_ctx = SharedContext(
        session_id=session_id, original_prompt="repair prompt"
    )
    repaired_plan_ctx.payload["plan"] = [
        {
            "step_id": 1,
            "tool_name": "MockTool",
            "description": "This will succeed",
            "parameters": {},
        }
    ]

    mock_planner.run_task.side_effect = [initial_plan_ctx, repaired_plan_ctx]

    # --- Act ---
    await neocortex.process_input(session_id, user_input)

    # --- Assert ---
    # 1. Planner was called twice (initial plan + repair)
    assert mock_planner.run_task.call_count == 2

    # 2. Tool was called twice
    assert neocortex.tools["MockTool"].execute.call_count == 2

    # 3. Check final state
    final_state = mock_stm.load_state(session_id)
    assert final_state["repair_attempts"] == 1
    assert len(final_state["step_history"]) == 1  # History was reset for the new plan
    assert final_state["step_history"][0]["output"]["status"] == "success"
    assert (
        final_state["step_history"][0]["output"]["result"]
        == "Success on the second try"
    )
