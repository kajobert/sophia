"""
Unit tests for Core Process Manager Plugin.

Tests cover:
- Process creation and management
- Background process monitoring
- Event emissions
- Process state tracking
- Error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from plugins.core_process_manager import (
    CoreProcessManager,
    BackgroundProcess,
    ProcessType,
    ProcessState
)
from core.context import SharedContext
from core.event_bus import EventBus
from core.events import EventType


@pytest.fixture
async def event_bus():
    """Create and start EventBus."""
    bus = EventBus()
    await bus.start()
    yield bus
    await bus.stop()


@pytest.fixture
def context(event_bus):
    """Create SharedContext with event bus."""
    ctx = SharedContext(
        session_id="test-session",
        current_state="TESTING",
        logger=Mock()
    )
    ctx.event_bus = event_bus
    return ctx


@pytest.fixture
def process_manager():
    """Create CoreProcessManager instance."""
    manager = CoreProcessManager()
    manager.setup({})
    return manager


def test_process_manager_initialization(process_manager):
    """Test that process manager initializes correctly."""
    assert process_manager.name == "core_process_manager"
    assert process_manager.plugin_type.name == "CORE"  # Fixed: use .name instead of .value
    assert len(process_manager.processes) == 0


def test_background_process_creation():
    """Test BackgroundProcess dataclass."""
    process = BackgroundProcess(
        process_type=ProcessType.TEST_SUITE,
        name="Test Process",
        command="pytest tests/"
    )
    
    assert process.process_type == ProcessType.TEST_SUITE
    assert process.name == "Test Process"
    assert process.command == "pytest tests/"
    assert process.state == ProcessState.STARTING
    assert process.is_terminal is False


def test_background_process_to_dict():
    """Test BackgroundProcess serialization."""
    process = BackgroundProcess(
        process_type=ProcessType.JULES_SESSION,
        name="Jules Task",
        command="jules session create",
        metadata={"session_id": "123"}
    )
    
    data = process.to_dict()
    
    assert data["process_type"] == "jules_session"
    assert data["name"] == "Jules Task"
    assert data["command"] == "jules session create"
    assert data["metadata"]["session_id"] == "123"


def test_process_manager_tool_definitions(process_manager):
    """Test that tool definitions are properly formatted."""
    tools = process_manager.get_tool_definitions()
    
    assert len(tools) == 4
    
    tool_names = [t["function"]["name"] for t in tools]
    assert "start_background_process" in tool_names
    assert "get_process_status" in tool_names
    assert "stop_background_process" in tool_names
    assert "list_background_processes" in tool_names


@pytest.mark.asyncio
async def test_start_background_process_success(process_manager, context):
    """Test starting a background process successfully."""
    result = await process_manager.start_background_process(
        context=context,
        process_type="test_suite",
        name="Test Run",
        command="echo 'Hello World'",
        timeout=5
    )
    
    assert result["success"] is True
    assert "process_id" in result
    assert result["pid"] is not None
    assert result["state"] == "running"
    
    # Wait for process to complete
    await asyncio.sleep(0.5)
    
    # Check process is in registry
    process_id = result["process_id"]
    assert process_id in process_manager.processes
    
    process = process_manager.processes[process_id]
    assert process.state == ProcessState.COMPLETED
    assert process.exit_code == 0
    assert "Hello World" in process.output


@pytest.mark.asyncio
async def test_start_background_process_failure(process_manager, context):
    """Test starting a process that fails."""
    result = await process_manager.start_background_process(
        context=context,
        process_type="test_suite",
        name="Failing Test",
        command="exit 1",  # Immediately exit with error
        timeout=5
    )
    
    assert result["success"] is True  # Start succeeds
    
    # Wait for process to complete
    await asyncio.sleep(0.5)
    
    process_id = result["process_id"]
    process = process_manager.processes[process_id]
    
    assert process.state == ProcessState.FAILED
    assert process.exit_code == 1


@pytest.mark.asyncio
async def test_start_background_process_timeout(process_manager, context):
    """Test process timeout."""
    result = await process_manager.start_background_process(
        context=context,
        process_type="custom",
        name="Slow Process",
        command="sleep 10",  # Sleep longer than timeout
        timeout=1  # 1 second timeout
    )
    
    assert result["success"] is True
    
    # Wait for timeout
    await asyncio.sleep(2)
    
    process_id = result["process_id"]
    process = process_manager.processes[process_id]
    
    assert process.state == ProcessState.TIMEOUT


@pytest.mark.asyncio
async def test_get_process_status(process_manager, context):
    """Test getting process status."""
    # Start a process
    result = await process_manager.start_background_process(
        context=context,
        process_type="test_suite",
        name="Status Test",
        command="echo 'test output'",
        timeout=5
    )
    
    process_id = result["process_id"]
    
    # Get status
    status = await process_manager.get_process_status(context, process_id)
    
    assert status["success"] is True
    assert status["process_id"] == process_id
    assert status["name"] == "Status Test"
    assert status["process_type"] == "test_suite"


@pytest.mark.asyncio
async def test_get_process_status_not_found(process_manager, context):
    """Test getting status of non-existent process."""
    status = await process_manager.get_process_status(context, "nonexistent")
    
    assert status["success"] is False
    assert "not found" in status["error"]


@pytest.mark.asyncio
async def test_stop_background_process(process_manager, context):
    """Test stopping a running process."""
    # Start a long-running process
    result = await process_manager.start_background_process(
        context=context,
        process_type="custom",
        name="Long Running",
        command="sleep 30",
        timeout=0
    )
    
    process_id = result["process_id"]
    
    # Wait a bit for process to start
    await asyncio.sleep(0.2)
    
    # Stop the process
    stop_result = await process_manager.stop_background_process(
        context=context,
        process_id=process_id,
        force=False
    )
    
    assert stop_result["success"] is True
    
    # Wait for process to stop
    await asyncio.sleep(0.5)
    
    process = process_manager.processes[process_id]
    assert process.state == ProcessState.CANCELLED


@pytest.mark.asyncio
async def test_list_background_processes(process_manager, context):
    """Test listing processes with filters."""
    # Start multiple processes
    await process_manager.start_background_process(
        context, "test_suite", "Test 1", "echo 'test1'", 5
    )
    await process_manager.start_background_process(
        context, "build", "Build 1", "echo 'build1'", 5
    )
    await process_manager.start_background_process(
        context, "custom", "Custom 1", "sleep 5", 0
    )
    
    # Wait a bit
    await asyncio.sleep(0.3)
    
    # List all
    result = await process_manager.list_background_processes(context, "all")
    assert result["success"] is True
    assert result["count"] >= 3
    
    # List running
    result = await process_manager.list_background_processes(context, "running")
    assert result["success"] is True
    # At least the sleep process should still be running
    assert result["count"] >= 1
    
    # List completed
    result = await process_manager.list_background_processes(context, "completed")
    assert result["success"] is True
    # The echo processes should have completed
    assert result["count"] >= 2


@pytest.mark.asyncio
async def test_process_events_emitted(process_manager, context, event_bus):
    """Test that process events are emitted correctly."""
    events_received = []
    
    def track_event(event):
        events_received.append(event)
    
    # Subscribe to process events
    event_bus.subscribe(EventType.PROCESS_STARTED, track_event)
    event_bus.subscribe(EventType.PROCESS_STOPPED, track_event)
    
    # Start a process
    await process_manager.start_background_process(
        context=context,
        process_type="test_suite",
        name="Event Test",
        command="echo 'events work'",
        timeout=5
    )
    
    # Wait for process to complete
    await asyncio.sleep(0.5)
    
    # Should have received PROCESS_STARTED and PROCESS_STOPPED
    assert len(events_received) >= 2
    
    started_events = [e for e in events_received if e.event_type == EventType.PROCESS_STARTED]
    stopped_events = [e for e in events_received if e.event_type == EventType.PROCESS_STOPPED]
    
    assert len(started_events) >= 1
    assert len(stopped_events) >= 1
    
    # Verify event data
    started = started_events[0]
    assert started.data["name"] == "Event Test"
    assert started.data["process_type"] == "test_suite"


@pytest.mark.asyncio
async def test_concurrent_processes(process_manager, context):
    """Test running multiple processes concurrently."""
    # Start 5 concurrent processes
    tasks = []
    for i in range(5):
        task = process_manager.start_background_process(
            context=context,
            process_type="test_suite",
            name=f"Concurrent {i}",
            command=f"echo 'process {i}'",
            timeout=5
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # All should start successfully
    assert all(r["success"] for r in results)
    
    # Wait for all to complete
    await asyncio.sleep(1)
    
    # All should be in processes registry
    assert len(process_manager.processes) >= 5
    
    # Most should have completed
    completed = [p for p in process_manager.processes.values() if p.state == ProcessState.COMPLETED]
    assert len(completed) >= 5
