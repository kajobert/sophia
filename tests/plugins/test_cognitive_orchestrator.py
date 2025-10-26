"""
Tests for Strategic Orchestrator Plugin

Tests the highest cognitive layer (VĚDOMÍ) coordination of autonomous workflows.
"""

import pytest
import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from core.context import SharedContext
from plugins.cognitive_orchestrator import StrategicOrchestrator
from plugins.base_plugin import PluginType


# Test Fixtures

@pytest.fixture
def mock_task_manager():
    """Mock TaskManager plugin."""
    manager = MagicMock()
    manager.name = "cognitive_task_manager"
    manager.execute = AsyncMock()
    return manager


@pytest.fixture
def mock_notes_analyzer():
    """Mock NotesAnalyzer plugin."""
    analyzer = MagicMock()
    analyzer.name = "cognitive_notes_analyzer"
    analyzer.execute = AsyncMock()
    return analyzer


@pytest.fixture
def mock_ethical_guardian():
    """Mock EthicalGuardian plugin."""
    guardian = MagicMock()
    guardian.name = "cognitive_ethical_guardian"
    guardian.execute = AsyncMock()
    return guardian


@pytest.fixture
def mock_doc_reader():
    """Mock DocReader plugin."""
    reader = MagicMock()
    reader.name = "cognitive_doc_reader"
    reader.execute = AsyncMock()
    return reader


@pytest.fixture
def orchestrator(mock_task_manager, mock_notes_analyzer, mock_ethical_guardian):
    """Create configured orchestrator with mocked dependencies."""
    orch = StrategicOrchestrator()
    orch.setup({
        "cognitive_task_manager": mock_task_manager,
        "cognitive_notes_analyzer": mock_notes_analyzer,
        "cognitive_ethical_guardian": mock_ethical_guardian,
        "require_approval": False,  # Disable for automated tests
        "max_concurrent_missions": 3
    })
    return orch


@pytest.fixture
def sample_goal():
    """Sample goal for testing."""
    return {
        "raw_idea": "Create a weather plugin",
        "formulated_goal": "Create a tool plugin that fetches weather data from wttr.in API",
        "context": {
            "relevant_docs": [],
            "similar_missions": [],
            "existing_plugins": []
        },
        "feasibility": "high",
        "alignment_with_dna": {
            "ahimsa": True,
            "satya": True,
            "kaizen": True
        }
    }


@pytest.fixture
def sample_task():
    """Sample task for testing."""
    return {
        "task_id": "test-task-123",
        "title": "Create weather plugin",
        "description": "Implement tool plugin for weather data",
        "goal": {
            "formulated_goal": "Create a tool plugin that fetches weather data"
        },
        "status": "pending",
        "priority": "high",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "history": []
    }


def create_context(user_input: str = "", payload: dict = None) -> SharedContext:
    """Helper to create SharedContext."""
    return SharedContext(
        session_id="test-session",
        user_input=user_input,
        current_state="testing",
        logger=logging.getLogger("test"),
        payload=payload or {}
    )


# Plugin Metadata Tests

def test_plugin_metadata():
    """Test plugin has correct metadata."""
    orch = StrategicOrchestrator()
    assert orch.name == "cognitive_orchestrator"
    assert orch.plugin_type == PluginType.COGNITIVE
    assert orch.version == "1.0.0"


def test_plugin_initialization():
    """Test plugin initializes with correct defaults."""
    orch = StrategicOrchestrator()
    assert orch.task_manager is None
    assert orch.notes_analyzer is None
    assert orch.ethical_guardian is None
    assert orch.require_approval is True
    assert orch.max_concurrent_missions == 3


# Setup and Configuration Tests

