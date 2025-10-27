import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from plugins.tool_bash import BashTool


@pytest.mark.asyncio
async def test_bash_tool_success():
    """Tests a successful command execution."""
    tool = BashTool()
    tool.setup({})
    return_code, stdout, stderr = await tool.execute_command("echo 'hello'")
    assert return_code == 0
    assert stdout == "hello"
    assert stderr == ""


@pytest.mark.asyncio
async def test_bash_tool_error():
    """Tests a command that produces an error."""
    tool = BashTool()
    tool.setup({})
    # 'ls' on a non-existent file should produce an error
    return_code, stdout, stderr = await tool.execute_command("ls non_existent_file")
    assert return_code != 0
    assert stdout == ""
    assert "No such file or directory" in stderr


@pytest.mark.asyncio
async def test_bash_tool_timeout():
    """Tests the timeout functionality."""
    tool = BashTool()
    tool.setup({"timeout": 1})  # Set a short timeout
    return_code, stdout, stderr = await tool.execute_command("sleep 2")
    assert return_code == -1
    assert stdout == ""
    assert "TimeoutError" in stderr
