# Task Queue Design Specification

**Version:** 1.0  
**Date:** 2025-11-03  
**Status:** Design Specification  
**Phase:** 1 - Continuous Loop  
**Author:** Sophia AI Agent

---

## 📋 Overview

The Task Queue is a priority-based, asynchronous task management system that enables Sophia to execute multiple tasks concurrently while maintaining control over execution order, resource allocation, and error recovery.

### **Goals**
1. ✅ Concurrent task execution - run multiple tasks in parallel
2. ✅ Priority-based scheduling - critical tasks first
3. ✅ Resource management - limit concurrent executions
4. ✅ Progress tracking - monitor task status in real-time
5. ✅ Error recovery - retry failed tasks, graceful degradation
6. ✅ Dependency management - tasks can depend on other tasks

---

## 🎯 Core Concepts

### **Task**
A unit of work to be executed asynchronously.

```python
from dataclasses import dataclass, field
from typing import Any, Optional, Callable, Awaitable, List
from datetime import datetime
from enum import Enum
import uuid

class TaskStatus(Enum):
    """Task lifecycle states"""
    PENDING = "pending"           # Waiting to start
    QUEUED = "queued"             # In queue, not yet started
    RUNNING = "running"           # Currently executing
    PAUSED = "paused"             # Temporarily stopped
    COMPLETED = "completed"       # Successfully finished
    FAILED = "failed"             # Execution failed
    CANCELLED = "cancelled"       # Manually cancelled
    TIMEOUT = "timeout"           # Exceeded time limit

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0   # System critical - run immediately
    HIGH = 1       # User requests, urgent tasks
    NORMAL = 2     # Regular tasks
    LOW = 3        # Background tasks, cleanup
    IDLE = 4       # Run only when system is idle

@dataclass
class Task:
    """
    Represents a task to be executed.
    
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
    function: Callable[..., Awaitable[Any]] = None
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
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"Task({self.name}, status={self.status.value}, priority={self.priority.name})"
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds"""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state"""
        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT
        }
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries
```

### **Task Result**
Standardized result format for task execution.

```python
from dataclasses import dataclass
from typing import Any, Optional

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
    metadata: dict[str, Any] = field(default_factory=dict)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       TaskQueue                             │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Priority Queues                                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │  │
│  │  │CRITICAL  │ │HIGH      │ │NORMAL    │ │LOW/IDLE │ │  │
│  │  │  Task1   │ │  Task3   │ │  Task5   │ │  Task7  │ │  │
│  │  │  Task2   │ │  Task4   │ │  Task6   │ │  Task8  │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └─────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Task Registry                                        │  │
│  │  task_id → Task                                       │  │
│  │  • task_123 → Task(name="analyze_code", status=...)  │  │
│  │  • task_456 → Task(name="run_tests", status=...)     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Worker Pool (AsyncIO)                                │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │  │
│  │  │Worker 1 │ │Worker 2 │ │Worker 3 │ │Worker N │    │  │
│  │  │RUNNING  │ │RUNNING  │ │IDLE     │ │IDLE     │    │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Dependency Graph                                     │  │
│  │  task_id → Set[task_id] (dependencies)               │  │
│  │  Ensures tasks execute in correct order              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
            ↓ add_task()              ↑ get_status()
┌──────────────────────┐    ┌──────────────────────┐
│  Task Producers      │    │  Task Consumers      │
│  • User Interface    │    │  • UI (status)       │
│  • Planner           │    │  • Memory (results)  │
│  • Self-Improvement  │    │  • Reporting         │
│  • Background Jobs   │    │  • Analytics         │
└──────────────────────┘    └──────────────────────┘
```

---

## 💻 Implementation

### **File Structure**
```
core/
├── task_queue.py         # TaskQueue class
├── task.py               # Task, TaskStatus, TaskPriority definitions
└── task_executor.py      # Task execution engine
```

### **Core TaskQueue Class**

