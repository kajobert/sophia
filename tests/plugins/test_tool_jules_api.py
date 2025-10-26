"""
Tests for Jules API Tool Plugin

Comprehensive testing of task delegation to external coding agents.
Tests cover all backends (mock, Jules, Copilot, Claude) and error scenarios.
"""

import pytest
import asyncio
from plugins.tool_jules_api import JulesAPITool, Backend, TaskStatus
from plugins.base_plugin import PluginType


@pytest.fixture
def jules_tool():
    """Create JulesAPITool instance with mock backend."""
    tool = JulesAPITool()
    tool.setup({
        "backend": "mock",
        "timeout": 300,
        "max_retries": 3,
        "poll_interval": 30
    })
    return tool


@pytest.fixture
def sample_specification():
    """Sample coding task specification."""
    return """
    Create a new COGNITIVE plugin called 'cognitive_pattern_matcher' that:
    1. Analyzes code patterns using AST parsing
    2. Identifies similar patterns across the codebase
    3. Suggests refactoring opportunities
    
    Must follow BasePlugin contract and include comprehensive tests.
    """


@pytest.fixture
def sample_context_files():
    """Sample context files for task."""
    return {
        "guidelines": "# Development Guidelines\n- 100% type hints\n- Google-style docstrings\n- Comprehensive tests",
        "architecture": "# Architecture\nCore-Plugin principle\nNo modifications to core/",
        "similar_code": "# Example Plugin\nclass ExamplePlugin(BasePlugin):\n    pass"
    }


@pytest.fixture
def sample_requirements():
    """Sample requirements for task."""
    return {
        "plugin_name": "cognitive_pattern_matcher",
        "plugin_type": "COGNITIVE",
        "must_have_tests": True,
        "language": "en"
    }


# =============================================================================
# Plugin Metadata Tests
# =============================================================================

def test_plugin_metadata():
    """Test plugin metadata properties."""
    tool = JulesAPITool()
    
    assert tool.name == "tool_jules_api"
    assert tool.plugin_type == PluginType.TOOL
    assert tool.version == "1.0.0"


def test_plugin_initialization():
    """Test plugin initialization."""
    tool = JulesAPITool()
    
    assert tool.backend == Backend.MOCK
    assert tool.api_key is None
    assert tool.endpoint is None
    assert tool.timeout == 300
    assert tool.max_retries == 3
    assert tool.poll_interval == 30
    assert tool._mock_tasks == {}
    assert tool._mock_task_counter == 0


# =============================================================================
# Setup Tests
# =============================================================================

def test_setup_mock_backend():
    """Test setup with mock backend."""
    tool = JulesAPITool()
    tool.setup({
        "backend": "mock",
        "timeout": 600,
        "max_retries": 5,
        "poll_interval": 10
    })
    
    assert tool.backend == Backend.MOCK
    assert tool.timeout == 600
    assert tool.max_retries == 5
    assert tool.poll_interval == 10


def test_setup_jules_backend():
    """Test setup with Jules backend."""
    tool = JulesAPITool()
    tool.setup({
        "backend": "jules",
        "api_key": "test_jules_key",
        "endpoint": "https://jules.googleapis.com/v1",
        "timeout": 300
    })
    
    assert tool.backend == Backend.JULES
    assert tool.api_key == "test_jules_key"
    assert tool.endpoint == "https://jules.googleapis.com/v1"


def test_setup_copilot_backend():
    """Test setup with Copilot backend."""
    tool = JulesAPITool()
    tool.setup({
        "backend": "copilot",
        "api_key": "test_copilot_key",
        "endpoint": "https://api.github.com/copilot"
    })
    
    assert tool.backend == Backend.COPILOT
    assert tool.api_key == "test_copilot_key"


def test_setup_claude_backend():
    """Test setup with Claude backend."""
    tool = JulesAPITool()
    tool.setup({
        "backend": "claude",
        "api_key": "test_claude_key",
        "endpoint": "https://api.anthropic.com/v1"
    })
    
    assert tool.backend == Backend.CLAUDE
    assert tool.api_key == "test_claude_key"


