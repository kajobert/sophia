import pytest
import logging
from unittest.mock import AsyncMock
from plugins.cognitive_planner import Planner
from core.context import SharedContext


@pytest.fixture
def planner():
    """Fixture for the Planner plugin."""
    return Planner()


@pytest.mark.asyncio
async def test_planner_execute_returns_shared_context(planner):
    """Test that the execute method returns a SharedContext object."""
    # Arrange
    context = SharedContext(
        session_id="test",
        user_input="test",
        current_state="PLANNING",
        logger=logging.getLogger("test"),
    )
    planner.llm_tool = AsyncMock()
    planner.llm_tool.execute.return_value = SharedContext(
        session_id="test",
        user_input="test",
        current_state="PLANNING",
        logger=logging.getLogger("test"),
        payload={"llm_response": '{"plan": []}'},
    )

    # Act
    result = await planner.execute(context)

    # Assert
    assert isinstance(result, SharedContext)


@pytest.mark.asyncio
async def test_planner_execute_handles_no_user_input(planner):
    """Test that the execute method handles no user input."""
    # Arrange
    context = SharedContext(
        session_id="test", current_state="PLANNING", logger=logging.getLogger("test")
    )

    # Act
    result = await planner.execute(context)

    # Assert
    assert result is context


@pytest.mark.asyncio
async def test_planner_execute_handles_no_llm_tool(planner):
    """Test that the execute method handles no llm_tool."""
    # Arrange
    context = SharedContext(
        session_id="test",
        user_input="test",
        current_state="PLANNING",
        logger=logging.getLogger("test"),
    )
    planner.llm_tool = None

    # Act
    result = await planner.execute(context)

    # Assert
    assert result is context
