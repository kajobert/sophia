import asyncio
import os
import time
from typing import Optional

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.event_bus import EventBus
from core.events import Event, EventType, EventPriority


class CoreProactiveAgent(BasePlugin):
    """Proactive agent plugin that emits periodic heartbeats and detects new ideas.

    Responsibilities:
    - Periodically publish a HEARTBEAT event (EventType.CUSTOM with subtype)
    - Watch a configured file (e.g., `docs/roberts-notes.txt`) for changes and
      publish NEW_IDEA_DETECTED events with the file contents when updates occur

    This plugin runs background tasks after the EventBus is injected via
    `set_event_bus`.
    """

    def __init__(self) -> None:
        self._event_bus: Optional[EventBus] = None
        self.heartbeat_interval = 60
        self.idea_file = "docs/roberts-notes.txt"
        self.poll_interval = 10
        self._tasks: list[asyncio.Task] = []

    @property
    def name(self) -> str:
        return "core_proactive_agent"

    @property
    def plugin_type(self) -> PluginType:
        # This is a cognitive component that runs proactively
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "0.1.0"

    def setup(self, config: dict) -> None:
        """Initialize the proactive agent with optional configuration.

        Config keys:
        - heartbeat_interval: seconds between heartbeats
        - idea_file: path to watch for new ideas
        - poll_interval: file watch polling interval in seconds
        """
        self.heartbeat_interval = config.get("heartbeat_interval", self.heartbeat_interval)
        self.idea_file = config.get("idea_file", self.idea_file)
        self.poll_interval = config.get("poll_interval", self.poll_interval)

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Inject the EventBus and start background tasks."""
        self._event_bus = event_bus

        # Start background tasks only if the event bus is present
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop (tests may start it later). Defer task creation.
            return

        # Create tasks and keep references so they are not GC'd
        self._tasks.append(loop.create_task(self._heartbeat_loop()))
        self._tasks.append(loop.create_task(self._idea_watcher()))

    async def _heartbeat_loop(self) -> None:
        """Periodically publish heartbeat events."""
        while True:
            if self._event_bus:
                evt = Event(
                    event_type=EventType.CUSTOM,
                    source=self.name,
                    priority=EventPriority.LOW,
                    data={"subtype": "HEARTBEAT", "timestamp": time.time()},
                )
                self._event_bus.publish(evt)
            await asyncio.sleep(self.heartbeat_interval)

    async def _idea_watcher(self) -> None:
        """Watch a file for modifications and publish NEW_IDEA_DETECTED events."""
        last_mtime = 0.0
        path = self.idea_file

        while True:
            try:
                if os.path.exists(path):
                    mtime = os.path.getmtime(path)
                    if mtime > last_mtime:
                        last_mtime = mtime
                        # Read file content
                        try:
                            with open(path, "r", encoding="utf-8") as fh:
                                content = fh.read()
                        except Exception:
                            content = ""

                        if self._event_bus:
                            evt = Event(
                                event_type=EventType.CUSTOM,
                                source=self.name,
                                priority=EventPriority.NORMAL,
                                data={"subtype": "NEW_IDEA_DETECTED", "content": content},
                            )
                            self._event_bus.publish(evt)
            except Exception:
                # Swallow errors to keep watcher alive
                pass

            await asyncio.sleep(self.poll_interval)

    async def execute(self, context: SharedContext) -> SharedContext:
        """Passive execute - the plugin runs its background tasks and returns context."""
        return context