def test_setup_with_all_dependencies(
    mock_task_manager,
    mock_notes_analyzer,
    mock_ethical_guardian,
    mock_doc_reader
):
    """Test setup with all dependencies."""
    orch = StrategicOrchestrator()
    orch.setup({
        "cognitive_task_manager": mock_task_manager,
        "cognitive_notes_analyzer": mock_notes_analyzer,
        "cognitive_ethical_guardian": mock_ethical_guardian,
        "cognitive_doc_reader": mock_doc_reader,
        "require_approval": False,
        "max_concurrent_missions": 5
    })
    
    assert orch.task_manager == mock_task_manager
    assert orch.notes_analyzer == mock_notes_analyzer
    assert orch.ethical_guardian == mock_ethical_guardian
    assert orch.doc_reader == mock_doc_reader
    assert orch.require_approval is False
    assert orch.max_concurrent_missions == 5


def test_setup_with_minimal_dependencies(mock_task_manager):
    """Test setup works with only required dependencies."""
    orch = StrategicOrchestrator()
    orch.setup({
        "cognitive_task_manager": mock_task_manager
    })
    
    assert orch.task_manager == mock_task_manager
    assert orch.notes_analyzer is None  # Optional
    assert orch.require_approval is True  # Default


# Execute Action Routing Tests

@pytest.mark.asyncio
async def test_execute_unknown_action(orchestrator):
    """Test handling of unknown action."""
    ctx = create_context(payload={"action": "invalid_action"})
    
    result_ctx = await orchestrator.execute(ctx)
    
    assert "result" in result_ctx.payload
    assert result_ctx.payload["result"]["success"] is False
    assert "Unknown action" in result_ctx.payload["result"]["error"]


@pytest.mark.asyncio
async def test_execute_analyze_goal_action(
    orchestrator,
    mock_notes_analyzer,
    mock_ethical_guardian,
    mock_task_manager,
    sample_goal
):
    """Test execute routes analyze_goal action correctly."""
    # Setup mocks
    mock_notes_analyzer.execute.return_value = create_context(
        payload={"result": [sample_goal]}
    )
    mock_ethical_guardian.execute.return_value = create_context(
        payload={"result": {"approved": True, "concerns": []}}
    )
    mock_task_manager.execute.return_value = create_context(
        payload={"result": "task-123"}
    )
    
    ctx = create_context(payload={
        "action": "analyze_goal",
        "goal": "Create a weather plugin"
    })
    
    result_ctx = await orchestrator.execute(ctx)
    
    assert "result" in result_ctx.payload
    assert result_ctx.payload["result"]["success"] is True
    assert result_ctx.payload["result"]["task_id"] == "task-123"


# Analyze Goal Tests

@pytest.mark.asyncio
async def test_analyze_goal_success(
    orchestrator,
    mock_notes_analyzer,
    mock_ethical_guardian,
    mock_task_manager,
    sample_goal
):
    """Test successful goal analysis workflow."""
    # Setup mocks
    mock_notes_analyzer.execute.return_value = create_context(
        payload={"result": [sample_goal]}
    )
    mock_ethical_guardian.execute.return_value = create_context(
        payload={"result": {"approved": True, "concerns": []}}
    )
    mock_task_manager.execute.return_value = create_context(
        payload={"result": "task-abc-123"}
    )
    
    ctx = create_context()
    result = await orchestrator._analyze_goal("Create a weather plugin", ctx)
    
    assert result["success"] is True
    assert result["task_id"] == "task-abc-123"
    assert "analysis" in result
    assert "ethical_validation" in result
    assert result["ethical_validation"]["approved"] is True


@pytest.mark.asyncio
async def test_analyze_goal_missing_dependencies():
    """Test analyze_goal fails gracefully without required plugins."""
    orch = StrategicOrchestrator()
    # No dependencies set
    
    ctx = create_context()
    result = await orch._analyze_goal("Some goal", ctx)
    
    assert result["success"] is False
    assert "Missing required plugins" in result["error"]


@pytest.mark.asyncio
async def test_analyze_goal_ethical_rejection(
    orchestrator,
    mock_notes_analyzer,
    mock_ethical_guardian,
    sample_goal
):
    """Test goal rejected due to ethical concerns."""
    # Setup mocks
    mock_notes_analyzer.execute.return_value = create_context(
        payload={"result": [sample_goal]}
    )
    mock_ethical_guardian.execute.return_value = create_context(
        payload={
            "result": {
                "approved": False,
                "concerns": ["potential harm", "unclear intent"],
                "recommendation": "Reject"
            }
        }
    )
    
    ctx = create_context()
    result = await orchestrator._analyze_goal("Delete all user data", ctx)
    
    assert result["success"] is False
    assert "ethical concerns" in result["message"]
    assert len(result["ethical_validation"]["concerns"]) > 0


