"""Unit tests for TaskQueue."""

import pytest
import asyncio
from datetime import datetime

from core.task import Task, TaskStatus, TaskPriority
from core.task_queue import TaskQueue
from core.event_bus import EventBus


@pytest.fixture
async def event_bus():
    """Create EventBus for testing."""
    bus = EventBus()
    await bus.start()
    yield bus
    await bus.stop()


@pytest.fixture
async def task_queue(event_bus):
    """Create TaskQueue for testing."""
    queue = TaskQueue(event_bus=event_bus, max_workers=2)
    await queue.start()
    yield queue
    await queue.stop()


# Dummy async functions for testing
async def simple_task():
    """Simple task that returns immediately."""
    await asyncio.sleep(0.01)
    return "success"


async def failing_task():
    """Task that always fails."""
    await asyncio.sleep(0.01)
    raise ValueError("Task failed")


async def slow_task():
    """Task that takes time."""
    await asyncio.sleep(1.0)
    return "slow_success"


async def task_with_args(x, y):
    """Task that uses arguments."""
    await asyncio.sleep(0.01)
    return x + y


# Tests
@pytest.mark.asyncio
async def test_task_queue_creation(task_queue):
    """Test TaskQueue initialization."""
    assert task_queue._running is True
    assert len(task_queue._workers) == 2
    assert task_queue.max_workers == 2


@pytest.mark.asyncio
async def test_add_simple_task(task_queue):
    """Test adding and executing a simple task."""
    task = Task(name="test_task", function=simple_task, priority=TaskPriority.HIGH)

    task_id = await task_queue.add_task(task)
    assert task_id == task.task_id
    assert task_queue.get_task(task_id) is task

    # Wait for execution
    await asyncio.sleep(0.2)

    assert task.status == TaskStatus.COMPLETED
    assert task.result == "success"
    assert task.duration is not None


@pytest.mark.asyncio
async def test_task_priority_ordering(task_queue):
    """Test that higher priority tasks execute first."""
    results = []

    async def record_task(name):
        results.append(name)
        await asyncio.sleep(0.01)

    # Add tasks in reverse priority order
    low_task = Task(name="low", function=record_task, args=("low",), priority=TaskPriority.LOW)
    normal_task = Task(
        name="normal", function=record_task, args=("normal",), priority=TaskPriority.NORMAL
    )
    high_task = Task(name="high", function=record_task, args=("high",), priority=TaskPriority.HIGH)
    critical_task = Task(
        name="critical", function=record_task, args=("critical",), priority=TaskPriority.CRITICAL
    )

    await task_queue.add_task(low_task)
    await task_queue.add_task(normal_task)
    await task_queue.add_task(high_task)
    await task_queue.add_task(critical_task)

    await asyncio.sleep(0.5)

    # Critical should execute first
    assert results[0] == "critical"
    assert results[1] == "high"


@pytest.mark.asyncio
async def test_task_with_arguments(task_queue):
    """Test task execution with arguments."""
    task = Task(
        name="add_task", function=task_with_args, args=(5, 3), priority=TaskPriority.NORMAL
    )

    await task_queue.add_task(task)
    await asyncio.sleep(0.2)

    assert task.status == TaskStatus.COMPLETED
    assert task.result == 8


@pytest.mark.asyncio
async def test_failing_task(task_queue):
    """Test task failure and retry."""
    task = Task(name="failing", function=failing_task, max_retries=2, priority=TaskPriority.NORMAL)

    await task_queue.add_task(task)
    await asyncio.sleep(0.5)

    assert task.status == TaskStatus.FAILED
    assert task.retry_count == 2  # Should have retried twice
    assert task.error is not None


@pytest.mark.asyncio
async def test_task_timeout(task_queue):
    """Test task timeout."""
    task = Task(
        name="slow", function=slow_task, timeout=0.1, max_retries=0, priority=TaskPriority.NORMAL
    )

    await task_queue.add_task(task)
    await asyncio.sleep(0.3)

    assert task.status == TaskStatus.TIMEOUT
    assert isinstance(task.error, TimeoutError)