def test_setup_invalid_backend():
    """Test setup with invalid backend falls back to mock."""
    tool = JulesAPITool()
    tool.setup({
        "backend": "invalid_backend"
    })
    
    assert tool.backend == Backend.MOCK


def test_setup_environment_variable():
    """Test API key from environment variable."""
    import os
    os.environ["TEST_JULES_KEY"] = "env_api_key_123"
    
    tool = JulesAPITool()
    tool.setup({
        "backend": "jules",
        "api_key": "${TEST_JULES_KEY}"
    })
    
    assert tool.api_key == "env_api_key_123"
    del os.environ["TEST_JULES_KEY"]


def test_setup_missing_environment_variable():
    """Test missing environment variable is handled gracefully."""
    tool = JulesAPITool()
    tool.setup({
        "backend": "jules",
        "api_key": "${NONEXISTENT_KEY}"
    })
    
    assert tool.api_key is None


# =============================================================================
# Execute Tests - Submit Task
# =============================================================================

@pytest.mark.asyncio
async def test_execute_submit_task_success(jules_tool, sample_specification,
                                          sample_context_files, sample_requirements):
    """Test successful task submission."""
    result = await jules_tool.execute({
        "action": "submit_task",
        "specification": sample_specification,
        "context_files": sample_context_files,
        "requirements": sample_requirements
    })
    
    assert result["success"] is True
    assert "task_id" in result
    assert result["task_id"].startswith("mock_task_")


@pytest.mark.asyncio
async def test_execute_submit_task_missing_specification(jules_tool):
    """Test task submission without specification fails."""
    result = await jules_tool.execute({
        "action": "submit_task",
        "context_files": {},
        "requirements": {}
    })
    
    assert result["success"] is False
    assert "Missing specification" in result["error"]


@pytest.mark.asyncio
async def test_execute_submit_task_empty_specification(jules_tool):
    """Test task submission with empty specification fails."""
    result = await jules_tool.execute({
        "action": "submit_task",
        "specification": "",
        "context_files": {},
        "requirements": {}
    })
    
    assert result["success"] is False
    assert "Missing specification" in result["error"]


# =============================================================================
# Execute Tests - Get Status
# =============================================================================

@pytest.mark.asyncio
async def test_execute_get_status_success(jules_tool, sample_specification,
                                         sample_context_files, sample_requirements):
    """Test status polling for submitted task."""
    # Submit task first
    submit_result = await jules_tool.execute({
        "action": "submit_task",
        "specification": sample_specification,
        "context_files": sample_context_files,
        "requirements": sample_requirements
    })
    
    task_id = submit_result["task_id"]
    
    # Get status
    status_result = await jules_tool.execute({
        "action": "get_status",
        "task_id": task_id
    })
    
    assert status_result["success"] is True
    assert status_result["task_id"] == task_id
    assert "status" in status_result
    assert status_result["status"] in ["pending", "running", "completed", "failed"]


@pytest.mark.asyncio
async def test_execute_get_status_missing_task_id(jules_tool):
    """Test status check without task_id fails."""
    result = await jules_tool.execute({
        "action": "get_status"
    })
    
    assert result["success"] is False
    assert "Missing task_id" in result["error"]


@pytest.mark.asyncio
async def test_execute_get_status_invalid_task_id(jules_tool):
    """Test status check for non-existent task."""
    result = await jules_tool.execute({
        "action": "get_status",
        "task_id": "nonexistent_task_id"
    })
    
    assert result["success"] is False
    assert "not found" in result["error"]


# =============================================================================
# Execute Tests - Get Result
# =============================================================================