@pytest.mark.asyncio
async def test_analyze_goal_empty_analysis(
    orchestrator,
    mock_notes_analyzer,
    mock_ethical_guardian
):
    """Test handling of empty analysis result."""
    # Mock returns empty result
    mock_notes_analyzer.execute.return_value = create_context(
        payload={"result": []}
    )
    
    ctx = create_context()
    result = await orchestrator._analyze_goal("Vague goal", ctx)
    
    assert result["success"] is False
    assert "analysis failed" in result["error"].lower()


@pytest.mark.asyncio
async def test_analyze_goal_task_creation_failed(
    orchestrator,
    mock_notes_analyzer,
    mock_ethical_guardian,
    mock_task_manager,
    sample_goal
):
    """Test handling of task creation failure."""
    # Setup mocks
    mock_notes_analyzer.execute.return_value = create_context(
        payload={"result": [sample_goal]}
    )
    mock_ethical_guardian.execute.return_value = create_context(
        payload={"result": {"approved": True, "concerns": []}}
    )
    mock_task_manager.execute.return_value = create_context(
        payload={"result": None}  # Task creation failed
    )
    
    ctx = create_context()
    result = await orchestrator._analyze_goal("Create plugin", ctx)
    
    assert result["success"] is False
    assert "Task creation failed" in result["error"]


# Execute Mission Tests

@pytest.mark.asyncio
async def test_execute_mission_success(
    orchestrator,
    mock_task_manager,
    sample_task
):
    """Test successful mission execution."""
    # Setup mocks
    mock_task_manager.execute.side_effect = [
        create_context(payload={"result": sample_task}),  # get_task
        create_context(payload={"result": []}),  # get_similar_tasks
        create_context(payload={"result": None})  # update_task
    ]
    
    ctx = create_context()
    result = await orchestrator._execute_mission("test-task-123", ctx)
    
    assert result["success"] is True
    assert result["task_id"] == "test-task-123"
    assert result["status"] == "analyzing"
    assert "plan" in result
    assert "next_steps" in result["plan"]


@pytest.mark.asyncio
async def test_execute_mission_task_not_found(orchestrator, mock_task_manager):
    """Test mission execution with non-existent task."""
    # Mock returns no task
    mock_task_manager.execute.return_value = create_context(
        payload={"result": None}
    )
    
    ctx = create_context()
    result = await orchestrator._execute_mission("invalid-id", ctx)
    
    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_execute_mission_with_similar_tasks(
    orchestrator,
    mock_task_manager,
    sample_task
):
    """Test mission execution finds and uses similar tasks."""
    similar_tasks = [
        {"task_id": "old-1", "title": "Similar task 1"},
        {"task_id": "old-2", "title": "Similar task 2"}
    ]
    
    # Setup mocks
    mock_task_manager.execute.side_effect = [
        create_context(payload={"result": sample_task}),  # get_task
        create_context(payload={"result": similar_tasks}),  # get_similar_tasks
        create_context(payload={"result": None})  # update_task
    ]
    
    ctx = create_context()
    result = await orchestrator._execute_mission("test-task-123", ctx)
    
    assert result["success"] is True
    assert result["plan"]["context"]["similar_tasks_found"] == 2
    assert len(result["plan"]["context"]["similar_tasks"]) == 2


@pytest.mark.asyncio
async def test_execute_mission_missing_task_manager():
    """Test mission execution fails without TaskManager."""
    orch = StrategicOrchestrator()
    # No task_manager set
    
    ctx = create_context()
    result = await orch._execute_mission("task-id", ctx)
    
    assert result["success"] is False
    assert "not available" in result["error"]


# Get Mission Status Tests

