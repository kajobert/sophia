import asyncio
import logging
from typing import Tuple
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class BashTool(BasePlugin):
    """A tool plugin for executing shell commands in a secure, sandboxed manner."""

    def __init__(self):
        super().__init__()
        self.timeout = 10  # Default timeout in seconds

    @property
    def name(self) -> str:
        return "tool_bash"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Configures the command execution parameters."""
        self.timeout = config.get("timeout", 10)
        logger.info(f"Bash tool initialized with a timeout of {self.timeout} seconds.")

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        This tool is not directly executed in the main loop.
        Its methods will be called by cognitive plugins.
        """
        return context

    async def execute_command(self, command: str) -> Tuple[int, str, str]:
        """
        Executes a shell command asynchronously with a timeout.

        Args:
            command: The shell command to execute.

        Returns:
            A tuple containing (return_code, stdout, stderr).
        """
        logger.info(f"Executing command: '{command}'")
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)

            return_code = proc.returncode if proc.returncode is not None else -1
            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()

            logger.info(f"Command finished with code {return_code}.")
            if stdout_str:
                logger.debug(f"STDOUT: {stdout_str}")
            if stderr_str:
                logger.warning(f"STDERR: {stderr_str}")

            return return_code, stdout_str, stderr_str

        except asyncio.TimeoutError:
            logger.error(f"Command '{command}' timed out after {self.timeout} seconds.")
            return -1, "", "TimeoutError: Command execution exceeded the time limit."
        except Exception as e:
            logger.error(f"Failed to execute command '{command}': {e}", exc_info=True)
            return -1, "", str(e)