```python
# core/task_queue.py

import asyncio
from typing import Dict, List, Optional, Callable, Awaitable, Any
from collections import defaultdict
from datetime import datetime
import logging

from core.task import Task, TaskStatus, TaskPriority, TaskResult
from core.event_bus import EventBus
from core.events import Event, EventType, EventPriority

class TaskQueue:
    """
    Priority-based asynchronous task queue.
    
    Features:
    - Priority scheduling with multiple queues
    - Concurrent execution with worker pool
    - Dependency management
    - Progress tracking
    - Error recovery and retry logic
    - Task cancellation
    - Resource limiting
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        max_workers: int = 5,
        max_queue_size: int = 1000
    ):
        self.logger = logging.getLogger("sophia.task_queue")
        self.event_bus = event_bus
        
        # Configuration
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # Priority queues
        self._queues: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue(maxsize=max_queue_size)
            for priority in TaskPriority
        }
        
        # Task registry (all tasks)
        self._tasks: Dict[str, Task] = {}
        
        # Dependency tracking
        self._dependencies: Dict[str, set] = defaultdict(set)  # task_id → dependencies
        self._dependents: Dict[str, set] = defaultdict(set)    # task_id → tasks waiting on it
        
        # Worker pool
        self._workers: List[asyncio.Task] = []
        self._running = False
        
        # Statistics
        self._stats = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "total_execution_time": 0.0
        }
        
        # Subscribe to events
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Subscribe to relevant events"""
        # When planner creates a task, add it to queue
        self.event_bus.subscribe(EventType.TASK_CREATED, self._handle_task_created)
        
        # System shutdown - stop all tasks
        self.event_bus.subscribe(EventType.SYSTEM_SHUTDOWN, self._handle_shutdown)
    
    async def _handle_task_created(self, event: Event):
        """Handle TASK_CREATED event from planner"""
        task_data = event.data
        
        # Create task from event data
        task = Task(
            task_id=task_data.get("task_id"),
            name=task_data.get("name", "unnamed"),
            description=task_data.get("description", ""),
            priority=TaskPriority[task_data.get("priority", "NORMAL")],
            metadata=task_data
        )
        
        # Add to queue
        await self.add_task(task)
    
    async def _handle_shutdown(self, event: Event):
        """Handle system shutdown - cancel all tasks"""
        await self.stop()
    
    async def add_task(
        self,
        task: Task,
        wait_for_completion: bool = False
    ) -> Optional[TaskResult]:
        """
        Add a task to the queue.
        
        Args:
            task: Task to add
            wait_for_completion: If True, wait for task to complete and return result
        
        Returns:
            TaskResult if wait_for_completion=True, else None
        """
        # Validate
        if len(self._tasks) >= self.max_queue_size:
            raise RuntimeError(f"Task queue full ({self.max_queue_size} tasks)")
        
        # Check dependencies exist
        for dep_id in task.dependencies:
            if dep_id not in self._tasks:
                raise ValueError(f"Dependency {dep_id} not found")
            self._dependents[dep_id].add(task.task_id)
            self._dependencies[task.task_id].add(dep_id)
        
        # Add to registry
        self._tasks[task.task_id] = task
        task.status = TaskStatus.QUEUED
        self._stats["tasks_created"] += 1
        
        # If no dependencies, add to queue
        if not task.dependencies:
            await self._enqueue_task(task)
        
        # Publish event
        self.event_bus.publish(Event(
            event_type=EventType.TASK_CREATED,
            source="task_queue",
            priority=EventPriority.NORMAL,
            data={
                "task_id": task.task_id,
                "name": task.name,
                "priority": task.priority.name
            }
        ))
        
        self.logger.info(f"Added task: {task}")
        
        # Wait for completion if requested
        if wait_for_completion:
            return await self._wait_for_task(task.task_id)
        
        return None
    
    async def _enqueue_task(self, task: Task):
        """Add task to appropriate priority queue"""
        await self._queues[task.priority].put(task)
    
    async def _wait_for_task(self, task_id: str, timeout: float = None) -> TaskResult:
        """Wait for a task to complete and return its result"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        start_time = datetime.now()
        while not task.is_terminal:
            await asyncio.sleep(0.1)
            
            # Check timeout
            if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")
        
        # Return result
        return TaskResult(
            success=task.status == TaskStatus.COMPLETED,
            data=task.result,
            error=str(task.error) if task.error else None,
            metadata={"duration": task.duration}
        )
    
    async def start(self):
        """Start the task queue and worker pool"""
        if self._running:
            self.logger.warning("TaskQueue already running")
            return
        
        self._running = True
        
        # Start workers
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self._workers.append(worker)
        
        self.logger.info(f"TaskQueue started with {self.max_workers} workers")
    
    async def stop(self):
        """Stop the task queue gracefully"""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel running tasks
        for task in self._tasks.values():
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
        
        # Cancel workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        self._workers.clear()
        self.logger.info("TaskQueue stopped")
    
    async def _worker_loop(self, worker_id: int):
        """Worker that processes tasks from queue"""
        self.logger.debug(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Get next task (check queues by priority)
                task = await self._get_next_task()
                
                if task is None:
                    # No tasks available - wait a bit
                    await asyncio.sleep(0.1)
                    continue
                
                # Execute task
                await self._execute_task(task, worker_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
        
        self.logger.debug(f"Worker {worker_id} stopped")
    
    async def _get_next_task(self) -> Optional[Task]:
        """Get next task from highest priority queue"""
        for priority in TaskPriority:
            try:
                task = self._queues[priority].get_nowait()
                return task
            except asyncio.QueueEmpty:
                continue
        return None
    
    async def _execute_task(self, task: Task, worker_id: int):
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            worker_id: ID of worker executing the task
        """
        # Update status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        # Publish start event
        self.event_bus.publish(Event(
            event_type=EventType.TASK_STARTED,
            source="task_queue",
            priority=EventPriority.NORMAL,
            data={
                "task_id": task.task_id,
                "name": task.name,
                "worker_id": worker_id
            }
        ))
        
        self.logger.info(f"Worker {worker_id} executing: {task}")
        
        try:
            # Execute with timeout
            if task.timeout:
                result = await asyncio.wait_for(
                    task.function(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                result = await task.function(*task.args, **task.kwargs)
            
            # Task succeeded
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now()
            task.progress = 100.0
            
            self._stats["tasks_completed"] += 1
            self._stats["total_execution_time"] += task.duration
            
            # Publish completion event
            self.event_bus.publish(Event(
                event_type=EventType.TASK_COMPLETED,
                source="task_queue",
                priority=EventPriority.NORMAL,
                data={
                    "task_id": task.task_id,
                    "name": task.name,
                    "duration": task.duration,
                    "result": result
                }
            ))
            
            self.logger.info(f"Task completed: {task.name} ({task.duration:.2f}s)")
            
            # Check if any dependent tasks can now run
            await self._check_dependents(task.task_id)
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.TIMEOUT
            task.completed_at = datetime.now()
            task.error = TimeoutError(f"Task exceeded timeout of {task.timeout}s")
            
            self._stats["tasks_failed"] += 1
            
            self.logger.error(f"Task timeout: {task.name}")
            
            # Retry if possible
            if task.can_retry:
                await self._retry_task(task)
            else:
                self._publish_task_failed(task)
        
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = e
            
            self._stats["tasks_failed"] += 1
            
            self.logger.error(f"Task failed: {task.name} - {e}", exc_info=True)
            
            # Retry if possible
            if task.can_retry:
                await self._retry_task(task)
            else:
                self._publish_task_failed(task)
    
    async def _retry_task(self, task: Task):
        """Retry a failed task"""
        task.retry_count += 1
        task.status = TaskStatus.QUEUED
        task.started_at = None
        task.completed_at = None
        task.progress = 0.0
        
        self.logger.info(f"Retrying task: {task.name} (attempt {task.retry_count}/{task.max_retries})")
        
        # Re-enqueue
        await self._enqueue_task(task)
    
    def _publish_task_failed(self, task: Task):
        """Publish task failure event"""
        self.event_bus.publish(Event(
            event_type=EventType.TASK_FAILED,
            source="task_queue",
            priority=EventPriority.HIGH,
            data={
                "task_id": task.task_id,
                "name": task.name,
                "error": str(task.error),
                "retry_count": task.retry_count
            }
        ))
    
    async def _check_dependents(self, completed_task_id: str):
        """Check if any tasks waiting on this one can now run"""
        if completed_task_id not in self._dependents:
            return
        
        for dependent_id in self._dependents[completed_task_id]:
            dependent = self._tasks[dependent_id]
            
            # Remove this dependency
            self._dependencies[dependent_id].discard(completed_task_id)
            
            # If no more dependencies, enqueue
            if not self._dependencies[dependent_id]:
                await self._enqueue_task(dependent)
                self.logger.debug(f"Enqueued dependent task: {dependent.name}")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self._tasks.get(task_id)
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with given status"""
        return [t for t in self._tasks.values() if t.status == status]
    
    def get_running_tasks(self) -> List[Task]:
        """Get all currently running tasks"""
        return self.get_tasks_by_status(TaskStatus.RUNNING)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: ID of task to cancel
        
        Returns:
            True if task was cancelled, False if not found or already terminal
        """
        task = self._tasks.get(task_id)
        if not task or task.is_terminal:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        self._stats["tasks_cancelled"] += 1
        
        self.event_bus.publish(Event(
            event_type=EventType.TASK_CANCELLED,
            source="task_queue",
            priority=EventPriority.NORMAL,
            data={"task_id": task_id, "name": task.name}
        ))
        
        self.logger.info(f"Cancelled task: {task.name}")
        return True
    
    def get_stats(self) -> dict:
        """Get queue statistics"""
        return {
            **self._stats,
            "queue_sizes": {
                priority.name: self._queues[priority].qsize()
                for priority in TaskPriority
            },
            "active_tasks": len(self.get_running_tasks()),
            "pending_tasks": len(self.get_tasks_by_status(TaskStatus.QUEUED)),
            "avg_execution_time": (
                self._stats["total_execution_time"] / self._stats["tasks_completed"]
                if self._stats["tasks_completed"] > 0 else 0
            )
        }
```

