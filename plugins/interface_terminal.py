import asyncio
import sys
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


class TerminalInterface(BasePlugin):
    """
    Implements a basic interaction with Sophia via the standard input/output
    in a terminal.
    """

    @property
    def name(self) -> str:
        return "interface_terminal"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.INTERFACE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        pass

    def prompt(self):
        """Prints the user input prompt to the console."""
        print("<<< Uživatel: ", end="", flush=True)

    async def execute(self, context: SharedContext) -> SharedContext:
        """Asynchronously waits for input from the terminal."""
        loop = asyncio.get_running_loop()
        # We use readline to wait for input without blocking the asyncio loop,
        # and without displaying its own prompt.
        user_input = await loop.run_in_executor(None, sys.stdin.readline)
        context.user_input = user_input.strip()
        return context
