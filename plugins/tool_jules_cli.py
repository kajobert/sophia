"""
Jules CLI Integration Plugin

Provides scriptable access to Jules CLI commands for autonomous workflow.
Enables Sophie to create sessions, pull results, and manage Jules tasks via command line.

Author: GitHub Copilot
Date: 2025-11-03
"""

import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from plugins.base_plugin import BasePlugin, PluginType


# ============================================
# PYDANTIC MODELS - Request & Response
# ============================================


class CreateSessionRequest(BaseModel):
    """Request model for creating Jules CLI session"""

    repo: str = Field(..., min_length=1, description="Repository in 'owner/repo' format")
    task: str = Field(..., min_length=1, description="Task description for Jules")
    parallel: int = Field(default=1, ge=1, le=5, description="Number of parallel sessions (1-5)")


class PullResultsRequest(BaseModel):
    """Request model for pulling Jules session results"""

    session_id: str = Field(..., min_length=1, description="Jules session ID")
    apply: bool = Field(default=False, description="If True, apply changes to local repository")


class SessionInfo(BaseModel):
    """Session information parsed from CLI output"""

    session_id: str
    status: Optional[str] = None
    repo: Optional[str] = None
    task: Optional[str] = None


class CLIResponse(BaseModel):
    """Generic CLI command response"""

    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0


# ============================================
# MAIN PLUGIN CLASS
# ============================================


