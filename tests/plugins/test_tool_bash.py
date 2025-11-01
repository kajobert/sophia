import pytest
import logging
from unittest.mock import MagicMock
from plugins.tool_bash import BashTool
from core.context import SharedContext

# Create a mock context for testing
@pytest.fixture
def mock_context():
    context = SharedContext(
        session_id="test_session",
        current_state="TESTING",
        logger=MagicMock(spec=logging.Logger)
    )
    return context


@pytest.mark.asyncio
async def test_bash_tool_success(mock_context):
    """Tests a successful command execution."""
    tool = BashTool()
    tool.setup({})
    output = await tool.execute_command(mock_context, "echo 'hello'")
    assert "STDOUT:\nhello" in output
    assert "STDERR:" in output
    mock_context.logger.info.assert_called()


@pytest.mark.asyncio
async def test_bash_tool_error(mock_context):
    """Tests a command that produces an error."""
    tool = BashTool()
    tool.setup({})
    # 'ls' on a non-existent file should produce an error
    output = await tool.execute_command(mock_context, "ls non_existent_file")
    assert "No such file or directory" in output
    mock_context.logger.warning.assert_called()


@pytest.mark.asyncio
async def test_bash_tool_timeout(mock_context):
    """Tests the timeout functionality."""
    tool = BashTool()
    tool.setup({"timeout": 1})  # Set a short timeout
    output = await tool.execute_command(mock_context, "sleep 2")
    assert "TimeoutError" in output
    mock_context.logger.error.assert_called()
