import asyncio
import sys
import os
from typing import Optional
from datetime import datetime
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


class TerminalInterface(BasePlugin):
    """
    Clean, simple terminal interface for Sophia.
    
    Version 2.0.0 - Enhanced with:
    - Formatted conversation display
    - Color-coded system activity
    - Timestamps for all messages
    - Clear visual separation
    """

    def __init__(self):
        super().__init__()
        self._input_queue: Optional[asyncio.Queue] = None
        self._input_task: Optional[asyncio.Task] = None
        
        # Conversation tracking
        self._conversation_history = []
        self._last_activity = None
        
        # Print welcome banner
        self._print_welcome()

    
    def _print_welcome(self):
        """Print welcome banner with instructions."""
        print("\n" + "="*70)
        print("🤖 SOPHIA AI - Interactive Terminal Interface")
        print("="*70)
        print("💬 Konverzace je připravena!")
        print("📊 Uvidíš: Tvé zprávy | Sophia odpovědi | Systémová aktivita")
        print("⌨️  Napiš zprávu a stiskni Enter")
        print("🚪 Ukonči: Ctrl+C nebo 'exit'")
        print("="*70 + "\n")
    
    def _log_activity(self, activity: str, type: str = "info"):
        """Log system activity with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color codes for different activity types
        colors = {
            "info": "\033[36m",      # Cyan
            "thinking": "\033[33m",  # Yellow
            "success": "\033[32m",   # Green
            "error": "\033[31m",     # Red
            "system": "\033[35m"     # Magenta
        }
        reset = "\033[0m"
        
        color = colors.get(type, colors["info"])
        icon = {
            "info": "ℹ️",
            "thinking": "🤔",
            "success": "✅",
            "error": "❌",
            "system": "⚙️"
        }.get(type, "•")
        
        print(f"{color}[{timestamp}] {icon} {activity}{reset}")
        self._last_activity = activity
    
    def _display_user_input(self, user_input: str):
        """Display user's message in a clear format."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n{'─'*70}")
        print(f"\033[1m👤 TY [{timestamp}]\033[0m")
        print(f"   {user_input}")
        print(f"{'─'*70}\n")
        
        # Track in conversation history
        self._conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
    
    def _display_sophia_response(self, response: str):
        """Display Sophia's response in a clear format."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Extract plan status if present (technical indicator)
        clean_response = response
        if response.startswith("Plan executed successfully. Result: "):
            # Log the success indicator separately
            self._log_activity("Plán úspěšně vykonán", "success")
            # Show only the actual response to user
            clean_response = response[len("Plan executed successfully. Result: "):]
        elif "Plan executed successfully." in response:
            # Handle other variants
            self._log_activity("Plán úspěšně vykonán", "success")
            clean_response = response.replace("Plan executed successfully. Result: ", "").replace("Plan executed successfully.", "").strip()
        
        # Display clean response in cyan (visible but neutral, not green for success)
        print(f"\n{'═'*70}")
        print(f"\033[1m🤖 SOPHIA [{timestamp}]\033[0m")
        print(f"\033[36m{clean_response}\033[0m")  # Cyan - clearly visible
        print(f"{'═'*70}\n")
        
        # Track in conversation history
        self._conversation_history.append({
            "role": "assistant",
            "content": clean_response,
            "timestamp": timestamp
        })

    @property
    def name(self) -> str:
        return "interface_terminal"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.INTERFACE

    @property
    def version(self) -> str:
        return "2.0.0"

    def setup(self, config: dict) -> None:
        """Setup the terminal interface."""
        pass  # No setup needed for basic terminal

    def prompt(self):
        """Prints the user input prompt to the console."""
        print("\n" + "─" * 70)
        print("\033[1;36m💭 TY ▶\033[0m ", end="", flush=True)

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Asynchronously waits for input from the terminal.
        
        Enhanced to show system activity and responses.
        """
        # ALWAYS register response callback (payload resets each loop iteration)
        context.payload["_response_callback"] = self._display_sophia_response
        
        if context.use_event_driven:
            # Non-blocking mode - check queue for input
            return await self._execute_nonblocking(context)
        else:
            # Legacy blocking mode
            return await self._execute_blocking(context)

    async def _execute_blocking(self, context: SharedContext) -> SharedContext:
        """Blocking input with formatted display."""
        import sys
        loop = asyncio.get_running_loop()
        
        # Use sys.stdin.readline() - read directly from stdin
        # The prompt is already displayed by the prompt() method in kernel
        def read_input():
            line = sys.stdin.readline()
            return line.rstrip('\n\r') if line else ""
        
        user_input = await loop.run_in_executor(None, read_input)
        
        # Display formatted user input
        if user_input:
            self._display_user_input(user_input)
            self._log_activity("Zpracovávám tvoji zprávu...", "thinking")
        
        context.user_input = user_input
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
