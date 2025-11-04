"""
Task definitions for Sophia's Task Queue system.

This module defines the core Task dataclass and related enums for
the priority-based asynchronous task management system.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Callable, Awaitable, List
from datetime import datetime
from enum import Enum
import uuid


class TaskStatus(Enum):
    """Task lifecycle states."""

    PENDING = "pending"  # Waiting to start
    QUEUED = "queued"  # In queue, not yet started
    RUNNING = "running"  # Currently executing
    PAUSED = "paused"  # Temporarily stopped
    COMPLETED = "completed"  # Successfully finished
    FAILED = "failed"  # Execution failed
    CANCELLED = "cancelled"  # Manually cancelled
    TIMEOUT = "timeout"  # Exceeded time limit


class TaskPriority(Enum):
    """Task priority levels (lower value = higher priority)."""

    CRITICAL = 0  # System critical - run immediately
    HIGH = 1  # User requests, urgent tasks
    NORMAL = 2  # Regular tasks
    LOW = 3  # Background tasks, cleanup
    IDLE = 4  # Run only when system is idle


@dataclass
class TaskResult:
    """
    Standardized task execution result.

    Attributes:
        success: Whether task completed successfully
        data: Result data from task
        error: Error message if failed
        metadata: Additional result context
    """

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class Task:
    """
    Represents a task to be executed asynchronously.

    Attributes:
        task_id: Unique identifier
        name: Human-readable task name
        description: What the task does
        function: Async callable to execute
        args: Positional arguments for function
        kwargs: Keyword arguments for function
        priority: Task priority
        status: Current task status
        dependencies: List of task_ids that must complete first
        timeout: Max execution time in seconds
        max_retries: Number of retry attempts on failure
        retry_count: Current retry attempt
        created_at: When task was created
        started_at: When execution began
        completed_at: When execution finished
        result: Task execution result
        error: Error if task failed
        progress: Progress percentage (0-100)
        metadata: Additional task context
    """

    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "unnamed_task"
    description: str = ""
    function: Optional[Callable[..., Awaitable[Any]]] = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[float] = None
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[Exception] = None
    progress: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"Task({self.name}, status={self.status.value}, priority={self.priority.name})"

    def __repr__(self) -> str:
        return (
            f"Task(task_id={self.task_id!r}, name={self.name!r}, "
            f"status={self.status.value}, priority={self.priority.name})"
        )

    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state (cannot be executed)."""
        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        }

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried after failure."""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries

    def mark_started(self) -> None:
        """Mark task as started (called by executor)."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, result: Any = None) -> None:
        """Mark task as completed successfully."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        self.progress = 100.0

    def mark_failed(self, error: Exception) -> None:
        """Mark task as failed with error."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        self.retry_count += 1

    def mark_cancelled(self) -> None:
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()

    def mark_timeout(self) -> None:
        """Mark task as timed out."""
        self.status = TaskStatus.TIMEOUT
        self.completed_at = datetime.now()
        self.error = TimeoutError(f"Task {self.name} exceeded timeout of {self.timeout}s")
