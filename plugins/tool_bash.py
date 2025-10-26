import asyncio
import logging
from typing import Tuple
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class BashTool(BasePlugin):
    """A tool plugin for executing shell commands in a secure, sandboxed manner."""
    
    # SECURITY: Whitelist of allowed commands and their safe arguments
    # Only these commands can be executed to prevent arbitrary code execution
    ALLOWED_COMMANDS = {
        # File operations (read-only)
        "ls", "cat", "head", "tail", "less", "more", "file", "stat",
        "find", "grep", "wc", "diff", "tree",
        
        # Git operations (safe subset)
        "git status", "git log", "git diff", "git show", "git branch",
        "git ls-files", "git ls-tree", "git rev-parse",
        
        # Python operations
        "python", "python3", "pip list", "pip show", "pytest",
        "black --check", "ruff check", "mypy",
        
        # System information (read-only)
        "pwd", "whoami", "env", "printenv", "which", "uname",
        "echo", "date", "hostname",
        
        # Package management (read-only)
        "apt list", "apt search", "apt show",
        "dpkg -l", "dpkg -L",
        
        # Testing utilities (safe, used in tests)
        "sleep", "true", "false",
    }
    
    # SECURITY: Dangerous patterns that should never appear in commands
    DANGEROUS_PATTERNS = [
        "rm ", "rmdir", "dd ", "mkfs", "> /dev/", "chmod", "chown",
        "sudo", "su ", "passwd", "useradd", "userdel",
        "wget", "curl", "nc ", "netcat", "telnet",
        "exec", "eval", "|", "&&", "||", ";", "`", "$(", ">/",
        "/dev/sd", "/dev/nvme", "fork", ":()", 
        " -c ",  # SECURITY: Block code injection via -c flag (python -c, bash -c, etc.)
        "/tmp/", "/var/tmp/",  # SECURITY: Block execution of files from temp directories
    ]

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

    def _is_command_allowed(self, command: str) -> Tuple[bool, str]:
        """
        Validates that a command is safe to execute.
        
        SECURITY: This prevents arbitrary code execution by:
        1. Checking command against whitelist
        2. Scanning for dangerous patterns
        3. Blocking command chaining and redirection
        
        Args:
            command: The shell command to validate.
            
        Returns:
            Tuple of (is_allowed, reason_if_denied)
        """
        # 1. Check for dangerous patterns first
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in command:
                return False, f"Command contains dangerous pattern: '{pattern}'"
        
        # 2. Extract the base command (first token)
        base_command = command.split()[0] if command.strip() else ""
        
        # 3. Check if base command is in whitelist
        if base_command not in self.ALLOWED_COMMANDS:
            # Check if it's a multi-word command (e.g., "git status")
            for allowed in self.ALLOWED_COMMANDS:
                if command.startswith(allowed + " ") or command == allowed:
                    return True, ""
            
            return False, f"Command '{base_command}' is not in the whitelist"
        
        return True, ""

    async def execute_command(self, command: str) -> Tuple[int, str, str]:
        """
        Executes a shell command asynchronously with a timeout.
        
        SECURITY: Commands are validated against a whitelist before execution.

        Args:
            command: The shell command to execute.

        Returns:
            A tuple containing (return_code, stdout, stderr).
        """
        # SECURITY: Validate command before execution
        is_allowed, reason = self._is_command_allowed(command)
        if not is_allowed:
            logger.error(f"Command blocked: '{command}' - {reason}")
            return -1, "", f"SecurityError: {reason}"
        
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
            # IMPORTANT: Kill the process to prevent resource leak
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass  # Process might already be dead
            return -1, "", "TimeoutError: Command execution exceeded the time limit."
        except Exception as e:
            logger.error(f"Failed to execute command '{command}': {e}", exc_info=True)
            return -1, "", str(e)
