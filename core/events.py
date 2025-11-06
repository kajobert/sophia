"""
Event System - Core event definitions for Sophia's event-driven architecture.

This module defines the Event dataclass and related enums for Sophia's pub/sub
event system. Events are immutable messages that flow through the EventBus.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class EventPriority(Enum):
    """Event priority levels for processing order."""

    CRITICAL = 0  # System errors, crashes
    HIGH = 1  # User input, urgent tasks
    NORMAL = 2  # Regular tasks, updates
    LOW = 3  # Background tasks, cleanup


class EventType(Enum):
    """Core event types in Sophia."""

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
    
    # Autonomous Operation (AMI 1.0)
    PROACTIVE_HEARTBEAT = "proactive_heartbeat"  # Periodic autonomous trigger
    DREAM_TRIGGER = "dream_trigger"  # Start memory consolidation
    DREAM_COMPLETE = "dream_complete"  # Consolidation finished
    HYPOTHESIS_CREATED = "hypothesis_created"  # New improvement hypothesis
    HYPOTHESIS_TESTED = "hypothesis_tested"  # Benchmark results ready
    HYPOTHESIS_DEPLOYED = "hypothesis_deployed"  # Approved fix deployed to production
    SYSTEM_RECOVERY = "system_recovery"  # Recovered from crash
    NOTES_UPDATED = "notes_updated"  # roberts-notes.txt changed
    BUDGET_WARNING = "budget_warning"  # Approaching spending limit (monthly)
    MODEL_OPTIMIZED = "model_optimized"  # LLM configuration improved
    
    # Budget Pacing (Phase 2.5)
    BUDGET_PACE_WARNING = "budget_pace_warning"  # Daily budget overspending
    BUDGET_PHASE_CHANGED = "budget_phase_changed"  # Conservative→Balanced→Aggressive
    BUDGET_REQUEST_CREATED = "budget_request_created"  # Urgent approval needed
    BUDGET_REQUEST_APPROVED = "budget_request_approved"  # User approved request
    BUDGET_REQUEST_DENIED = "budget_request_denied"  # User denied request
    BUDGET_REQUEST_TIMEOUT = "budget_request_timeout"  # No response after 2h
    TASK_COMPLEXITY_HIGH = "task_complexity_high"  # Task requires expert LLM

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
        """Ensure immutability by freezing after creation."""
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, key, value):
        """Prevent modification after initialization."""
        if hasattr(self, "_frozen"):
            raise AttributeError(f"Event is immutable - cannot modify {key}")
        super().__setattr__(key, value)

    def __str__(self) -> str:
        """String representation of event."""
        return (
            f"Event({self.event_type.value}, "
            f"source={self.source}, "
            f"priority={self.priority.name}, "
            f"id={self.event_id[:8]}...)"
        )

    def __repr__(self) -> str:
        """Detailed representation of event."""
        return (
            f"Event(event_id='{self.event_id}', "
            f"event_type={self.event_type}, "
            f"source='{self.source}', "
            f"priority={self.priority}, "
            f"timestamp={self.timestamp.isoformat()})"
        )
