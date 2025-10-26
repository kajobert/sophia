"""
Tests for Cognitive Task Manager Plugin

Tests the subconscious task tracking and pattern recognition.
"""

import json
import logging
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from plugins.cognitive_task_manager import TaskManager
from core.context import SharedContext


@pytest.fixture
def temp_tasks_dir(tmp_path):
    """Create temporary tasks directory."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    return tasks_dir


@pytest.fixture
def mock_memory_chroma():
    """Create mock ChromaDB memory plugin."""
    mock = AsyncMock()
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def mock_file_system():
    """Create mock FileSystem plugin."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def task_manager(temp_tasks_dir, mock_memory_chroma, mock_file_system):
    """Create TaskManager instance with mocked dependencies."""
    manager = TaskManager()
    config = {
        "enabled": True,
        "tasks_dir": str(temp_tasks_dir),
        "memory_chroma": mock_memory_chroma,
        "tool_file_system": mock_file_system
    }
    manager.setup(config)
    return manager


@pytest.fixture
def sample_goal():
    """Sample goal from NotesAnalyzer."""
    return {
        "raw_idea": "Implement new feature X",
        "formulated_goal": "Add feature X to improve system capability Y",
        "feasibility": "high",
        "dna_alignment": {
            "ahimsa": True,
            "satya": True,
            "kaizen": True
        }
    }


def create_context(user_input: str, payload: dict) -> SharedContext:
    """Helper to create SharedContext with required fields."""
    return SharedContext(
        session_id="test-session",
        current_state="TESTING",
        logger=logging.getLogger("test"),
        user_input=user_input,
        payload=payload
    )


