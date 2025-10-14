import pytest
import os
import json
from unittest.mock import patch, mock_open

from core.state_manager import StateManager, State, StateTransitionError

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root with a memory directory."""
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    return str(tmp_path)

def test_initialization(temp_project_root):
    """Test that the StateManager initializes correctly."""
    sm = StateManager(project_root=temp_project_root)
    assert sm.current_state == State.AWAITING_USER_INPUT
    assert sm.session_id is not None
    assert sm.session_file == os.path.join(temp_project_root, "memory", "session.json")

def test_valid_transition(temp_project_root):
    """Test a valid state transition."""
    sm = StateManager(project_root=temp_project_root)
    sm.transition_to(State.PLANNING, "User submitted a prompt.")
    assert sm.current_state == State.PLANNING
    assert len(sm.history) == 1
    assert sm.history[0]["to"] == "planning"

def test_invalid_transition(temp_project_root):
    """Test that an invalid state transition raises an error."""
    sm = StateManager(project_root=temp_project_root)
    sm.current_state = State.EXECUTING_STEP
    with pytest.raises(StateTransitionError) as excinfo:
        sm.transition_to(State.PLANNING)
    assert "Invalid transition from executing_step to planning" in str(excinfo.value)

def test_set_and_get_data(temp_project_root):
    """Test setting and getting state data."""
    sm = StateManager(project_root=temp_project_root)
    sm.set_data("test_key", {"value": 123})
    retrieved_data = sm.get_data("test_key")
    assert retrieved_data == {"value": 123}
    assert sm.get_data("non_existent_key", "default") == "default"

@patch("builtins.open", new_callable=mock_open)
@patch("os.makedirs")
def test_persistence(mock_makedirs, mock_file, temp_project_root):
    """Test that the state is persisted to a file correctly."""
    sm = StateManager(project_root=temp_project_root, session_id="test_session")

    # Set data and transition state, each of which calls persist
    sm.set_data("plan", {"goal": "Test persistence"})
    sm.transition_to(State.PLANNING)

    # Verify open was called for the session file
    mock_file.assert_called_with(sm.session_file, 'w', encoding='utf-8')

    # Reconstruct the full written string from all write calls
    handle = mock_file()
    # json.dump with indent writes in chunks, so we must join them.
    # The mock file is opened twice, so we need to get the writes from the second call.
    # This is tricky. A better way is to clear mocks between operations.
    handle.reset_mock()

    # Call the method that persists one final time to have a clean mock
    sm.persist()

    written_content = "".join(call.args[0] for call in handle.write.call_args_list)
    written_data = json.loads(written_content)

    # Assertions on the final persisted state
    assert written_data["session_id"] == "test_session"
    assert written_data["current_state"] == "planning"
    assert written_data["plan"]["goal"] == "Test persistence"
    assert len(written_data["history"]) == 1
    assert written_data["history"][0]["to"] == "planning"

def test_restore_file_not_found(temp_project_root):
    """Test that restore returns False if the session file doesn't exist."""
    sm = StateManager(project_root=temp_project_root)
    assert not sm.restore()

def test_restore_success(temp_project_root):
    """Test successfully restoring state from a file."""
    session_data = {
        "session_id": "restored_session",
        "current_state": "executing_step",
        "plan": {"goal": "Restore me"},
        "history": [{"from": "planning", "to": "executing_step"}],
        "last_updated": "2023-10-27T10:00:00"
    }
    session_file = os.path.join(temp_project_root, "memory", "session.json")
    with open(session_file, 'w') as f:
        json.dump(session_data, f)

    sm = StateManager(project_root=temp_project_root)
    assert sm.restore()

    assert sm.session_id == "restored_session"
    assert sm.current_state == State.EXECUTING_STEP
    assert sm.get_data("plan")["goal"] == "Restore me"
    assert len(sm.history) == 1
    assert sm.history[0]["to"] == "executing_step"