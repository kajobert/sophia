"""
Event Bus - Central pub/sub messaging system for Sophia's event-driven architecture.

The EventBus enables decoupled communication between components through an
asynchronous publish/subscribe pattern with priority-based event processing.
"""

import asyncio
from typing import Dict, List, Callable, Optional, Union, Awaitable
from collections import defaultdict
import logging

from core.events import Event, EventType, EventPriority


# Type alias for event handlers (sync or async)
EventHandler = Callable[[Event], Union[None, Awaitable[None]]]


class EventBus:
    """
    Central event bus for pub/sub messaging.

    Features:
    - Priority-based event queuing
    - Async event processing
    - Subscribe/unsubscribe to event types
    - Event history for debugging
    - Error handling with dead letter queue

    Example:
        >>> bus = EventBus()
        >>> await bus.start()
        >>>
        >>> def handler(event: Event):
        ...     print(f"Received: {event.event_type}")
        >>>
        >>> bus.subscribe(EventType.USER_INPUT, handler)
        >>> bus.publish(Event(event_type=EventType.USER_INPUT, source="terminal"))
        >>>
        >>> await bus.stop()
    """

    def __init__(self, max_history: int = 1000, max_retries: int = 3):
        """
        Initialize the event bus.

        Args:
            max_history: Maximum number of events to keep in history
            max_retries: Maximum retry attempts for failed event handlers
        """
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
            "handlers_executed": 0,
        }

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe a handler to an event type.

        Args:
            event_type: Type of event to listen for
            handler: Callable to handle the event (sync or async)

        Example:
            >>> def my_handler(event: Event):
            ...     print(f"Got event: {event.event_type}")
            >>>
            >>> bus.subscribe(EventType.TASK_COMPLETED, my_handler)
        """
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            self.logger.debug(
                f"Subscribed {handler.__name__} to {event_type.value}",
                extra={"plugin_name": "EventBus"},
            )

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: Type of event to stop listening for
            handler: Handler to remove
        """
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            self.logger.debug(
                f"Unsubscribed {handler.__name__} from {event_type.value}",
                extra={"plugin_name": "EventBus"},
            )

    def publish(self, event: Event) -> None:
        """
        Publish an event to the bus.

        The event will be queued for processing based on its priority.

        Args:
            event: Event to publish

        Example:
            >>> event = Event(
            ...     event_type=EventType.USER_INPUT,
            ...     source="terminal",
            ...     priority=EventPriority.HIGH,
            ...     data={"input": "Hello, Sophia!"}
            ... )
            >>> bus.publish(event)
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
            f"[priority={event.priority.name}]",
            extra={"plugin_name": "EventBus"},
        )

    async def start(self) -> None:
        """
        Start the event dispatcher.

        This starts a background task that processes events from the queues.
        """
        if self._running:
            self.logger.warning("EventBus already running", extra={"plugin_name": "EventBus"})
            return

        self._running = True
        self._dispatcher_task = asyncio.create_task(self._dispatch_loop())
        self.logger.info("EventBus started", extra={"plugin_name": "EventBus"})

    async def stop(self) -> None:
        """
        Stop the event dispatcher gracefully.

        Waits for current events to finish processing before stopping.
        """
        if not self._running:
            return

        self._running = False
        if self._dispatcher_task:
            self._dispatcher_task.cancel()
            try:
                await self._dispatcher_task
            except asyncio.CancelledError:
                pass

        self.logger.info("EventBus stopped", extra={"plugin_name": "EventBus"})

    async def _dispatch_loop(self) -> None:
        """
        Main event processing loop.

        Continuously checks queues in priority order and dispatches events
        to their subscribers.
        """
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
                self.logger.error(
                    f"Error in dispatch loop: {e}",
                    exc_info=True,
                    extra={"plugin_name": "EventBus"},
                )

    async def _dispatch_event(self, event: Event) -> None:
        """
        Dispatch event to all subscribers.

        Args:
            event: Event to dispatch
        """
        handlers = self._subscribers.get(event.event_type, [])

        if not handlers:
            self.logger.debug(
                f"No handlers for {event.event_type.value}", extra={"plugin_name": "EventBus"}
            )
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
                    exc_info=result,
                    extra={"plugin_name": "EventBus"},
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
        """
        Get event bus statistics.

        Returns:
            Dictionary containing:
            - events_published: Total events published
            - events_processed: Total events processed
            - events_failed: Total failed event handlers
            - handlers_executed: Total handler executions
            - active_subscribers: Number of active subscriptions
            - queue_sizes: Current queue sizes by priority
            - dead_letter_size: Number of events in dead letter queue
        """
        return {
            **self._stats,
            "active_subscribers": sum(len(handlers) for handlers in self._subscribers.values()),
            "queue_sizes": {
                priority.name: self._queues[priority].qsize() for priority in EventPriority
            },
            "dead_letter_size": len(self._dead_letter_queue),
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

    def clear_dead_letter_queue(self) -> List[tuple[Event, Exception]]:
        """
        Clear and return the dead letter queue.

        Returns:
            List of (event, exception) tuples that failed
        """
        dead_letters = self._dead_letter_queue.copy()
        self._dead_letter_queue.clear()
        return dead_letters
