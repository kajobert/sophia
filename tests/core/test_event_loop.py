"""
Integration test for Event-Driven Consciousness Loop (Phase 1).

Tests the basic functionality of the event-driven architecture.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock

from core.event_bus import EventBus
from core.task_queue import TaskQueue
from core.event_loop import EventDrivenLoop
from core.context import SharedContext
from core.events import Event, EventType, EventPriority


@pytest.fixture
async def event_bus():
    """Create and start EventBus."""
    bus = EventBus()
    await bus.start()
    yield bus
    await bus.stop()


@pytest.fixture
async def task_queue(event_bus):
    """Create and start TaskQueue."""
    queue = TaskQueue(event_bus=event_bus, max_workers=2)
    await queue.start()
    yield queue
    await queue.stop()


@pytest.fixture
def plugin_manager():
    """Mock plugin manager."""
    manager = Mock()
    manager.get_plugins_by_type.return_value = []
    return manager


@pytest.fixture
def event_loop_instance(plugin_manager, event_bus, task_queue):
    """Create EventDrivenLoop instance."""
    all_plugins_map = {}
    return EventDrivenLoop(
        plugin_manager=plugin_manager,
        all_plugins_map=all_plugins_map,
        event_bus=event_bus,
        task_queue=task_queue
    )


@pytest.mark.asyncio
async def test_event_loop_initialization(event_loop_instance):
    """Test that event loop initializes and registers handlers."""
    assert event_loop_instance is not None
    assert event_loop_instance.is_running is False
    assert event_loop_instance.event_bus is not None
    assert event_loop_instance.task_queue is not None


@pytest.mark.asyncio
async def test_event_loop_handles_user_input(event_loop_instance, event_bus):
    """Test that event loop receives and handles USER_INPUT events."""
    # Track if handler was called
    handler_called = []
    
    async def track_handler(event):
        handler_called.append(event)
    
    # Replace handler with tracking version
    original_handler = event_loop_instance._handle_user_input
    event_loop_instance._handle_user_input = track_handler
    
    # Re-subscribe with new handler
    event_bus.subscribe(EventType.USER_INPUT, track_handler)
    
    # Publish USER_INPUT event
    event_bus.publish(Event(
        event_type=EventType.USER_INPUT,
        source="test",
        priority=EventPriority.HIGH,
        data={"input": "test input", "session_id": "test-123"}
    ))
    
    # Wait for processing
    await asyncio.sleep(0.2)
    
    # Verify handler was called
    assert len(handler_called) > 0
    assert handler_called[0].data["input"] == "test input"


@pytest.mark.asyncio
async def test_event_loop_single_run_mode(event_loop_instance, event_bus):
    """Test single-run mode (non-interactive)."""
    # Create context
    context = SharedContext(
        session_id="test-123",
        current_state="INITIALIZING",
        logger=Mock()
    )
    context.event_bus = event_bus
    
    # Track published events
    published_events = []
    
    def track_events(event):
        published_events.append(event)
    
    event_bus.subscribe(EventType.USER_INPUT, track_events)
    
    # Run in single-run mode
    await event_loop_instance.run(context, single_run_input="test input")
    
    # Wait for processing
    await asyncio.sleep(0.2)
    
    # Verify event was published
    assert len(published_events) > 0
    user_input_events = [e for e in published_events if e.data.get("input") == "test input"]
    assert len(user_input_events) > 0


@pytest.mark.asyncio
async def test_event_loop_stop(event_loop_instance):
    """Test that event loop can be stopped."""
    # Start loop in background
    context = SharedContext(
        session_id="test-123",
        current_state="RUNNING",
        logger=Mock()
    )
    
    loop_task = asyncio.create_task(event_loop_instance.run(context))
    
    # Wait for loop to start
    await asyncio.sleep(0.1)
    
    # Stop loop
    event_loop_instance.stop()
    
    # Wait for loop to finish
    await asyncio.sleep(0.2)
    
    # Verify loop stopped
    assert event_loop_instance.is_running is False
    
    # Cancel task if still running
    if not loop_task.done():
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_event_loop_handles_system_error(event_loop_instance, event_bus):
    """Test that event loop handles SYSTEM_ERROR events."""
    # Track if handler was called
    handler_called = []
    
    async def track_handler(event):
        handler_called.append(event)
    
    # Replace handler with tracking version
    event_loop_instance._handle_system_error = track_handler
    
    # Re-subscribe with new handler
    event_bus.subscribe(EventType.SYSTEM_ERROR, track_handler)
    
    # Publish SYSTEM_ERROR event
    event_bus.publish(Event(
        event_type=EventType.SYSTEM_ERROR,
        source="test",
        priority=EventPriority.CRITICAL,
        data={"error": "test error"}
    ))
    
    # Wait for processing
    await asyncio.sleep(0.2)
    
    # Verify handler was called
    assert len(handler_called) > 0
    assert handler_called[0].data["error"] == "test error"