@pytest.mark.asyncio
async def test_get_mission_status_success(orchestrator, mock_task_manager, sample_task):
    """Test successful status retrieval."""
    sample_task["status"] = "analyzing"
    sample_task["history"] = [
        {"event": "created", "timestamp": datetime.now().isoformat()},
        {"event": "analyzing", "timestamp": datetime.now().isoformat()}
    ]
    
    mock_task_manager.execute.return_value = create_context(
        payload={"result": sample_task}
    )
    
    result = await orchestrator._get_mission_status("test-task-123")
    
    assert result["success"] is True
    assert result["task_id"] == "test-task-123"
    assert result["status"] == "analyzing"
    assert len(result["history"]) == 2


@pytest.mark.asyncio
async def test_get_mission_status_task_not_found(orchestrator, mock_task_manager):
    """Test status check for non-existent task."""
    mock_task_manager.execute.return_value = create_context(
        payload={"result": None}
    )
    
    result = await orchestrator._get_mission_status("invalid-id")
    
    assert result["success"] is False
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_get_mission_status_missing_task_manager():
    """Test status check fails without TaskManager."""
    orch = StrategicOrchestrator()
    
    result = await orch._get_mission_status("task-id")
    
    assert result["success"] is False
    assert "not available" in result["error"]


# Integration Tests

@pytest.mark.asyncio
async def test_full_workflow_analyze_and_execute(
    orchestrator,
    mock_notes_analyzer,
    mock_ethical_guardian,
    mock_task_manager,
    sample_goal,
    sample_task
):
    """Test complete workflow: analyze goal → create task → execute mission."""
    # Setup mocks for analyze_goal
    mock_notes_analyzer.execute.return_value = create_context(
        payload={"result": [sample_goal]}
    )
    mock_ethical_guardian.execute.return_value = create_context(
        payload={"result": {"approved": True, "concerns": []}}
    )
    
    # First call: create_task returns task_id
    # Then get_task, get_similar, update_task for execute_mission
    mock_task_manager.execute.side_effect = [
        create_context(payload={"result": "new-task-456"}),  # create_task
        create_context(payload={"result": sample_task}),  # get_task
        create_context(payload={"result": []}),  # get_similar_tasks
        create_context(payload={"result": None})  # update_task
    ]
    
    # Step 1: Analyze and create task
    ctx1 = create_context()
    analysis_result = await orchestrator._analyze_goal("Create weather plugin", ctx1)
    
    assert analysis_result["success"] is True
    task_id = analysis_result["task_id"]
    
    # Step 2: Execute mission
    ctx2 = create_context()
    mission_result = await orchestrator._execute_mission(task_id, ctx2)
    
    assert mission_result["success"] is True
    assert mission_result["status"] == "analyzing"


# Error Handling Tests

@pytest.mark.asyncio
async def test_analyze_goal_exception_handling(
    orchestrator,
    mock_notes_analyzer
):
    """Test error handling in analyze_goal."""
    mock_notes_analyzer.execute.side_effect = Exception("Analysis error")
    
    ctx = create_context()
    result = await orchestrator._analyze_goal("Goal text", ctx)
    
    assert result["success"] is False
    assert "error" in result
    assert "Analysis error" in result["error"]


@pytest.mark.asyncio
async def test_execute_mission_exception_handling(
    orchestrator,
    mock_task_manager
):
    """Test error handling in execute_mission."""
    mock_task_manager.execute.side_effect = Exception("Execution error")
    
    ctx = create_context()
    result = await orchestrator._execute_mission("task-id", ctx)
    
    assert result["success"] is False
    assert "error" in result
    assert "Execution error" in result["error"]


@pytest.mark.asyncio
async def test_get_mission_status_exception_handling(
    orchestrator,
    mock_task_manager
):
    """Test error handling in get_mission_status."""
    mock_task_manager.execute.side_effect = Exception("Status error")
    
    result = await orchestrator._get_mission_status("task-id")
    
    assert result["success"] is False
    assert "error" in result
    assert "Status error" in result["error"]
