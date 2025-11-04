import asyncio
import sys
from typing import Optional
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


class TerminalInterface(BasePlugin):
    """
    Simple terminal interface for interacting with Sophia.

    UPGRADED: Now with cyberpunk sci-fi mode! 🚀
    Use: sophia --scifi for holographic experience
    """


import os
from plugins.base_plugin import BasePlugin

# Try to import sci-fi interface (graceful fallback)
try:
    from plugins.interface_terminal_scifi import InterfaceTerminalSciFi

    SCIFI_AVAILABLE = True
except ImportError:
    SCIFI_AVAILABLE = False


class TerminalInterface(BasePlugin):

    def __init__(self):
        super().__init__()
        self._input_queue: Optional[asyncio.Queue] = None
        self._input_task: Optional[asyncio.Task] = None

        # 🚀 SCI-FI MODE DETECTION
        self.scifi_mode = os.getenv("SOPHIA_SCIFI_MODE", "").lower() == "true"

        if self.scifi_mode and SCIFI_AVAILABLE:
            self.scifi_ui = InterfaceTerminalSciFi()
            print("🚀 SCI-FI MODE ACTIVATED! 🌌")
        else:
            self.scifi_ui = None
            if self.scifi_mode and not SCIFI_AVAILABLE:
                print("⚠️  Sci-fi mode requested but dependencies missing.")
                print("   Install: pip install rich textual")

    @property
    def name(self) -> str:
        return "interface_terminal"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.INTERFACE

    @property
    def version(self) -> str:
        return "1.0.1"

    def setup(self, config: dict) -> None:
        """Setup the terminal interface."""
        pass

    def prompt(self):
        """Prints the user input prompt to the console."""
        print("<<< Uživatel: ", end="", flush=True)

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Asynchronously waits for input from the terminal.

        In event-driven mode, this is non-blocking and checks the input queue.
        In legacy mode, this blocks until input is received.
        """
        if context.use_event_driven:
            # Non-blocking mode - check queue for input
            return await self._execute_nonblocking(context)
        else:
            # Legacy blocking mode
            return await self._execute_blocking(context)

    async def _execute_blocking(self, context: SharedContext) -> SharedContext:
        """Legacy blocking input (original behavior)."""
        loop = asyncio.get_running_loop()
        user_input = await loop.run_in_executor(None, sys.stdin.readline)
        context.user_input = user_input.strip()
        return context

    async def _execute_nonblocking(self, context: SharedContext) -> SharedContext:
        """
        Non-blocking input for event-driven mode.

        Checks if input is available without blocking.
        """
        # Initialize input queue on first use
        if self._input_queue is None:
            self._input_queue = asyncio.Queue()
            # Start background task to read input
            self._input_task = asyncio.create_task(self._read_input_continuously())

        try:
            # Try to get input without blocking (0.01s timeout)
            user_input = await asyncio.wait_for(self._input_queue.get(), timeout=0.01)
            context.user_input = user_input

            # Publish USER_INPUT event
            if context.event_bus:
                from core.events import Event, EventType, EventPriority
                from datetime import datetime

                context.event_bus.publish(
                    Event(
                        event_type=EventType.USER_INPUT,
                        source="interface_terminal",
                        priority=EventPriority.HIGH,
                        data={"input": user_input, "session_id": context.session_id},
                        metadata={"timestamp": datetime.now().isoformat()},
                    )
                )

        except asyncio.TimeoutError:
            # No input available - that's OK in non-blocking mode
            context.user_input = None

        return context

    async def _read_input_continuously(self):
        """
        Background task that continuously reads input and queues it.

        This runs in parallel with the main loop, ensuring input is always
        available when the user types something.
        """
        loop = asyncio.get_running_loop()

        while True:
            try:
                # Read input in executor (blocking operation)
                user_input = await loop.run_in_executor(None, sys.stdin.readline)

                if user_input:
                    # Add to queue for consumption
                    await self._input_queue.put(user_input.strip())
                else:
                    # EOF reached
                    break

            except Exception as e:
                # Log error but don't crash
                print(f"Error reading input: {e}", file=sys.stderr)
                await asyncio.sleep(0.1)

    async def shutdown(self):
        """Clean up background tasks."""
        if self._input_task:
            self._input_task.cancel()
            try:
                await self._input_task
            except asyncio.CancelledError:
                pass