---

## 🔌 Integration Examples

### **Example 1: Simple Task**

```python
# Create a simple task
async def analyze_code(file_path: str) -> dict:
    # Analyze code
    return {"complexity": 5, "lines": 100}

task = Task(
    name="analyze_code",
    description="Analyze code complexity",
    function=analyze_code,
    args=("src/main.py",),
    priority=TaskPriority.NORMAL
)

# Add to queue
await task_queue.add_task(task)

# Or wait for result
result = await task_queue.add_task(task, wait_for_completion=True)
print(result.data)  # {"complexity": 5, "lines": 100}
```

### **Example 2: Task with Dependencies**

```python
# Task 1: Fetch data
task1 = Task(
    task_id="fetch_data",
    name="fetch_data",
    function=fetch_data_from_api,
    priority=TaskPriority.HIGH
)

# Task 2: Process data (depends on task1)
task2 = Task(
    task_id="process_data",
    name="process_data",
    function=process_data,
    dependencies=["fetch_data"],
    priority=TaskPriority.NORMAL
)

# Add both tasks
await task_queue.add_task(task1)
await task_queue.add_task(task2)  # Won't run until task1 completes
```

### **Example 3: Progress Tracking**

```python
async def long_running_task(context, task_id: str):
    """Task that reports progress"""
    for i in range(100):
        # Do work
        await asyncio.sleep(0.1)
        
        # Update progress
        task = context.task_queue.get_task(task_id)
        task.progress = i + 1
        
        # Publish progress event
        context.event_bus.publish(Event(
            event_type=EventType.TASK_PROGRESS,
            source="long_running_task",
            data={"task_id": task_id, "progress": task.progress}
        ))
    
    return "Done!"
```

