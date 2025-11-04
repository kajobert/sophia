# Event System Design Specification

**Version:** 1.0  
**Date:** 2025-11-03  
**Status:** Design Specification  
**Phase:** 1 - Continuous Loop  
**Author:** Sophia AI Agent

---

## 📋 Overview

The Event System is a pub/sub (publish-subscribe) architecture that enables asynchronous, decoupled communication between Sophia's core components and plugins. This replaces the current blocking, sequential execution model with an event-driven architecture.

### **Goals**
1. ✅ Enable non-blocking operation - chat while executing tasks
2. ✅ Decouple plugins - components don't need direct references
3. ✅ Enable concurrent execution - multiple tasks in parallel
4. ✅ Improve debugging - centralized event logging
5. ✅ Support extensibility - plugins can emit/listen to events freely

---

## 🎯 Core Concepts

### **Event**
A discrete occurrence in the system that other components may be interested in.

```python
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from enum import Enum
import uuid

class EventPriority(Enum):
    """Event priority levels for processing order"""
    CRITICAL = 0   # System errors, crashes
    HIGH = 1       # User input, urgent tasks
    NORMAL = 2     # Regular tasks, updates
    LOW = 3        # Background tasks, cleanup

class EventType(Enum):
    """Core event types in Sophia"""
    # User Interaction
    USER_INPUT = "user_input"
    USER_COMMAND = "user_command"
    
    # Task Management
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    
    # Memory & Learning
    MEMORY_CREATED = "memory_created"
    MEMORY_UPDATED = "memory_updated"
    MEMORY_RETRIEVED = "memory_retrieved"
    DREAM_STARTED = "dream_started"
    DREAM_COMPLETED = "dream_completed"
    
    # Process Management
    PROCESS_STARTED = "process_started"
    PROCESS_STOPPED = "process_stopped"
    PROCESS_FAILED = "process_failed"
    PROCESS_HEALTH_CHECK = "process_health_check"
    
    # System Events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    SYSTEM_READY = "system_ready"
    
    # Plugin Events
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_FAILED = "plugin_failed"
    PLUGIN_MESSAGE = "plugin_message"
    
    # Jules Integration
    JULES_TASK_SUBMITTED = "jules_task_submitted"
    JULES_TASK_STARTED = "jules_task_started"
    JULES_TASK_COMPLETED = "jules_task_completed"
    JULES_TASK_FAILED = "jules_task_failed"
    
    # UI Updates
    UI_UPDATE = "ui_update"
    UI_NOTIFICATION = "ui_notification"
    
    # Custom Events
    CUSTOM = "custom"

@dataclass
class Event:
    """
    Immutable event object representing a system occurrence.
    
    Attributes:
        event_id: Unique identifier for this event
        event_type: Type of event (from EventType enum)
        source: Component that emitted the event
        timestamp: When the event was created
        priority: Event priority for processing order
        data: Event payload (arbitrary data)
        metadata: Additional context (user_id, session_id, etc.)
        correlation_id: Link related events together
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.CUSTOM
    source: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        """Ensure immutability by freezing after creation"""
        object.__setattr__(self, '_frozen', True)
    
    def __setattr__(self, key, value):
        if hasattr(self, '_frozen'):
            raise AttributeError(f"Event is immutable - cannot modify {key}")
        super().__setattr__(key, value)
```

### **Event Handler**
A callable that processes events. Can be sync or async.

```python
from typing import Protocol, Callable, Awaitable, Union

class EventHandler(Protocol):
    """Protocol for event handlers - sync or async"""
    def __call__(self, event: Event) -> Union[None, Awaitable[None]]:
        ...

# Example handlers
def sync_handler(event: Event) -> None:
    print(f"Received: {event.event_type}")

async def async_handler(event: Event) -> None:
    await some_async_operation(event.data)
```

### **Event Bus**
Central hub for event routing and delivery.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Event Bus                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Event Queue (Priority-based)                     │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │  │
│  │  │CRIT  │ │HIGH  │ │NORM  │ │LOW   │            │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘            │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Subscriber Registry                              │  │
│  │  EventType → List[EventHandler]                   │  │
│  │  • TASK_CREATED → [task_queue_handler, ui_handler]│  │
│  │  • USER_INPUT → [planner_handler, logger]         │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Event Dispatcher (AsyncIO)                       │  │
│  │  • Delivers events to subscribers                 │  │
│  │  • Handles sync/async handlers                    │  │
│  │  • Error handling & retry logic                   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
            ↓ publish()              ↑ subscribe()
