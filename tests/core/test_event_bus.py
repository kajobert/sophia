"""
Unit tests for Event Bus system.

Tests cover:
- Basic pub/sub functionality
- Priority ordering
- Async/sync handler support
- Event history
- Error handling
- Statistics
"""

import pytest
import asyncio
from datetime import datetime

from core.event_bus import EventBus
from core.events import Event, EventType, EventPriority


@pytest.mark.asyncio
async def test_subscribe_and_publish():
    """Test basic pub/sub functionality."""
    bus = EventBus()
    received = []
    
    def handler(event: Event):
        received.append(event)
    
    bus.subscribe(EventType.USER_INPUT, handler)
    
    await bus.start()
    
    event = Event(event_type=EventType.USER_INPUT, source="test")
    bus.publish(event)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    assert len(received) == 1
    assert received[0].event_type == EventType.USER_INPUT
    assert received[0].source == "test"
    
    await bus.stop()


@pytest.mark.asyncio
async def test_multiple_subscribers():
    """Test that multiple handlers receive the same event."""
    bus = EventBus()
    received1 = []
    received2 = []
    
    def handler1(event: Event):
        received1.append(event)
    
    def handler2(event: Event):
        received2.append(event)
    
    bus.subscribe(EventType.TASK_COMPLETED, handler1)
    bus.subscribe(EventType.TASK_COMPLETED, handler2)
    
    await bus.start()
    
    event = Event(event_type=EventType.TASK_COMPLETED, source="test")
    bus.publish(event)
    
    await asyncio.sleep(0.1)
    
    assert len(received1) == 1
    assert len(received2) == 1
    assert received1[0].event_id == received2[0].event_id
    
    await bus.stop()


@pytest.mark.asyncio
async def test_priority_ordering():
    """Test that CRITICAL events process before NORMAL events."""
    bus = EventBus()
    processed = []
    
    async def handler(event: Event):
        processed.append(event.priority)
        await asyncio.sleep(0.01)  # Small delay to ensure ordering
    
    bus.subscribe(EventType.CUSTOM, handler)
    await bus.start()
    
    # Publish in reverse priority order
    bus.publish(Event(
        event_type=EventType.CUSTOM,
        priority=EventPriority.LOW,
        source="test"
    ))
    bus.publish(Event(
        event_type=EventType.CUSTOM,
        priority=EventPriority.CRITICAL,
        source="test"
    ))
    bus.publish(Event(
        event_type=EventType.CUSTOM,
        priority=EventPriority.NORMAL,
        source="test"
    ))
    
    await asyncio.sleep(0.2)
    
    # Should process CRITICAL first
    assert processed[0] == EventPriority.CRITICAL
    
    await bus.stop()


@pytest.mark.asyncio
async def test_async_handler():
    """Test async event handlers."""
    bus = EventBus()
    result = []
    
    async def async_handler(event: Event):
        await asyncio.sleep(0.05)
        result.append(event.data.get("value"))
    
    bus.subscribe(EventType.TASK_CREATED, async_handler)
    await bus.start()
    
    bus.publish(Event(
        event_type=EventType.TASK_CREATED,
        source="test",
        data={"value": "done"}
    ))
    
    await asyncio.sleep(0.1)
    
    assert result == ["done"]
    await bus.stop()


@pytest.mark.asyncio
async def test_sync_handler():
    """Test synchronous event handlers."""
    bus = EventBus()
    result = []
    
    def sync_handler(event: Event):
        result.append(event.data.get("value"))
    
    bus.subscribe(EventType.TASK_STARTED, sync_handler)
    await bus.start()
    
    bus.publish(Event(
        event_type=EventType.TASK_STARTED,
        source="test",
        data={"value": "started"}
    ))
    
    await asyncio.sleep(0.1)
    
    assert result == ["started"]
    await bus.stop()


@pytest.mark.asyncio
async def test_unsubscribe():
    """Test unsubscribing handlers."""
    bus = EventBus()
    received = []
    
    def handler(event: Event):
        received.append(event)
    
    bus.subscribe(EventType.USER_INPUT, handler)
    await bus.start()
    
    # Publish with subscription
    bus.publish(Event(event_type=EventType.USER_INPUT, source="test1"))
    await asyncio.sleep(0.05)
    
    # Unsubscribe
    bus.unsubscribe(EventType.USER_INPUT, handler)
    
    # Publish without subscription
    bus.publish(Event(event_type=EventType.USER_INPUT, source="test2"))
    await asyncio.sleep(0.05)
    
    # Should only receive first event
    assert len(received) == 1
    assert received[0].source == "test1"
    
    await bus.stop()


@pytest.mark.asyncio
async def test_event_history():
    """Test event history tracking."""
    bus = EventBus(max_history=5)
    await bus.start()
    
    # Publish multiple events
    for i in range(10):
        bus.publish(Event(
            event_type=EventType.CUSTOM,
            source=f"test{i}",
            data={"index": i}
        ))
    
    await asyncio.sleep(0.1)
    
    # Should only keep last 5 events
    history = bus.get_history()
    assert len(history) <= 5
    
    # Should be in reverse order (most recent first)
    assert history[0].data["index"] > history[-1].data["index"]
    
    await bus.stop()