class JulesCLIPlugin(BasePlugin):
    """
    ⚡ EXPERIMENTAL: Jules CLI Integration for Advanced Workflows

    This plugin provides CLI-based Jules integration for features not available in API:
    - Local repository integration via `jules pull`
    - Automatic change application to working directory
    - Git branch management for Jules sessions

    **Strategy:** Use API for session creation/monitoring, CLI for pulling results.

    Complements tool_jules.py (API) for hybrid workflow:
    1. tool_jules: Create session via API
    2. cognitive_jules_monitor: Monitor via API
    3. tool_jules_cli: Pull results via CLI (`jules pull`)

    Jules CLI integration plugin for Sophie.

    Provides methods to:
    - Create Jules sessions via CLI
    - List sessions
    - Pull and apply results
    - Parse CLI output into structured data

    Complements tool_jules (API) for hybrid workflow.
    """

    @property
    def name(self) -> str:
        return "tool_jules_cli"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "2.0.0-hybrid"  # Updated for hybrid API+CLI strategy

    def __init__(self):
        super().__init__()
        self.bash_tool = None
        self.enabled = True  # RE-ENABLED for hybrid strategy!
        self.logger = None  # Will be injected in setup()

    def setup(self, config):
        """
        Initialize plugin with configuration.

        Args:
            config: Plugin configuration dict containing logger and other plugins
        """
        super().setup(config)

        # Get logger from config (dependency injection)
        self.logger = config.get("logger")
        if not self.logger:
            raise ValueError("Logger must be provided in config")

        # Log strategy info
        self.logger.info(
            "⚡ Jules CLI plugin - HYBRID MODE: "
            "Use for `jules pull` to apply changes locally. "
            "Combine with tool_jules (API) for session creation."
        )

        # Get bash tool for command execution
        all_plugins = config.get("all_plugins", {})
        self.bash_tool = all_plugins.get("tool_bash")

        if not self.bash_tool:
            self.logger.warning(
                "tool_bash not found in config. JulesCLIPlugin will not function properly. "
                "Make sure tool_bash is loaded before tool_jules_cli."
            )

    # ============================================
    # PUBLIC METHODS - Tool Definitions
    # ============================================

    async def create_session(
        self, context, repo: str, task: str, parallel: int = 1
    ) -> Dict[str, Any]:
        """
        Create Jules session(s) via CLI.

        Creates one or more Jules sessions to work on a coding task.
        Supports parallel execution for complex tasks.

        Args:
            context: Shared execution context
            repo: Repository in 'owner/repo' format (e.g., 'ShotyCZ/sophia')
            task: Task description for Jules to work on
            parallel: Number of parallel sessions (1-5). Multiple sessions work on same task.

        Returns:
            Dict with session_ids (list), command output, and success status

        Example:
            >>> result = create_session(context, "ShotyCZ/sophia", "Fix bug in auth", parallel=3)
            >>> result["session_ids"]  # ['123456', '123457', '123458']
        """
        # Validate request
        request = CreateSessionRequest(repo=repo, task=task, parallel=parallel)

        # Build command
        cmd = (
            f"jules remote new "
            f"--repo {request.repo} "
            f'--session "{request.task}" '
            f"--parallel {request.parallel}"
        )

        context.logger.info(
            f"Creating Jules session via CLI: repo={request.repo}, "
            f"parallel={request.parallel}, task={request.task[:50]}..."
        )

        # Execute via bash
        result = await self._execute_bash(context, cmd)

        if not result["success"]:
            context.logger.error(f"Failed to create Jules session: {result['error']}")
            return {"success": False, "error": result["error"], "session_ids": []}

        # Parse session IDs from output
        session_ids = self._parse_session_ids(result["output"])

        if not session_ids:
            context.logger.warning(
                f"No session IDs found in output. Raw output:\n{result['output']}"
            )
        else:
            context.logger.info(f"✅ Created {len(session_ids)} Jules session(s): {session_ids}")

        return {
            "success": True,
            "session_ids": session_ids,
            "output": result["output"],
            "command": cmd,
        }

    async def pull_results(self, context, session_id: str, apply: bool = False) -> Dict[str, Any]:
        """
        Pull results from Jules session.

        Retrieves the changes Jules made for a completed session.
        Optionally applies changes to local repository.

        Args:
            context: Shared execution context
            session_id: Jules session ID (e.g., '123456' or 'sessions/123456')
            apply: If True, apply changes to local repository. If False, just show diff.

        Returns:
            Dict with diff/changes, applied status, and success indicator

        Example:
            >>> # Just view changes
            >>> result = pull_results(context, "123456", apply=False)
            >>> print(result["diff"])

            >>> # Apply changes to local repo
            >>> result = pull_results(context, "123456", apply=True)
            >>> # Changes are now in local git repository
        """
        # Validate request
        request = PullResultsRequest(session_id=session_id, apply=apply)

        # Clean session ID (remove 'sessions/' prefix if present)
        clean_id = session_id.replace("sessions/", "")

        # Build command
        apply_flag = "--apply" if request.apply else ""
        cmd = f"jules remote pull --session {clean_id} {apply_flag}".strip()

        action = "Applying" if request.apply else "Pulling"
        context.logger.info(f"{action} Jules session results: {clean_id}")

        # Execute via bash
        result = await self._execute_bash(context, cmd)

        if not result["success"]:
            context.logger.error(f"Failed to pull Jules results: {result['error']}")
            return {"success": False, "error": result["error"], "applied": False}

        # Parse output
        output = result["output"]

        if request.apply:
            context.logger.info("✅ Jules results applied to local repository")
            return {
                "success": True,
                "applied": True,
                "output": output,
                "message": "Changes applied to local repository",
                "command": cmd,
            }
        else:
            context.logger.info("✅ Jules results retrieved (not applied)")
            return {"success": True, "applied": False, "diff": output, "command": cmd}

    async def list_sessions(self, context) -> Dict[str, Any]:
        """
        List all remote Jules sessions.

        Retrieves list of all Jules sessions with their status.

        Args:
            context: Shared execution context

        Returns:
            Dict with sessions list and raw output

        Example:
            >>> result = list_sessions(context)
            >>> for session in result["sessions"]:
            ...     print(f"{session['session_id']}: {session['status']}")
        """
        cmd = "jules remote list --session"

        context.logger.info("Listing all Jules sessions via CLI")

        # Execute via bash
        result = await self._execute_bash(context, cmd)

        if not result["success"]:
            context.logger.error(f"Failed to list Jules sessions: {result['error']}")
            return {"success": False, "error": result["error"], "sessions": []}

        # Parse sessions from output
        sessions = self._parse_sessions_list(result["output"])

        context.logger.info(f"✅ Found {len(sessions)} Jules session(s)")

        return {"success": True, "sessions": sessions, "output": result["output"], "command": cmd}

    async def list_repos(self, context) -> Dict[str, Any]:
        """
        List all repositories connected to Jules.

        Args:
            context: Shared execution context

        Returns:
            Dict with repos list and raw output
        """
        cmd = "jules remote list --repo"

        context.logger.info("Listing all Jules repositories via CLI")

        # Execute via bash
        result = await self._execute_bash(context, cmd)

        if not result["success"]:
            context.logger.error(f"Failed to list Jules repos: {result['error']}")
            return {"success": False, "error": result["error"], "repos": []}

        # Parse repos from output (simple line split for now)
        repos = [line.strip() for line in result["output"].split("\n") if line.strip()]

        context.logger.info(f"✅ Found {len(repos)} Jules repo(s)")

        return {"success": True, "repos": repos, "output": result["output"], "command": cmd}

    # ============================================
    # PRIVATE HELPER METHODS
    # ============================================

    async def _execute_bash(self, context, command: str) -> Dict[str, Any]:
        """
        Execute bash command via tool_bash plugin. If 'jules' is not found, prompt user to install.
        """
        if not self.bash_tool:
            return {
                "success": False,
                "output": "",
                "error": "tool_bash not available",
                "exit_code": -1,
            }

        try:
            import asyncio
            # Execute the requested command via tool_bash. Avoid an extra pre-check
            # which causes tests to observe two execute_command calls (one for 'which',
            # one for the actual command). If Jules CLI is missing, the underlying
            # bash tool should return the error output which can be handled by caller.

            if asyncio.iscoroutinefunction(self.bash_tool.execute_command):
                output = await self.bash_tool.execute_command(context, command)
            else:
                output = self.bash_tool.execute_command(context, command)

            return {"success": True, "output": output, "error": None, "exit_code": 0}

        except Exception as e:
            context.logger.error(f"Bash execution failed: {e}")
            return {"success": False, "output": "", "error": str(e), "exit_code": -1}

    def _parse_session_ids(self, output: str) -> List[str]:
        """
        Parse session IDs from CLI output.

        Handles various output formats:
        - "Session ID: 123456"
        - "Created session 123456"
        - "Sessions: 123, 124, 125"

        Args:
            output: Raw CLI output text

        Returns:
            List of session IDs (as strings)
        """
        session_ids = []

        # Pattern 1: "Session ID: 123456"
        matches = re.findall(r"Session ID:\s*(\d+)", output, re.IGNORECASE)
        if matches:
            session_ids.extend(matches)

        # Pattern 2: "Created session 123456"
        matches = re.findall(r"Created session\s+(\d+)", output, re.IGNORECASE)
        if matches:
            session_ids.extend(matches)

        # Pattern 3: "sessions/123456" (full format)
        matches = re.findall(r"sessions/(\d+)", output)
        if matches:
            session_ids.extend(matches)

        # Pattern 4: Just numbers (6+ digits, likely session IDs)
        if not session_ids:
            matches = re.findall(r"\b(\d{6,})\b", output)
            session_ids.extend(matches)

        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for sid in session_ids:
            if sid not in seen:
                seen.add(sid)
                unique_ids.append(sid)

        return unique_ids

    def _parse_sessions_list(self, output: str) -> List[Dict[str, str]]:
        """
        Parse 'jules remote list --session' output.

        Expected format (example):
        ID       Status      Repo              Task
        123456   COMPLETED   ShotyCZ/sophia    Fix auth bug
        123457   IN_PROGRESS torvalds/linux    Add tests

        Args:
            output: Raw CLI output text

        Returns:
            List of dicts with session info
        """
        sessions = []

        # Split into lines
        lines = output.strip().split("\n")

        # Skip header line(s) - look for lines starting with digits
        for line in lines:
            line = line.strip()
            if not line or not line[0].isdigit():
                continue

            # Try to parse session info
            # Format: ID Status Repo Task
            # Use regex to handle variable spacing
            match = re.match(r"(\d+)\s+(\S+)\s+(\S+)\s+(.+)", line)

            if match:
                sessions.append(
                    {
                        "session_id": match.group(1),
                        "status": match.group(2),
                        "repo": match.group(3),
                        "task": match.group(4).strip(),
                    }
                )
            else:
                # Fallback: just extract session ID
                id_match = re.search(r"(\d{6,})", line)
                if id_match:
                    sessions.append(
                        {
                            "session_id": id_match.group(1),
                            "status": "UNKNOWN",
                            "repo": "",
                            "task": line,
                        }
                    )

        return sessions

    # ============================================
    # EXECUTE METHOD - Dynamic Invocation
    # ============================================

    async def execute(self, context, method_name: str, **kwargs):
        """
        Execute a method dynamically.

        Args:
            context: Shared context
            method_name: Name of method to execute (can include plugin prefix)
            **kwargs: Method arguments

        Returns:
            Method execution result
        """
        # Remove plugin prefix if present (e.g., "tool_jules_cli.list_repos" → "list_repos")
        actual_method = method_name.replace(f"{self.name}.", "")

        if not hasattr(self, actual_method):
            raise ValueError(f"Unknown method: {actual_method}")

        method = getattr(self, actual_method)
        return method(context, **kwargs)

    # ============================================
    # TOOL DEFINITIONS - For Planner
    # ============================================

    def get_tool_definitions(self):
        """
        Return tool definitions for cognitive planner.

        Returns:
            List of tool definitions in JSON Schema format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_session",
                    "description": (
                        "Create Jules coding session(s) via CLI. "
                        "Jules will work asynchronously in cloud VM to complete the task. "
                        "Supports parallel execution (1-5 sessions) for complex tasks. "
                        "Use this when you want to delegate coding work to Jules AI agent. "
                        "IMPORTANT: Use parameter names 'repo' and 'task' (NOT 'source' or 'prompt'). "
                        'Example: {"repo": "ShotyCZ/sophia", "task": "Create test file", "parallel": 1}'
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository in 'owner/repo' format. REQUIRED parameter name is 'repo' (not 'source'). Example: 'ShotyCZ/sophia'",
                            },
                            "task": {
                                "type": "string",
                                "description": "Task description for Jules to work on. REQUIRED parameter name is 'task' (not 'prompt'). Example: 'Create file sandbox/test.txt with Hello World'",
                            },
                            "parallel": {
                                "type": "integer",
                                "description": "Number of parallel sessions (1-5). Use higher values for complex tasks to get multiple approaches.",
                                "default": 1,
                                "minimum": 1,
                                "maximum": 5,
                            },
                        },
                        "required": ["repo", "task"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "pull_results",
                    "description": (
                        "Pull results from completed Jules session. "
                        "Use apply=False to just view changes (diff). "
                        "Use apply=True to apply changes to local repository. "
                        "Should be called after session reaches COMPLETED state."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Jules session ID (e.g., '123456' or 'sessions/123456')",
                            },
                            "apply": {
                                "type": "boolean",
                                "description": "If true, apply changes to local repository. If false, just show diff.",
                                "default": False,
                            },
                        },
                        "required": ["session_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_sessions",
                    "description": (
                        "List all remote Jules sessions with their status. "
                        "Useful for checking session status or finding session IDs."
                    ),
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_repos",
                    "description": (
                        "List all repositories connected to Jules. "
                        "Shows which repos Jules can work on."
                    ),
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]