┌──────────────────────┐    ┌──────────────────────┐
│  Publishers          │    │  Subscribers         │
│  • Kernel            │    │  • TaskQueue         │
│  • Plugins           │    │  • UI Components     │
│  • Tools             │    │  • Memory Manager    │
│  • User Interface    │    │  • Process Manager   │
└──────────────────────┘    └──────────────────────┘
```

---

## 💻 Implementation

### **File Structure**
```
core/
├── event_bus.py          # Main EventBus class
├── events.py             # Event, EventType, EventPriority definitions
└── event_handlers.py     # Built-in event handlers
```

### **Core EventBus Class**

```python
# core/event_bus.py

import asyncio
from typing import Dict, List, Set, Callable, Optional
from collections import defaultdict
from datetime import datetime
import logging

from core.events import Event, EventType, EventPriority, EventHandler

class EventBus:
    """
    Central event bus for pub/sub messaging.
    
    Features:
    - Priority-based event queuing
    - Async event processing
    - Subscribe/unsubscribe to event types
    - Event history for debugging
    - Error handling with dead letter queue
    """
    
    def __init__(self, max_history: int = 1000, max_retries: int = 3):
        self.logger = logging.getLogger("sophia.event_bus")
        
        # Subscriber registry: EventType → List[EventHandler]
        self._subscribers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        
        # Event queues by priority
        self._queues: Dict[EventPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in EventPriority
        }
        
        # Event history for debugging
        self._history: List[Event] = []
        self._max_history = max_history
        
        # Dead letter queue for failed events
        self._dead_letter_queue: List[tuple[Event, Exception]] = []
        self._max_retries = max_retries
        
        # Running state
        self._running = False
        self._dispatcher_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "handlers_executed": 0
        }
    
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: Type of event to listen for
            handler: Callable to handle the event (sync or async)
        """
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            self.logger.debug(f"Subscribed {handler.__name__} to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type"""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            self.logger.debug(f"Unsubscribed {handler.__name__} from {event_type.value}")
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to the bus.
        
        Args:
            event: Event to publish
        """
        # Add to history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        # Queue by priority
        self._queues[event.priority].put_nowait(event)
        self._stats["events_published"] += 1
        
        self.logger.debug(
            f"Published {event.event_type.value} from {event.source} "
            f"[priority={event.priority.name}]"
        )
    
    async def start(self) -> None:
        """Start the event dispatcher"""
        if self._running:
            self.logger.warning("EventBus already running")
            return
        
        self._running = True
        self._dispatcher_task = asyncio.create_task(self._dispatch_loop())
        self.logger.info("EventBus started")
    
    async def stop(self) -> None:
        """Stop the event dispatcher gracefully"""
        if not self._running:
            return
        
        self._running = False
        if self._dispatcher_task:
            self._dispatcher_task.cancel()
            try:
                await self._dispatcher_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("EventBus stopped")
    
    async def _dispatch_loop(self) -> None:
        """Main event processing loop - checks queues by priority"""
        while self._running:
            try:
                # Check queues in priority order (CRITICAL → LOW)
                event = None
                for priority in EventPriority:
                    try:
                        event = self._queues[priority].get_nowait()
                        break
                    except asyncio.QueueEmpty:
                        continue
                
                if event is None:
                    # No events in any queue - wait a bit
                    await asyncio.sleep(0.01)
                    continue
                
                # Dispatch event to subscribers
                await self._dispatch_event(event)
                self._stats["events_processed"] += 1
                
            except Exception as e:
                self.logger.error(f"Error in dispatch loop: {e}", exc_info=True)
    
    async def _dispatch_event(self, event: Event) -> None:
        """
        Dispatch event to all subscribers.
        
        Args:
            event: Event to dispatch
        """
        handlers = self._subscribers.get(event.event_type, [])
        
        if not handlers:
            self.logger.debug(f"No handlers for {event.event_type.value}")
            return
        
        # Execute all handlers (concurrently if async)
        tasks = []
        for handler in handlers:
            tasks.append(self._execute_handler(handler, event))
        
        # Wait for all handlers to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for errors
        for handler, result in zip(handlers, results):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Handler {handler.__name__} failed for {event.event_type.value}: {result}",
                    exc_info=result
                )
                self._stats["events_failed"] += 1
                self._dead_letter_queue.append((event, result))
            else:
                self._stats["handlers_executed"] += 1
    
    async def _execute_handler(self, handler: EventHandler, event: Event) -> None:
        """
        Execute a single handler (sync or async).
        
        Args:
            handler: Handler to execute
            event: Event to pass to handler
        """
        if asyncio.iscoroutinefunction(handler):
            await handler(event)
        else:
            # Run sync handler in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, handler, event)
    
    def get_stats(self) -> dict:
        """Get event bus statistics"""
        return {
            **self._stats,
            "active_subscribers": sum(len(handlers) for handlers in self._subscribers.values()),
            "queue_sizes": {
                priority.name: self._queues[priority].qsize()
                for priority in EventPriority
            },
            "dead_letter_size": len(self._dead_letter_queue)
        }
    
    def get_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type (optional)
            limit: Max number of events to return
        
        Returns:
            List of events (most recent first)
        """
        history = self._history[::-1]  # Reverse for most recent first
        
        if event_type:
            history = [e for e in history if e.event_type == event_type]
        
        return history[:limit]