@pytest.mark.asyncio
async def test_execute_get_result_success(jules_tool, sample_specification,
                                         sample_context_files, sample_requirements):
    """Test result retrieval for completed task."""
    # Submit task
    submit_result = await jules_tool.execute({
        "action": "submit_task",
        "specification": sample_specification,
        "context_files": sample_context_files,
        "requirements": sample_requirements
    })
    
    task_id = submit_result["task_id"]
    
    # Poll until completed
    max_polls = 10
    for _ in range(max_polls):
        status = await jules_tool.execute({
            "action": "get_status",
            "task_id": task_id
        })
        
        if status["status"] == "completed":
            break
        
        await asyncio.sleep(0.1)
    
    # Get result
    result = await jules_tool.execute({
        "action": "get_result",
        "task_id": task_id
    })
    
    assert result["success"] is True
    assert "result" in result
    assert "plugin_code" in result["result"]
    assert "test_code" in result["result"]
    assert "documentation" in result["result"]


@pytest.mark.asyncio
async def test_execute_get_result_task_not_completed(jules_tool, sample_specification,
                                                     sample_context_files, sample_requirements):
    """Test result retrieval for non-completed task fails."""
    # Submit task
    submit_result = await jules_tool.execute({
        "action": "submit_task",
        "specification": sample_specification,
        "context_files": sample_context_files,
        "requirements": sample_requirements
    })
    
    task_id = submit_result["task_id"]
    
    # Try to get result immediately (task not completed)
    result = await jules_tool.execute({
        "action": "get_result",
        "task_id": task_id
    })
    
    assert result["success"] is False
    assert "not completed" in result["error"]


@pytest.mark.asyncio
async def test_execute_get_result_missing_task_id(jules_tool):
    """Test result retrieval without task_id fails."""
    result = await jules_tool.execute({
        "action": "get_result"
    })
    
    assert result["success"] is False
    assert "Missing task_id" in result["error"]


@pytest.mark.asyncio
async def test_execute_get_result_invalid_task_id(jules_tool):
    """Test result retrieval for non-existent task."""
    result = await jules_tool.execute({
        "action": "get_result",
        "task_id": "nonexistent_task_id"
    })
    
    assert result["success"] is False
    assert "not found" in result["error"]


# =============================================================================
# Execute Tests - Cancel Task
# =============================================================================

@pytest.mark.asyncio
async def test_execute_cancel_task_success(jules_tool, sample_specification,
                                          sample_context_files, sample_requirements):
    """Test task cancellation."""
    # Submit task
    submit_result = await jules_tool.execute({
        "action": "submit_task",
        "specification": sample_specification,
        "context_files": sample_context_files,
        "requirements": sample_requirements
    })
    
    task_id = submit_result["task_id"]
    
    # Cancel task
    cancel_result = await jules_tool.execute({
        "action": "cancel_task",
        "task_id": task_id
    })
    
    assert cancel_result["success"] is True
    assert cancel_result["task_id"] == task_id


@pytest.mark.asyncio
async def test_execute_cancel_task_missing_task_id(jules_tool):
    """Test cancellation without task_id fails."""
    result = await jules_tool.execute({
        "action": "cancel_task"
    })
    
    assert result["success"] is False
    assert "Missing task_id" in result["error"]


@pytest.mark.asyncio
async def test_execute_cancel_task_invalid_task_id(jules_tool):
    """Test cancellation for non-existent task."""
    result = await jules_tool.execute({
        "action": "cancel_task",
        "task_id": "nonexistent_task_id"
    })
    
    assert result["success"] is False
    assert "not found" in result["error"]


# =============================================================================
# Execute Tests - Unknown Action
# =============================================================================

@pytest.mark.asyncio
async def test_execute_unknown_action(jules_tool):
    """Test unknown action fails gracefully."""
    result = await jules_tool.execute({
        "action": "invalid_action"
    })
    
    assert result["success"] is False
    assert "Unknown action" in result["error"]


# =============================================================================
# Mock Backend Tests
# =============================================================================