# ============================================================================
# CREATE TASK TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_task_success(task_manager, sample_goal, temp_tasks_dir):
    """Test successful task creation."""
    context = create_context(
        user_input="create task",
        payload={
            "action": "create_task",
            "goal": sample_goal,
            "context": {"project": "sophia"},
            "priority": "high"
        }
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    assert "task_id" in result
    assert result["status"] == "pending"
    assert "created_at" in result
    assert "title" in result
    
    # Verify UUID format
    UUID(result["task_id"])
    
    # Verify file was created
    task_file = temp_tasks_dir / f"{result['task_id']}.json"
    assert task_file.exists()
    
    # Verify file content
    task_data = json.loads(task_file.read_text())
    assert task_data["task_id"] == result["task_id"]
    assert task_data["status"] == "pending"
    assert task_data["priority"] == "high"
    assert task_data["goal"] == sample_goal
    assert len(task_data["history"]) == 1


@pytest.mark.asyncio
async def test_create_task_default_priority(task_manager, sample_goal):
    """Test task creation with default priority."""
    context = create_context(
        user_input="create task",
        payload={
            "action": "create_task",
            "goal": sample_goal
        }
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    assert "task_id" in result
    
    # Load task and verify default priority
    task_file = task_manager.tasks_dir / f"{result['task_id']}.json"
    task_data = json.loads(task_file.read_text())
    assert task_data["priority"] == "medium"


@pytest.mark.asyncio
async def test_create_task_missing_goal(task_manager):
    """Test task creation without goal."""
    context = create_context(
        user_input="create task",
        payload={"action": "create_task"}
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    assert "error" in result
    assert "goal" in result["error"].lower()


@pytest.mark.asyncio
async def test_create_task_invalid_priority(task_manager, sample_goal):
    """Test task creation with invalid priority."""
    context = create_context(
        user_input="create task",
        payload={
            "action": "create_task",
            "goal": sample_goal,
            "priority": "critical"  # Invalid
        }
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    assert "error" in result
    assert "priority" in result["error"].lower()


# ============================================================================
# UPDATE TASK TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_task_success(task_manager, sample_goal):
    """Test successful task update."""
    # Create task first
    ctx = create_context(
        user_input="create task",
        payload={"action": "create_task", "goal": sample_goal}
    )
    result_ctx = await task_manager.execute(ctx)

    create_result = result_ctx.payload.get("result")
    task_id = create_result["task_id"]
    
    # Update task
    update_context = create_context(
        user_input="update task",
        payload={
            "action": "update_task",
            "task_id": task_id,
            "status": "analyzing",
            "notes": "Starting analysis phase"
        }
    )
    
    result_ctx = await task_manager.execute(update_context)
    result = result_ctx.payload.get("result")
    
    assert result["task_id"] == task_id
    assert result["status"] == "analyzing"
    assert "updated_at" in result
    
    # Verify file was updated
    task_file = task_manager.tasks_dir / f"{task_id}.json"
    task_data = json.loads(task_file.read_text())
    assert task_data["status"] == "analyzing"
    assert len(task_data["history"]) == 2
    assert task_data["history"][1]["notes"] == "Starting analysis phase"


@pytest.mark.asyncio
async def test_update_task_not_found(task_manager):
    """Test updating non-existent task."""
    context = create_context(
        user_input="update task",
        payload={
            "action": "update_task",
            "task_id": "nonexistent-uuid",
            "status": "analyzing"
        }
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_update_task_invalid_status(task_manager, sample_goal):
    """Test updating task with invalid status."""
    # Create task first
    ctx = create_context(
        user_input="create task",
        payload={"action": "create_task", "goal": sample_goal}
    )
    result_ctx = await task_manager.execute(ctx)

    create_result = result_ctx.payload.get("result")
    task_id = create_result["task_id"]
    
    # Update with invalid status
    update_context = create_context(
        user_input="update task",
        payload={
            "action": "update_task",
            "task_id": task_id,
            "status": "invalid_status"
        }
    )
    
    result_ctx = await task_manager.execute(update_context)
    result = result_ctx.payload.get("result")
    
    assert "error" in result
    assert "status" in result["error"].lower()


@pytest.mark.asyncio
async def test_update_task_status_progression(task_manager, sample_goal):
    """Test complete task status progression."""
    # Create task
    ctx = create_context(
        user_input="create task",
        payload={"action": "create_task", "goal": sample_goal}
    )
    result_ctx = await task_manager.execute(ctx)

    create_result = result_ctx.payload.get("result")
    task_id = create_result["task_id"]
    
    # Progress through statuses
    statuses = ["analyzing", "delegated", "reviewing", "integrating", "completed"]
    
    for status in statuses:
        update_context = create_context(
            user_input="update task",
            payload={
                "action": "update_task",
                "task_id": task_id,
                "status": status
            }
        )
        result_ctx = await task_manager.execute(update_context)
        result = result_ctx.payload.get("result")
        assert result["status"] == status
    
    # Verify history
    task_file = task_manager.tasks_dir / f"{task_id}.json"
    task_data = json.loads(task_file.read_text())
    assert len(task_data["history"]) == 6  # pending + 5 updates


# ============================================================================
# GET TASK TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_task_success(task_manager, sample_goal):
    """Test retrieving task details."""
    # Create task
    ctx = create_context(
        user_input="create task",
        payload={"action": "create_task", "goal": sample_goal, "priority": "high"}
    )
    result_ctx = await task_manager.execute(ctx)

    create_result = result_ctx.payload.get("result")
    task_id = create_result["task_id"]
    
    # Get task
    get_context = create_context(
        user_input="get task",
        payload={"action": "get_task", "task_id": task_id}
    )
    
    result_ctx = await task_manager.execute(get_context)
    result = result_ctx.payload.get("result")
    
    assert result["task_id"] == task_id
    assert result["status"] == "pending"
    assert result["priority"] == "high"
    assert result["goal"] == sample_goal


@pytest.mark.asyncio
async def test_get_task_not_found(task_manager):
    """Test getting non-existent task."""
    context = create_context(
        user_input="get task",
        payload={"action": "get_task", "task_id": "nonexistent-uuid"}
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    assert "error" in result
    assert "not found" in result["error"].lower()


# ============================================================================
# LIST TASKS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_tasks_empty(task_manager):
    """Test listing tasks when none exist."""
    context = create_context(
        user_input="list tasks",
        payload={"action": "list_tasks"}
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    assert result["tasks"] == []
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_list_tasks_multiple(task_manager, sample_goal):
    """Test listing multiple tasks."""
    # Create 3 tasks with different priorities
    priorities = ["high", "medium", "low"]
    task_ids = []
    
    for priority in priorities:
        context = create_context(
            user_input="create task",
            payload={
                "action": "create_task",
                "goal": {**sample_goal, "raw_idea": f"Task {priority}"},
                "priority": priority
            }
        )
        result_ctx = await task_manager.execute(context)

        result = result_ctx.payload.get("result")
        task_ids.append(result["task_id"])
    
    # List all tasks
    list_context = create_context(
        user_input="list tasks",
        payload={"action": "list_tasks"}
    )
    
    result_ctx = await task_manager.execute(list_context)
    result = result_ctx.payload.get("result")
    
    assert len(result["tasks"]) == 3
    assert result["total"] == 3
    
    # Verify sorting (high priority first)
    assert result["tasks"][0]["priority"] == "high"


@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(task_manager, sample_goal):
    """Test filtering tasks by status."""
    # Create 2 tasks
    task_ids = []
    for i in range(2):
        context = create_context(
            user_input="create task",
            payload={"action": "create_task", "goal": sample_goal}
        )
        result_ctx = await task_manager.execute(context)

        result = result_ctx.payload.get("result")
        task_ids.append(result["task_id"])
    
    # Update one to analyzing
    update_context = create_context(
        user_input="update task",
        payload={
            "action": "update_task",
            "task_id": task_ids[0],
            "status": "analyzing"
        }
    )
    await task_manager.execute(update_context)
    
    # List only analyzing tasks
    list_context = create_context(
        user_input="list tasks",
        payload={"action": "list_tasks", "status": "analyzing"}
    )
    
    result_ctx = await task_manager.execute(list_context)
    result = result_ctx.payload.get("result")
    
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["task_id"] == task_ids[0]


# ============================================================================
# SIMILAR TASKS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_similar_tasks_with_chroma(task_manager, mock_memory_chroma, sample_goal):
    """Test finding similar tasks using ChromaDB."""
    # Create a task first
    ctx = create_context(
        user_input="create task",
        payload={"action": "create_task", "goal": sample_goal}
    )
    result_ctx = await task_manager.execute(ctx)

    create_result = result_ctx.payload.get("result")
    task_id = create_result["task_id"]
    
    # Mock ChromaDB response
    mock_memory_chroma.execute.return_value = {
        "memories": [
            {
                "text": "Similar task description",
                "metadata": {"task_id": task_id},
                "score": 0.85
            }
        ]
    }
    
    # Search for similar tasks
    similar_context = create_context(
        user_input="find similar",
        payload={
            "action": "get_similar_tasks",
            "task": {"title": "Similar feature", "description": "Similar description"},
            "top_k": 5
        }
    )
    
    result_ctx = await task_manager.execute(similar_context)
    result = result_ctx.payload.get("result")
    
    assert "similar_tasks" in result
    assert result["count"] == 1
    assert result["similar_tasks"][0]["task_id"] == task_id


@pytest.mark.asyncio
async def test_get_similar_tasks_no_chroma(task_manager):
    """Test similar tasks when ChromaDB unavailable."""
    # Disable ChromaDB
    task_manager.memory_chroma = None
    
    context = create_context(
        user_input="find similar",
        payload={
            "action": "get_similar_tasks",
            "task": {"title": "Test", "description": "Test"}
        }
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    assert result["similar_tasks"] == []
    assert result["count"] == 0


# ============================================================================
# CONSOLIDATE INSIGHTS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_consolidate_insights_success(task_manager, mock_memory_chroma, sample_goal):
    """Test consolidating insights from completed task."""
    # Create task
    ctx = create_context(
        user_input="create task",
        payload={"action": "create_task", "goal": sample_goal}
    )
    result_ctx = await task_manager.execute(ctx)

    create_result = result_ctx.payload.get("result")
    task_id = create_result["task_id"]
    
    # Update with meaningful history
    update_context = create_context(
        user_input="update task",
        payload={
            "action": "update_task",
            "task_id": task_id,
            "status": "completed",
            "notes": "Learned important lesson: Always validate input data before processing"
        }
    )
    await task_manager.execute(update_context)
    
    # Mock ChromaDB
    mock_memory_chroma.execute.return_value = {"success": True}
    
    # Consolidate insights
    consolidate_context = create_context(
        user_input="consolidate_insights",
        payload={"action": "consolidate_insights", "task_id": task_id}
    )
    
    result_ctx = await task_manager.execute(consolidate_context)
    result = result_ctx.payload.get("result")
    
    assert result["status"] == "success"
    assert result["insights_stored"] >= 2  # Description + learning note
    assert mock_memory_chroma.execute.called


@pytest.mark.asyncio
async def test_consolidate_insights_no_chroma(task_manager, sample_goal):
    """Test consolidating insights without ChromaDB."""
    # Disable ChromaDB
    task_manager.memory_chroma = None
    
    # Create task
    ctx = create_context(
        user_input="create task",
        payload={"action": "create_task", "goal": sample_goal}
    )
    result_ctx = await task_manager.execute(ctx)

    create_result = result_ctx.payload.get("result")
    task_id = create_result["task_id"]
    
    # Consolidate insights
    context = create_context(
        user_input="consolidate_insights",
        payload={"action": "consolidate_insights", "task_id": task_id}
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    assert result["status"] == "skipped"
    assert "ChromaDB" in result.get("reason", "")


@pytest.mark.asyncio
async def test_consolidate_insights_task_not_found(task_manager):
    """Test consolidating insights for non-existent task."""
    context = create_context(
        user_input="consolidate_insights",
        payload={"action": "consolidate_insights", "task_id": "nonexistent-uuid"}
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    assert "error" in result
    assert "not found" in result["error"].lower()


# ============================================================================
# PERSISTENCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_task_persistence_across_restarts(temp_tasks_dir, mock_memory_chroma, mock_file_system, sample_goal):
    """Test that tasks persist across TaskManager restarts."""
    # Create first instance and create task
    manager1 = TaskManager()
    config = {
        "enabled": True,
        "tasks_dir": str(temp_tasks_dir),
        "memory_chroma": mock_memory_chroma,
        "tool_file_system": mock_file_system
    }
    manager1.setup(config)
    
    ctx = create_context(
        user_input="create task",
        payload={"action": "create_task", "goal": sample_goal}
    )
    result_ctx = await manager1.execute(ctx)
    create_result = result_ctx.payload.get("result")
    task_id = create_result["task_id"]
    
    # Create second instance (simulating restart)
    manager2 = TaskManager()
    manager2.setup(config)
    
    # Retrieve task with new instance
    get_ctx = create_context(
        user_input="get task",
        payload={"action": "get_task", "task_id": task_id}
    )
    
    result_ctx = await manager2.execute(get_ctx)
    result = result_ctx.payload.get("result")
    
    assert result["task_id"] == task_id
    assert result["goal"] == sample_goal


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.asyncio
async def test_unknown_action(task_manager):
    """Test handling of unknown action."""
    context = create_context(
        user_input="unknown",
        payload={"action": "unknown_action"}
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    assert "error" in result
    assert "unknown" in result["error"].lower()


@pytest.mark.asyncio
async def test_long_task_title_truncation(task_manager):
    """Test that very long task titles are truncated."""
    long_goal = {
        "raw_idea": "A" * 200,  # Very long title
        "formulated_goal": "B" * 200
    }
    
    context = create_context(
        user_input="create task",
        payload={"action": "create_task", "goal": long_goal}
    )
    
    result_ctx = await task_manager.execute(context)

    
    result = result_ctx.payload.get("result")
    
    # Load task
    task_file = task_manager.tasks_dir / f"{result['task_id']}.json"
    task_data = json.loads(task_file.read_text())
    
    # Title should be truncated to 100 chars
    assert len(task_data["title"]) == 100