```

---

## 🔌 Integration with Kernel

### **Kernel Changes**

```python
# core/kernel.py

from core.event_bus import EventBus
from core.events import Event, EventType, EventPriority

class Kernel:
    def __init__(self):
        # ... existing init ...
        
        # Create event bus
        self.event_bus = EventBus()
        
        # Add to shared context
        self.context.event_bus = self.event_bus
    
    async def startup(self):
        """Startup sequence"""
        # Start event bus first
        await self.event_bus.start()
        
        # Publish startup event
        self.event_bus.publish(Event(
            event_type=EventType.SYSTEM_STARTUP,
            source="kernel",
            priority=EventPriority.HIGH,
            data={"version": "2.0", "mode": self.context.mode}
        ))
        
        # ... rest of startup ...
    
    async def shutdown(self):
        """Shutdown sequence"""
        # Publish shutdown event
        self.event_bus.publish(Event(
            event_type=EventType.SYSTEM_SHUTDOWN,
            source="kernel",
            priority=EventPriority.CRITICAL
        ))
        
        # Wait for events to process
        await asyncio.sleep(0.5)
        
        # Stop event bus
        await self.event_bus.stop()
        
        # ... rest of shutdown ...
    
    async def consciousness_loop(self):
        """Main loop - now event-driven"""
        while self.context.running:
            try:
                # Check for user input (non-blocking)
                user_input = await self._get_user_input()
                
                if user_input:
                    # Publish user input event
                    self.event_bus.publish(Event(
                        event_type=EventType.USER_INPUT,
                        source="kernel",
                        priority=EventPriority.HIGH,
                        data={"input": user_input}
                    ))
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal")
                break
            except Exception as e:
                self.logger.error(f"Error in consciousness loop: {e}", exc_info=True)
                self.event_bus.publish(Event(
                    event_type=EventType.SYSTEM_ERROR,
                    source="kernel",
                    priority=EventPriority.CRITICAL,
                    data={"error": str(e)}
                ))
```

---

## 📊 Event Flow Examples

### **Example 1: User Asks a Question**

```
1. User types in terminal: "What's the weather?"

2. Kernel receives input → Publishes:
   Event(
       event_type=USER_INPUT,
       source="kernel",
       priority=HIGH,
       data={"input": "What's the weather?"}
   )

3. Planner subscribes to USER_INPUT → Receives event
   → Analyzes input → Creates task

4. Planner publishes:
   Event(
       event_type=TASK_CREATED,
       source="cognitive_planner",
       priority=NORMAL,
       data={"task_id": "task_123", "description": "Get weather"}
   )

5. TaskQueue subscribes to TASK_CREATED → Receives event
   → Adds task to queue → Starts execution

6. TaskQueue publishes:
   Event(
       event_type=TASK_STARTED,
       source="task_queue",
       priority=NORMAL,
       data={"task_id": "task_123"}
   )

7. UI subscribes to TASK_STARTED → Updates status bar

8. Task completes → TaskQueue publishes:
   Event(
       event_type=TASK_COMPLETED,
       source="task_queue",
       priority=NORMAL,
       data={"task_id": "task_123", "result": "Sunny, 72°F"}
   )

9. UI displays result, Memory stores conversation
```

### **Example 2: Jules Task in Background**

```
1. Task starts → Publishes JULES_TASK_STARTED

2. User asks another question while Jules is running
   → Publishes USER_INPUT

3. Both events processed concurrently:
   - Jules task continues in background
   - New task created from user input
   