---

## 🧪 Testing Strategy

### **Unit Tests**

```python
# tests/core/test_task_queue.py

import pytest
import asyncio
from core.task_queue import TaskQueue
from core.task import Task, TaskStatus, TaskPriority
from core.event_bus import EventBus

@pytest.mark.asyncio
async def test_add_and_execute_task():
    """Test basic task execution"""
    event_bus = EventBus()
    await event_bus.start()
    
    queue = TaskQueue(event_bus)
    await queue.start()
    
    # Create task
    async def simple_task():
        return "success"
    
    task = Task(
        name="simple",
        function=simple_task,
        priority=TaskPriority.NORMAL
    )
    
    # Execute and wait
    result = await queue.add_task(task, wait_for_completion=True)
    
    assert result.success
    assert result.data == "success"
    assert task.status == TaskStatus.COMPLETED
    
    await queue.stop()
    await event_bus.stop()

@pytest.mark.asyncio
async def test_task_dependencies():
    """Test dependency management"""
    event_bus = EventBus()
    await event_bus.start()
    
    queue = TaskQueue(event_bus)
    await queue.start()
    
    results = []
    
    async def task1():
        results.append(1)
        return 1
    
    async def task2():
        results.append(2)
        return 2
    
    t1 = Task(task_id="t1", name="t1", function=task1)
    t2 = Task(task_id="t2", name="t2", function=task2, dependencies=["t1"])
    
    await queue.add_task(t1)
    await queue.add_task(t2)
    
    # Wait for both
    await asyncio.sleep(0.5)
    
    # Task 1 should run before task 2
    assert results == [1, 2]
    
    await queue.stop()
    await event_bus.stop()

@pytest.mark.asyncio
async def test_task_retry():
    """Test retry on failure"""
    event_bus = EventBus()
    await event_bus.start()
    
    queue = TaskQueue(event_bus)
    await queue.start()
    
    attempts = []
    
    async def failing_task():
        attempts.append(1)
        if len(attempts) < 3:
            raise ValueError("Fail")
        return "success"
    
    task = Task(
        name="failing",
        function=failing_task,
        max_retries=3
    )
    
    result = await queue.add_task(task, wait_for_completion=True)
    
    assert len(attempts) == 3
    assert result.success
    
    await queue.stop()
    await event_bus.stop()
```

---

## 📈 Performance Considerations

### **Throughput**
- Target: 100+ concurrent tasks
- Worker pool size configurable (default: 5)
- Queue size limit prevents memory issues

### **Latency**
- Critical tasks: <100ms to start
- Normal tasks: <1s to start
- Progress updates: every 1s

### **Resource Management**
- Max concurrent tasks limited by worker pool
- Memory usage monitored
- Long-running tasks can be paused/resumed

---

## ✅ Success Criteria

- [ ] Can execute 100+ tasks concurrently
- [ ] Priority scheduling works correctly
- [ ] Dependencies enforced properly
- [ ] Progress tracking accurate
- [ ] Failed tasks retry automatically
- [ ] Task cancellation works
- [ ] Integration with EventBus successful
- [ ] Unit tests achieve >90% coverage

---

## 🔗 Related Documents

- `EVENT_SYSTEM.md` - Event-driven communication
- `LOOP_MIGRATION.md` - Migration from blocking loop
- `GUARDRAILS.md` - Safety constraints
- `docs/en/04_advanced_features.md` - Autonomous task management

---

**Status:** Ready for Implementation ✅  
**Next Steps:** Implement `core/task_queue.py` and `core/task.py`