@pytest.mark.asyncio
async def test_event_history_filtering():
    """Test filtering event history by type."""
    bus = EventBus()
    await bus.start()
    
    # Publish different event types
    bus.publish(Event(event_type=EventType.USER_INPUT, source="test"))
    bus.publish(Event(event_type=EventType.TASK_CREATED, source="test"))
    bus.publish(Event(event_type=EventType.USER_INPUT, source="test"))
    
    await asyncio.sleep(0.1)
    
    # Filter by type
    user_input_events = bus.get_history(event_type=EventType.USER_INPUT)
    assert len(user_input_events) == 2
    assert all(e.event_type == EventType.USER_INPUT for e in user_input_events)
    
    await bus.stop()


@pytest.mark.asyncio
async def test_statistics():
    """Test event bus statistics."""
    bus = EventBus()
    
    def handler(event: Event):
        pass
    
    bus.subscribe(EventType.CUSTOM, handler)
    await bus.start()
    
    # Publish events
    for i in range(5):
        bus.publish(Event(event_type=EventType.CUSTOM, source="test"))
    
    await asyncio.sleep(0.1)
    
    stats = bus.get_stats()
    assert stats["events_published"] == 5
    assert stats["events_processed"] == 5
    assert stats["handlers_executed"] == 5
    assert stats["active_subscribers"] == 1
    
    await bus.stop()


@pytest.mark.asyncio
async def test_error_handling():
    """Test that handler errors don't crash the bus."""
    bus = EventBus()
    received = []
    
    def failing_handler(event: Event):
        raise ValueError("Test error")
    
    def working_handler(event: Event):
        received.append(event)
    
    bus.subscribe(EventType.CUSTOM, failing_handler)
    bus.subscribe(EventType.CUSTOM, working_handler)
    
    await bus.start()
    
    bus.publish(Event(event_type=EventType.CUSTOM, source="test"))
    
    await asyncio.sleep(0.1)
    
    # Working handler should still receive the event
    assert len(received) == 1
    
    # Failed event should be in dead letter queue
    stats = bus.get_stats()
    assert stats["events_failed"] == 1
    assert stats["dead_letter_size"] == 1
    
    await bus.stop()


@pytest.mark.asyncio
async def test_dead_letter_queue():
    """Test dead letter queue for failed events."""
    bus = EventBus()
    
    def failing_handler(event: Event):
        raise RuntimeError("Handler failed")
    
    bus.subscribe(EventType.CUSTOM, failing_handler)
    await bus.start()
    
    event = Event(event_type=EventType.CUSTOM, source="test", data={"key": "value"})
    bus.publish(event)
    
    await asyncio.sleep(0.1)
    
    # Get dead letters
    dead_letters = bus.clear_dead_letter_queue()
    assert len(dead_letters) == 1
    
    failed_event, exception = dead_letters[0]
    assert failed_event.event_id == event.event_id
    assert isinstance(exception, RuntimeError)
    
    # Queue should be cleared
    assert bus.get_stats()["dead_letter_size"] == 0
    
    await bus.stop()


@pytest.mark.asyncio
async def test_event_immutability():
    """Test that events cannot be modified after creation."""
    event = Event(
        event_type=EventType.USER_INPUT,
        source="test",
        data={"key": "value"}
    )
    
    # Should raise error when trying to modify
    with pytest.raises(AttributeError, match="immutable"):
        event.source = "modified"


@pytest.mark.asyncio
async def test_no_handlers_for_event():
    """Test publishing event with no subscribers."""
    bus = EventBus()
    await bus.start()
    
    # Should not crash
    bus.publish(Event(event_type=EventType.CUSTOM, source="test"))
    
    await asyncio.sleep(0.1)
    
    stats = bus.get_stats()
    assert stats["events_published"] == 1
    assert stats["events_processed"] == 1
    
    await bus.stop()


@pytest.mark.asyncio
async def test_stop_idempotent():
    """Test that calling stop() multiple times is safe."""
    bus = EventBus()
    await bus.start()
    await bus.stop()
    await bus.stop()  # Should not crash


@pytest.mark.asyncio
async def test_start_idempotent():
    """Test that calling start() multiple times is safe."""
    bus = EventBus()
    await bus.start()
    await bus.start()  # Should log warning but not crash
    await bus.stop()


@pytest.mark.asyncio
async def test_event_metadata():
    """Test event metadata and correlation_id."""
    bus = EventBus()
    received = []
    
    def handler(event: Event):
        received.append(event)
    
    bus.subscribe(EventType.CUSTOM, handler)
    await bus.start()
    
    correlation_id = "correlation-123"
    event = Event(
        event_type=EventType.CUSTOM,
        source="test",
        metadata={"user_id": "user-456", "session": "sess-789"},
        correlation_id=correlation_id
    )
    bus.publish(event)
    
    await asyncio.sleep(0.1)
    
    assert len(received) == 1
    assert received[0].correlation_id == correlation_id
    assert received[0].metadata["user_id"] == "user-456"
    
    await bus.stop()


@pytest.mark.asyncio
async def test_concurrent_publish():
    """Test publishing events concurrently."""
    bus = EventBus()
    received = []
    
    async def handler(event: Event):
        received.append(event)
    
    bus.subscribe(EventType.CUSTOM, handler)
    await bus.start()
    
    # Publish many events concurrently
    tasks = []
    for i in range(100):
        event = Event(
            event_type=EventType.CUSTOM,
            source=f"test{i}",
            data={"index": i}
        )
        bus.publish(event)
    
    await asyncio.sleep(0.5)
    
    # All events should be received
    assert len(received) == 100
    
    await bus.stop()