4. No blocking - seamless multitasking
```

---

## 🧪 Testing Strategy

### **Unit Tests**

```python
# tests/core/test_event_bus.py

import pytest
import asyncio
from core.event_bus import EventBus
from core.events import Event, EventType, EventPriority

@pytest.mark.asyncio
async def test_subscribe_and_publish():
    """Test basic pub/sub"""
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
    
    await bus.stop()

@pytest.mark.asyncio
async def test_priority_ordering():
    """Test that CRITICAL events process before NORMAL"""
    bus = EventBus()
    processed = []
    
    async def handler(event: Event):
        processed.append(event.priority)
    
    bus.subscribe(EventType.CUSTOM, handler)
    await bus.start()
    
    # Publish in reverse priority order
    bus.publish(Event(event_type=EventType.CUSTOM, priority=EventPriority.LOW))
    bus.publish(Event(event_type=EventType.CUSTOM, priority=EventPriority.CRITICAL))
    bus.publish(Event(event_type=EventType.CUSTOM, priority=EventPriority.NORMAL))
    
    await asyncio.sleep(0.2)
    
    # Should process CRITICAL first
    assert processed[0] == EventPriority.CRITICAL
    
    await bus.stop()

@pytest.mark.asyncio
async def test_async_handler():
    """Test async event handlers"""
    bus = EventBus()
    result = []
    
    async def async_handler(event: Event):
        await asyncio.sleep(0.05)
        result.append("done")
    
    bus.subscribe(EventType.TASK_CREATED, async_handler)
    await bus.start()
    
    bus.publish(Event(event_type=EventType.TASK_CREATED))
    await asyncio.sleep(0.1)
    
    assert result == ["done"]
    await bus.stop()
```

---

## 🛡️ Error Handling

### **Handler Failures**
- If a handler throws an exception, it's logged but doesn't stop other handlers
- Failed events go to dead letter queue for inspection
- Max retry attempts configurable (default: 3)

### **Event Bus Failure**
- If dispatcher crashes, system publishes SYSTEM_ERROR event
- Graceful degradation - plugins can still function without events
- Dead letter queue persisted for post-mortem analysis

---

## 📈 Performance Considerations

### **Throughput**
- Target: 1000+ events/second
- Async processing prevents blocking
- Priority queues ensure critical events aren't starved

### **Memory**
- Event history limited (default: 1000 events)
- Dead letter queue capped (default: 100 events)
- Old events pruned automatically

### **Latency**
- Critical events: <10ms
- Normal events: <100ms
- Low priority: <1s

---

## 🔄 Migration Path

### **Phase 1: Parallel Run**
- Event bus runs alongside existing blocking code
- Plugins can opt-in to events
- No breaking changes

### **Phase 2: Gradual Migration**
- Core plugins migrate to event-driven
- TaskQueue starts consuming events
- UI updates via events

### **Phase 3: Full Cutover**
- Remove blocking consciousness loop
- All communication via events
- Clean up legacy code

---

## 📚 API Reference

### **EventBus Methods**

```python
def subscribe(event_type: EventType, handler: EventHandler) -> None
def unsubscribe(event_type: EventType, handler: EventHandler) -> None
def publish(event: Event) -> None
async def start() -> None
async def stop() -> None
def get_stats() -> dict
def get_history(event_type: Optional[EventType], limit: int) -> List[Event]
```

### **Event Properties**

```python
event_id: str              # Unique ID
event_type: EventType      # Type of event
source: str                # Who published it
timestamp: datetime        # When it happened
priority: EventPriority    # Processing priority
data: dict                 # Event payload
metadata: dict             # Additional context
correlation_id: str        # Link related events
```

---

## ✅ Success Criteria

- [ ] EventBus can handle 1000+ events/second
- [ ] Priority queues work correctly
- [ ] Async and sync handlers both supported
- [ ] Event history accessible for debugging
- [ ] Dead letter queue captures failed events
- [ ] Unit tests achieve >90% coverage
- [ ] Integration with Kernel successful
- [ ] No performance regression in existing features

---

## 🔗 Related Documents

- `TASK_QUEUE.md` - Uses events for task management
- `LOOP_MIGRATION.md` - Migration strategy from blocking to event-driven
- `GUARDRAILS.md` - Safety checks for event processing
- `docs/en/02_architecture.md` - Core architecture overview

---

**Status:** Ready for Implementation ✅  
**Next Steps:** Implement `core/event_bus.py` and `core/events.py`