@pytest.mark.asyncio
async def test_mock_task_lifecycle(jules_tool, sample_specification,
                                   sample_context_files, sample_requirements):
    """Test complete task lifecycle with mock backend."""
    # 1. Submit task
    submit = await jules_tool.execute({
        "action": "submit_task",
        "specification": sample_specification,
        "context_files": sample_context_files,
        "requirements": sample_requirements
    })
    
    assert submit["success"] is True
    task_id = submit["task_id"]
    
    # 2. Check status - should be running
    status1 = await jules_tool.execute({
        "action": "get_status",
        "task_id": task_id
    })
    
    assert status1["success"] is True
    assert status1["status"] in ["pending", "running"]
    
    # 3. Poll until completed
    max_polls = 10
    for _ in range(max_polls):
        status = await jules_tool.execute({
            "action": "get_status",
            "task_id": task_id
        })
        
        if status["status"] == "completed":
            break
        
        await asyncio.sleep(0.1)
    
    # 4. Get result
    result = await jules_tool.execute({
        "action": "get_result",
        "task_id": task_id
    })
    
    assert result["success"] is True
    assert "plugin_code" in result["result"]
    assert "test_code" in result["result"]
    assert "documentation" in result["result"]


@pytest.mark.asyncio
async def test_mock_multiple_tasks(jules_tool, sample_specification,
                                   sample_context_files, sample_requirements):
    """Test handling multiple concurrent tasks."""
    # Submit 3 tasks
    task_ids = []
    for i in range(3):
        result = await jules_tool.execute({
            "action": "submit_task",
            "specification": f"{sample_specification} (variant {i})",
            "context_files": sample_context_files,
            "requirements": sample_requirements
        })
        task_ids.append(result["task_id"])
    
    # Verify all tasks exist
    for task_id in task_ids:
        status = await jules_tool.execute({
            "action": "get_status",
            "task_id": task_id
        })
        assert status["success"] is True


@pytest.mark.asyncio
async def test_mock_task_progress(jules_tool, sample_specification,
                                  sample_context_files, sample_requirements):
    """Test task progress tracking."""
    submit = await jules_tool.execute({
        "action": "submit_task",
        "specification": sample_specification,
        "context_files": sample_context_files,
        "requirements": sample_requirements
    })
    
    task_id = submit["task_id"]
    
    # Track progress over multiple polls
    progresses = []
    for _ in range(5):
        status = await jules_tool.execute({
            "action": "get_status",
            "task_id": task_id
        })
        
        if "progress" in status:
            progresses.append(status["progress"])
        
        if status["status"] == "completed":
            break
        
        await asyncio.sleep(0.1)
    
    # Progress should increase over time
    assert len(progresses) > 0
    # Last progress should be higher than first (or both are 1.0 if completed fast)
    if len(progresses) > 1:
        assert progresses[-1] >= progresses[0]


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.asyncio
async def test_execute_exception_handling(jules_tool):
    """Test exception handling in execute method."""
    # This should not raise an exception, even with malformed input
    result = await jules_tool.execute({
        "action": "submit_task",
        "specification": None  # This might cause an error internally
    })
    
    assert "success" in result
    assert "error" in result or result["success"] is True


# =============================================================================
# Non-Implemented Backend Tests
# =============================================================================

@pytest.mark.asyncio
async def test_jules_backend_not_implemented():
    """Test Jules backend returns not implemented error."""
    tool = JulesAPITool()
    tool.setup({"backend": "jules"})
    
    result = await tool.execute({
        "action": "submit_task",
        "specification": "test spec",
        "context_files": {},
        "requirements": {}
    })
    
    assert result["success"] is False
    assert "not yet implemented" in result["error"]


@pytest.mark.asyncio
async def test_copilot_backend_not_implemented():
    """Test Copilot backend returns not implemented error."""
    tool = JulesAPITool()
    tool.setup({"backend": "copilot"})
    
    result = await tool.execute({
        "action": "submit_task",
        "specification": "test spec",
        "context_files": {},
        "requirements": {}
    })
    
    assert result["success"] is False
    assert "not yet implemented" in result["error"]


@pytest.mark.asyncio
async def test_claude_backend_not_implemented():
    """Test Claude backend returns not implemented error."""
    tool = JulesAPITool()
    tool.setup({"backend": "claude"})
    
    result = await tool.execute({
        "action": "submit_task",
        "specification": "test spec",
        "context_files": {},
        "requirements": {}
    })
    
    assert result["success"] is False
    assert "not yet implemented" in result["error"]
