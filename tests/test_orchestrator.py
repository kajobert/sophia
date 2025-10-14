import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from core.orchestrator import NomadOrchestrator
from core.state_manager import State # Import the real State enum

@pytest.fixture
def mock_dependencies():
    """Mocks all external dependencies for the orchestrator."""
    with patch('core.orchestrator.StateManager') as MockStateManager, \
         patch('core.orchestrator.RichPrinter') as MockRichPrinter, \
         patch('core.orchestrator.MCPClient') as MockMCPClient:

        # Configure the mock instances
        mock_state_manager_instance = MockStateManager.return_value
        mock_state_manager_instance.restore.return_value = False # Default to no restore
        mock_state_manager_instance.current_state.value = "mock_state_value" # Default value

        mock_mcp_client_instance = MockMCPClient.return_value
        mock_mcp_client_instance.shutdown = AsyncMock()

        yield {
            "StateManager": MockStateManager,
            "RichPrinter": MockRichPrinter,
            "MCPClient": MockMCPClient,
            "state_manager_instance": mock_state_manager_instance,
            "mcp_client_instance": mock_mcp_client_instance
        }

def test_initialization_new_session(mock_dependencies):
    """Test orchestrator initialization for a new session."""
    orchestrator = NomadOrchestrator(project_root="/test")

    mock_dependencies["StateManager"].assert_called_once_with("/test", None)
    # restore() is only called if session_id is provided
    mock_dependencies["state_manager_instance"].restore.assert_not_called()
    mock_dependencies["RichPrinter"].info.assert_any_call("Starting a new session.")

def test_initialization_restore_session_success(mock_dependencies):
    """Test orchestrator initialization with a successful session restore."""
    mock_sm_instance = mock_dependencies["state_manager_instance"]
    mock_sm_instance.restore.return_value = True
    mock_sm_instance.current_state.value = "restored_state" # Set a predictable value

    orchestrator = NomadOrchestrator(project_root="/test", session_id="test_session_123")

    mock_dependencies["StateManager"].assert_called_once_with("/test", "test_session_123")
    mock_sm_instance.restore.assert_called_once()
    # Assert with the predictable value
    mock_dependencies["RichPrinter"].info.assert_any_call("Restored session test_session_123. Current state: restored_state")

def test_initialization_restore_session_failure(mock_dependencies):
    """Test orchestrator initialization when session restore fails."""
    # Restore is false by default in the fixture
    orchestrator = NomadOrchestrator(project_root="/test", session_id="test_session_456")

    mock_dependencies["StateManager"].assert_called_once_with("/test", "test_session_456")
    mock_dependencies["state_manager_instance"].restore.assert_called_once()
    mock_dependencies["RichPrinter"].info.assert_any_call("Starting a new session.")

@pytest.mark.asyncio
async def test_shutdown_sequence(mock_dependencies):
    """Test that the shutdown sequence is called correctly."""
    orchestrator = NomadOrchestrator(project_root="/test")

    await orchestrator.shutdown()

    mock_dependencies["mcp_client_instance"].shutdown.assert_awaited_once()
    mock_dependencies["state_manager_instance"].persist.assert_called_once()
    mock_dependencies["RichPrinter"].info.assert_any_call("Shutting down orchestrator...")
    mock_dependencies["RichPrinter"].info.assert_any_call("Orchestrator shutdown complete.")

@pytest.mark.asyncio
async def test_run_with_initial_prompt(mock_dependencies):
    """Test the basic run logic with an initial prompt."""
    orchestrator = NomadOrchestrator(project_root="/test")

    await orchestrator.run(initial_prompt="Hello, world!")

    # Verify that the prompt triggers a transition to PLANNING using the REAL enum
    mock_dependencies["state_manager_instance"].transition_to.assert_called_once_with(
        State.PLANNING, # Use the real enum member
        reason="Initial prompt received."
    )
    mock_dependencies["RichPrinter"].info.assert_any_call("Received initial prompt: Hello, world!")