"""
Task Queue implementation for Sophia's asynchronous task management.

This module provides a priority-based task queue that enables concurrent
execution of tasks with dependency management, error recovery, and progress tracking.
"""

import asyncio
from typing import Dict, List, Optional, TYPE_CHECKING
from collections import defaultdict
import logging

from core.task import Task, TaskStatus, TaskPriority
from core.events import Event, EventType, EventPriority

if TYPE_CHECKING:
    from core.event_bus import EventBus


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

    def __init__(self, event_bus: "EventBus", max_workers: int = 5, max_queue_size: int = 1000):
        self.logger = logging.getLogger("sophia.task_queue")
        self.event_bus = event_bus

        # Configuration
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size

        # Priority queues - one for each priority level
        self._queues: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue(maxsize=max_queue_size) for priority in TaskPriority
        }

        # Task registry (all tasks by ID)
        self._tasks: Dict[str, Task] = {}

        # Dependency tracking
        self._dependencies: Dict[str, set] = defaultdict(set)  # task_id → dependencies
        self._dependents: Dict[str, set] = defaultdict(set)  # task_id → tasks waiting on it

        # Worker pool
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Statistics
        self._stats = {
            "tasks_created": 0,
            "tasks_queued": 0,
            "tasks_started": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "tasks_timeout": 0,
            "total_execution_time": 0.0,
        }

    async def start(self) -> None:
        """Start the task queue and worker pool."""
        if self._running:
            self.logger.warning("TaskQueue already running")
            return

        self._running = True
        self._shutdown_event.clear()

        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(
                self._worker_loop(worker_id=i), name=f"TaskQueue-Worker-{i}"
            )
            self._workers.append(worker)

        self.logger.info(
            f"TaskQueue started with {self.max_workers} workers",
            extra={"plugin_name": "TaskQueue"},
        )

        # Publish event
        self.event_bus.publish(
            Event(
                event_type=EventType.SYSTEM_READY,
                source="task_queue",
                priority=EventPriority.NORMAL,
                data={"workers": self.max_workers},
            )
        )

    async def stop(self) -> None:
        """Stop the task queue and gracefully shutdown workers."""
        if not self._running:
            return

        self.logger.info("Stopping TaskQueue...", extra={"plugin_name": "TaskQueue"})
        self._running = False
        self._shutdown_event.set()

        # Cancel all workers
        for worker in self._workers:
            worker.cancel()

        # Wait for workers to finish
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)

        self._workers.clear()

        self.logger.info("TaskQueue stopped", extra={"plugin_name": "TaskQueue"})

    async def add_task(self, task: Task, dependencies: Optional[List[str]] = None) -> str:
        """
        Add a task to the queue.

        Args:
            task: Task to add
            dependencies: Optional list of task IDs this task depends on

        Returns:
            task_id: The ID of the added task
        """
        # Register task
        self._tasks[task.task_id] = task
        self._stats["tasks_created"] += 1

        # Handle dependencies
        if dependencies:
            self._dependencies[task.task_id] = set(dependencies)
            for dep_id in dependencies:
                self._dependents[dep_id].add(task.task_id)

            self.logger.debug(
                f"Task {task.name} has {len(dependencies)} dependencies",
                extra={"plugin_name": "TaskQueue"},
            )

        # Check if dependencies are satisfied
        if self._can_execute(task):
            await self._enqueue_task(task)
        else:
            task.status = TaskStatus.PENDING
            self.logger.debug(
                f"Task {task.name} waiting for dependencies", extra={"plugin_name": "TaskQueue"}
            )

        # Publish event
        self.event_bus.publish(
            Event(
                event_type=EventType.TASK_CREATED,
                source="task_queue",
                priority=EventPriority.NORMAL,
                data={
                    "task_id": task.task_id,
                    "name": task.name,
                    "priority": task.priority.name,
                    "has_dependencies": bool(dependencies),
                },
            )
        )

        return task.task_id

    def _can_execute(self, task: Task) -> bool:
        """Check if task's dependencies are satisfied."""
        if task.task_id not in self._dependencies:
            return True

        deps = self._dependencies[task.task_id]
        for dep_id in deps:
            if dep_id not in self._tasks:
                return False
            dep_task = self._tasks[dep_id]
            if not dep_task.is_terminal:
                return False
            if dep_task.status != TaskStatus.COMPLETED:
                # Dependency failed - mark this task as failed too
                task.mark_failed(Exception(f"Dependency {dep_id} failed"))
                return False

        return True

    async def _enqueue_task(self, task: Task) -> None:
        """Add task to appropriate priority queue."""
        task.status = TaskStatus.QUEUED
        self._stats["tasks_queued"] += 1

        queue = self._queues[task.priority]
        await queue.put(task)

        self.logger.debug(
            f"Task {task.name} queued with priority {task.priority.name}",
            extra={"plugin_name": "TaskQueue"},
        )

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker loop that processes tasks from priority queues."""
        self.logger.debug(f"Worker {worker_id} started", extra={"plugin_name": "TaskQueue"})

        while self._running:
            try:
                # Try to get task from highest priority queue first
                task = await self._get_next_task()

                if task is None:
                    # No tasks available, wait a bit
                    await asyncio.sleep(0.1)
                    continue

                # Execute task
                await self._execute_task(task, worker_id)

            except asyncio.CancelledError:
                self.logger.debug(
                    f"Worker {worker_id} cancelled", extra={"plugin_name": "TaskQueue"}
                )
                break
            except Exception as e:
                self.logger.error(
                    f"Worker {worker_id} error: {e}",
                    exc_info=True,
                    extra={"plugin_name": "TaskQueue"},
                )

        self.logger.debug(f"Worker {worker_id} stopped", extra={"plugin_name": "TaskQueue"})

    async def _get_next_task(self) -> Optional[Task]:
        """Get next task from highest priority queue."""
        # Check queues in priority order (CRITICAL first)
        for priority in sorted(TaskPriority, key=lambda p: p.value):
            queue = self._queues[priority]

            if not queue.empty():
                try:
                    task = queue.get_nowait()
                    return task
                except asyncio.QueueEmpty:
                    continue

        return None

    async def _execute_task(self, task: Task, worker_id: int) -> None:
        """Execute a single task."""
        self.logger.info(
            f"Worker {worker_id} executing task: {task.name}", extra={"plugin_name": "TaskQueue"}
        )

        task.mark_started()
        self._stats["tasks_started"] += 1

        # Publish event
        self.event_bus.publish(
            Event(
                event_type=EventType.TASK_STARTED,
                source="task_queue",
                priority=EventPriority.NORMAL,
                data={"task_id": task.task_id, "name": task.name, "worker_id": worker_id},
            )
        )

        try:
            # Execute with timeout if specified
            if task.timeout:
                result = await asyncio.wait_for(
                    task.function(*task.args, **task.kwargs), timeout=task.timeout
                )
            else:
                result = await task.function(*task.args, **task.kwargs)

            # Mark success
            task.mark_completed(result)
            self._stats["tasks_completed"] += 1

            if task.duration:
                self._stats["total_execution_time"] += task.duration

            self.logger.info(
                f"Task {task.name} completed in {task.duration:.2f}s",
                extra={"plugin_name": "TaskQueue"},
            )

            # Publish event
            self.event_bus.publish(
                Event(
                    event_type=EventType.TASK_COMPLETED,
                    source="task_queue",
                    priority=EventPriority.NORMAL,
                    data={
                        "task_id": task.task_id,
                        "name": task.name,
                        "duration": task.duration,
                        "success": True,
                    },
                )
            )

        except asyncio.TimeoutError:
            task.mark_timeout()
            self._stats["tasks_timeout"] += 1

            self.logger.warning(
                f"Task {task.name} timed out after {task.timeout}s",
                extra={"plugin_name": "TaskQueue"},
            )

            # Publish event
            self.event_bus.publish(
                Event(
                    event_type=EventType.TASK_FAILED,
                    source="task_queue",
                    priority=EventPriority.HIGH,
                    data={
                        "task_id": task.task_id,
                        "name": task.name,
                        "error": "Timeout",
                        "can_retry": task.can_retry,
                    },
                )
            )

            # Retry if possible
            if task.can_retry:
                await self._retry_task(task)

        except Exception as e:
            task.mark_failed(e)
            self._stats["tasks_failed"] += 1

            self.logger.error(
                f"Task {task.name} failed: {e}", exc_info=True, extra={"plugin_name": "TaskQueue"}
            )

            # Publish event
            self.event_bus.publish(
                Event(
                    event_type=EventType.TASK_FAILED,
                    source="task_queue",
                    priority=EventPriority.HIGH,
                    data={
                        "task_id": task.task_id,
                        "name": task.name,
                        "error": str(e),
                        "can_retry": task.can_retry,
                    },
                )
            )

            # Retry if possible
            if task.can_retry:
                await self._retry_task(task)

        finally:
            # Check and enqueue dependent tasks
            await self._check_dependents(task)

    async def _retry_task(self, task: Task) -> None:
        """Retry a failed task."""
        self.logger.info(
            f"Retrying task {task.name} (attempt {task.retry_count + 1}/{task.max_retries})",
            extra={"plugin_name": "TaskQueue"},
        )

        # Reset task state
        task.status = TaskStatus.QUEUED
        task.started_at = None
        task.completed_at = None
        task.error = None

        # Re-enqueue
        await self._enqueue_task(task)

    async def _check_dependents(self, completed_task: Task) -> None:
        """Check if any tasks were waiting for this task to complete."""
        task_id = completed_task.task_id

        if task_id not in self._dependents:
            return

        dependent_ids = self._dependents[task_id].copy()

        for dep_id in dependent_ids:
            if dep_id not in self._tasks:
                continue

            dependent_task = self._tasks[dep_id]

            # Check if all dependencies are now satisfied
            if self._can_execute(dependent_task):
                await self._enqueue_task(dependent_task)

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.

        Returns:
            True if task was cancelled, False if not found or already terminal
        """
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]

        if task.is_terminal:
            return False

        task.mark_cancelled()
        self._stats["tasks_cancelled"] += 1

        self.logger.info(f"Task {task.name} cancelled", extra={"plugin_name": "TaskQueue"})

        # Publish event
        self.event_bus.publish(
            Event(
                event_type=EventType.TASK_CANCELLED,
                source="task_queue",
                priority=EventPriority.NORMAL,
                data={"task_id": task_id, "name": task.name},
            )
        )

        return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def get_stats(self) -> dict:
        """Get queue statistics."""
        queue_sizes = {priority.name: self._queues[priority].qsize() for priority in TaskPriority}

        return {
            **self._stats,
            "queue_sizes": queue_sizes,
            "total_tasks": len(self._tasks),
            "workers_active": self.max_workers if self._running else 0,
        }

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self._tasks.values())

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with given status."""
        return [task for task in self._tasks.values() if task.status == status]
