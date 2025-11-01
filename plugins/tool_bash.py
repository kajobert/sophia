import asyncio
import sys
from typing import Tuple, List, Dict, Any

from pydantic import BaseModel, Field

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


class ExecuteCommandArgs(BaseModel):
    """Pydantic model for arguments of the execute_command tool."""
    command: str = Field(..., description="The shell command to execute.")


class BashTool(BasePlugin):
    """A tool plugin for executing shell commands in a secure, sandboxed manner."""

    def __init__(self):
        super().__init__()
        self.timeout = 30  # Increased default timeout for potentially longer tasks

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
        self.timeout = config.get("timeout", 30)
        import logging
        logging.info(f"Bash tool initialized with a timeout of {self.timeout} seconds.")

    async def execute(self, context: SharedContext) -> SharedContext:
        """This tool is not directly executed in the main loop."""
        return context

    async def execute_command(self, context: SharedContext, command: str) -> str:
        """
        Executes a shell command using the project's virtual environment.

        Args:
            context: The shared context for the session.
            command: The shell command to execute.

        Returns:
            A string containing the combined stdout and stderr.
        """
        context.logger.info(f"Executing command: '{command}'")

        # Ensure the command runs within the correct virtual environment
        # sys.executable points to the python interpreter of the current venv
        full_command = f'{sys.executable} -m {command}' if 'pytest' in command else command

        try:
            proc = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)

            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()
            combined_output = f"STDOUT:\n{stdout_str}\n\nSTDERR:\n{stderr_str}".strip()

            if proc.returncode == 0:
                context.logger.info(f"Command '{command}' executed successfully.")
            else:
                context.logger.warning(
                    f"Command '{command}' finished with exit code {proc.returncode}."
                )

            return combined_output

        except asyncio.TimeoutError:
            error_msg = f"TimeoutError: Command '{command}' timed out after {self.timeout} seconds."
            context.logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Failed to execute command '{command}': {e}"
            context.logger.error(error_msg, exc_info=True)
            return error_msg

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Gets the definitions of the tools provided by this plugin."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_command",
                    "description": "Executes a shell command (e.g., 'pytest', 'ls -l'). For python scripts like pytest, use 'pytest' as the command.",
                    "parameters": ExecuteCommandArgs.model_json_schema(),
                },
            }
        ]