@pytest.mark.asyncio
async def test_task_cancellation(task_queue):
    """Test task cancellation."""
    task = Task(name="to_cancel", function=slow_task, priority=TaskPriority.LOW)

    task_id = await task_queue.add_task(task)
    await asyncio.sleep(0.05)

    success = await task_queue.cancel_task(task_id)
    assert success is True
    assert task.status == TaskStatus.CANCELLED


@pytest.mark.asyncio
async def test_task_dependencies(task_queue):
    """Test task dependency execution order."""
    execution_order = []

    async def dep_task(name):
        execution_order.append(name)
        await asyncio.sleep(0.1)

    # Create tasks with dependencies
    task1 = Task(name="task1", function=dep_task, args=("task1",))
    task2 = Task(name="task2", function=dep_task, args=("task2",))
    task3 = Task(name="task3", function=dep_task, args=("task3",))

    # Add tasks: task3 depends on task2, task2 depends on task1
    id1 = await task_queue.add_task(task1)
    id2 = await task_queue.add_task(task2, dependencies=[id1])
    id3 = await task_queue.add_task(task3, dependencies=[id2])

    await asyncio.sleep(0.5)

    # Should execute in order
    assert execution_order == ["task1", "task2", "task3"]
    assert task1.status == TaskStatus.COMPLETED
    assert task2.status == TaskStatus.COMPLETED
    assert task3.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_queue_statistics(task_queue):
    """Test queue statistics tracking."""
    task1 = Task(name="t1", function=simple_task)
    task2 = Task(name="t2", function=simple_task)

    await task_queue.add_task(task1)
    await task_queue.add_task(task2)
    await asyncio.sleep(0.3)

    stats = task_queue.get_stats()

    assert stats["tasks_created"] == 2
    assert stats["tasks_completed"] == 2
    assert stats["workers_active"] == 2


@pytest.mark.asyncio
async def test_get_tasks_by_status(task_queue):
    """Test filtering tasks by status."""
    task1 = Task(name="t1", function=simple_task)
    task2 = Task(name="t2", function=failing_task, max_retries=0)

    await task_queue.add_task(task1)
    await task_queue.add_task(task2)
    await asyncio.sleep(0.3)

    completed = task_queue.get_tasks_by_status(TaskStatus.COMPLETED)
    failed = task_queue.get_tasks_by_status(TaskStatus.FAILED)

    assert len(completed) == 1
    assert len(failed) == 1


@pytest.mark.asyncio
async def test_concurrent_execution(task_queue):
    """Test that multiple tasks run concurrently."""
    start_times = {}

    async def concurrent_task(name):
        start_times[name] = datetime.now()
        await asyncio.sleep(0.2)

    task1 = Task(name="t1", function=concurrent_task, args=("t1",))
    task2 = Task(name="t2", function=concurrent_task, args=("t2",))

    await task_queue.add_task(task1)
    await task_queue.add_task(task2)
    await asyncio.sleep(0.5)

    # Both should have started around the same time
    assert "t1" in start_times
    assert "t2" in start_times
    time_diff = abs((start_times["t1"] - start_times["t2"]).total_seconds())
    assert time_diff < 0.1  # Started within 100ms of each other


@pytest.mark.asyncio
async def test_task_properties(task_queue):
    """Test Task property methods."""
    task = Task(name="test", function=simple_task)

    # Test is_terminal
    assert task.is_terminal is False
    task.status = TaskStatus.COMPLETED
    assert task.is_terminal is True

    # Test can_retry
    task.status = TaskStatus.FAILED
    task.retry_count = 0
    task.max_retries = 3
    assert task.can_retry is True

    task.retry_count = 3
    assert task.can_retry is False


@pytest.mark.asyncio
async def test_graceful_shutdown(event_bus):
    """Test graceful shutdown of TaskQueue."""
    queue = TaskQueue(event_bus=event_bus, max_workers=2)
    await queue.start()

    # Add some tasks
    for i in range(5):
        task = Task(name=f"t{i}", function=simple_task)
        await queue.add_task(task)

    # Shutdown
    await queue.stop()

    assert queue._running is False
    assert len(queue._workers) == 0
