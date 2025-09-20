import pytest
from unittest.mock import MagicMock, patch
from agents.tester_agent import TesterAgent
from core.context import SharedContext

@pytest.fixture
def mock_llm():
    """Provides a mock LLM for testing."""
    return MagicMock()

@patch('agents.tester_agent.Crew')
@patch('agents.tester_agent.Task')
@patch('agents.tester_agent.Agent')
def test_run_task_success(MockAgent, MockTask, MockCrew, mock_llm):
    """
    Tests that the run_task method successfully executes the testing crew
    and updates the context with the results.
    """
    # Arrange
    tester_agent = TesterAgent(llm=mock_llm)
    context = SharedContext(
        session_id="test_session",
        original_prompt="test_prompt",
        payload={"code": "def hello():\n    return 'world'"}
    )

    # Mock the crew and its kickoff method to return a successful result
    mock_crew_instance = MockCrew.return_value
    mock_crew_instance.kickoff.return_value = "All tests passed!"

    # Act
    result_context = tester_agent.run_task(context)

    # Assert
    assert "test_results" in result_context.payload
    assert result_context.payload["test_results"] == "All tests passed!"
    MockCrew.assert_called_once()
    mock_crew_instance.kickoff.assert_called_once()

@patch('agents.tester_agent.Agent')
def test_run_task_missing_code(MockAgent, mock_llm):
    """
    Tests that run_task raises a ValueError if 'code' is missing from the context.
    """
    # Arrange
    tester_agent = TesterAgent(llm=mock_llm)
    context = SharedContext(
        session_id="test_session",
        original_prompt="test_prompt",
        payload={}
    )

    # Act & Assert
    with pytest.raises(ValueError, match="The 'code' is missing from the context payload."):
        tester_agent.run_task(context)
