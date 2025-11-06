"""
Event-Driven Consciousness Loop - Phase 1 Implementation

This module contains the event-driven version of the consciousness loop,
designed to run concurrently with the legacy blocking loop during migration.

Design:
- Non-blocking input handling
- Event-based task execution
- Autonomous background operations
- Backwards compatible with existing plugins
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from core.context import SharedContext
from core.events import Event, EventType, EventPriority
from core.event_bus import EventBus
from core.task_queue import TaskQueue
from plugins.base_plugin import PluginType

logger = logging.getLogger(__name__)


class EventDrivenLoop:
    """
    Event-driven consciousness loop for Sophia.

    This is the Phase 1 implementation that replaces the blocking
    consciousness loop with an event-driven architecture.
    """

    def __init__(
        self,
        plugin_manager,
        all_plugins_map: Dict[str, Any],
        event_bus: EventBus,
        task_queue: TaskQueue,
    ):
        """
        Initialize event-driven loop.

        Args:
            plugin_manager: Plugin manager instance
            all_plugins_map: Map of plugin names to plugin instances
            event_bus: Event bus instance
            task_queue: Task queue instance
        """
        self.plugin_manager = plugin_manager
        self.all_plugins_map = all_plugins_map
        self.event_bus = event_bus
        self.task_queue = task_queue
        self.is_running = False
        
        # AMI 1.0: Proactive heartbeat
        self._heartbeat_task = None
        self._last_heartbeat = 0

        # Subscribe to events
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Subscribe to relevant events."""
        # Subscribe to USER_INPUT events for processing
        self.event_bus.subscribe(EventType.USER_INPUT, self._handle_user_input)

        # Subscribe to TASK_COMPLETED events for response handling
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._handle_task_completed)

        # Subscribe to SYSTEM_ERROR events for error handling
        self.event_bus.subscribe(EventType.SYSTEM_ERROR, self._handle_system_error)

        logger.info(
            "Event-driven loop handlers registered", extra={"plugin_name": "EventDrivenLoop"}
        )

    async def _handle_user_input(self, event: Event):
        """
        Handle USER_INPUT events.

        This triggers the planning and execution pipeline.
        """
        user_input = event.data.get("input")
        session_id = event.data.get("session_id")

        if not user_input:
            return

        logger.info(
            f"Processing user input via event: '{user_input}'",
            extra={"plugin_name": "EventDrivenLoop"},
        )

        # TODO: Trigger planner via event
        # For now, log that we received the event
        logger.debug(
            f"USER_INPUT event received: {user_input}", extra={"plugin_name": "EventDrivenLoop"}
        )

    async def _handle_task_completed(self, event: Event):
        """
        Handle TASK_COMPLETED events.

        This updates UI with task results.
        """
        task_name = event.data.get("task_name", "unknown")
        result = event.data.get("result")

        logger.info(f"Task completed: {task_name}", extra={"plugin_name": "EventDrivenLoop"})

        # TODO: Update UI with result
        # TODO: Trigger memory storage

    async def _handle_system_error(self, event: Event):
        """
        Handle SYSTEM_ERROR events.

        This logs and potentially recovers from errors.
        """
        error = event.data.get("error")

        logger.error(f"System error event: {error}", extra={"plugin_name": "EventDrivenLoop"})

    async def run(self, context: SharedContext, single_run_input: Optional[str] = None):
        """
        Run the event-driven consciousness loop.

        Args:
            context: Shared context for the session
            single_run_input: Optional input for single-run mode
        """
        self.is_running = True

        logger.info(
            "Starting event-driven consciousness loop", extra={"plugin_name": "EventDrivenLoop"}
        )
        
        # AMI 1.0: Start proactive heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # Handle single-run mode
        if single_run_input:
            # Publish USER_INPUT event
            self.event_bus.publish(
                Event(
                    event_type=EventType.USER_INPUT,
                    source="event_driven_loop",
                    priority=EventPriority.HIGH,
                    data={"input": single_run_input, "session_id": context.session_id},
                    metadata={"timestamp": datetime.now().isoformat()},
                )
            )

            # Wait for processing
            await asyncio.sleep(1.0)

            self.is_running = False
            return

        # Main event-driven loop
        while self.is_running:
            try:
                # 1. Check for user input (non-blocking)
                await self._check_input(context)

                # 2. Check for autonomous tasks
                await self._check_autonomous_tasks(context)

                # 3. Small sleep to prevent CPU spinning
                await asyncio.sleep(0.01)

            except asyncio.CancelledError:
                logger.info(
                    "Event-driven loop cancelled", extra={"plugin_name": "EventDrivenLoop"}
                )
                self.is_running = False
                break

            except Exception as e:
                logger.error(
                    f"Error in event-driven loop: {e}",
                    exc_info=True,
                    extra={"plugin_name": "EventDrivenLoop"},
                )

                # Publish error event
                self.event_bus.publish(
                    Event(
                        event_type=EventType.SYSTEM_ERROR,
                        source="event_driven_loop",
                        priority=EventPriority.CRITICAL,
                        data={"error": str(e)},
                    )
                )

                await asyncio.sleep(1.0)

        logger.info(
            "Event-driven consciousness loop finished", extra={"plugin_name": "EventDrivenLoop"}
        )
    
    async def _heartbeat_loop(self):
        """Emit PROACTIVE_HEARTBEAT event every 60 seconds."""
        import time
        logger.info("💓 Heartbeat loop started (60s intervals)", extra={"plugin_name": "EventDrivenLoop"})
        
        while self.is_running:
            try:
                # Emit heartbeat event FIRST (don't wait 60s before first beat)
                self.event_bus.publish(
                    Event(
                        event_type=EventType.PROACTIVE_HEARTBEAT,
                        source="event_driven_loop",
                        priority=EventPriority.LOW,
                        data={"timestamp": datetime.now().isoformat()},
                    )
                )
                
                self._last_heartbeat = time.time()
                logger.info("💓 PROACTIVE_HEARTBEAT emitted", extra={"plugin_name": "EventDrivenLoop"})
                
                # Sleep 60s until next beat
                await asyncio.sleep(60)
                
                if not self.is_running:
                    break
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}", extra={"plugin_name": "EventDrivenLoop"})

    async def _check_input(self, context: SharedContext):
        """
        Check for user input (non-blocking).

        Calls interface plugins in non-blocking mode.
        """
        interface_plugins = self.plugin_manager.get_plugins_by_type(PluginType.INTERFACE)

        if not interface_plugins:
            return

        # Execute interface plugins (they handle event emission internally)
        for plugin in interface_plugins:
            try:
                await plugin.execute(context)
            except Exception as e:
                logger.error(
                    f"Error in interface plugin {plugin.name}: {e}",
                    exc_info=True,
                    extra={"plugin_name": "EventDrivenLoop"},
                )

    async def _check_autonomous_tasks(self, context: SharedContext):
        """
        Check for autonomous tasks that should run.

        This is where Sophia proactively looks for work to do:
        - Check roberts-notes.txt for new ideas
        - Run scheduled maintenance tasks
        - Consolidate memories
        - Self-improvement workflows (BenchmarkRunner)
        """
        # Run BenchmarkRunner plugin periodically (every N seconds) in a background task
        if not hasattr(self, "_last_benchmark_run"):
            self._last_benchmark_run = 0
        if not hasattr(self, "_benchmark_task"):
            self._benchmark_task = None
        import time
        BENCHMARK_INTERVAL = 300  # seconds (5 minutes)
        now = time.time()
        if now - self._last_benchmark_run > BENCHMARK_INTERVAL:
            benchmark_runner = self.all_plugins_map.get("benchmark_runner")
            if benchmark_runner and hasattr(benchmark_runner, "execute"):
                try:
                    self._last_benchmark_run = now
                    # Pokud předchozí task ještě běží, nečekej na něj
                    if self._benchmark_task is None or self._benchmark_task.done():
                        self._benchmark_task = asyncio.create_task(benchmark_runner.execute(context))
                except Exception as e:
                    logger.error(f"BenchmarkRunner error: {e}", extra={"plugin_name": "EventDrivenLoop"})

    def stop(self):
        """Stop the event-driven loop."""
        self.is_running = False
        logger.info("Event-driven loop stop requested", extra={"plugin_name": "EventDrivenLoop"})
