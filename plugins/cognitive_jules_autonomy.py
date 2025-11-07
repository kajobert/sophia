# plugins/cognitive_jules_autonomy.py
"""
Cognitive Jules Autonomy Plugin

High-level autonomous workflows for Jules AI agent integration.
Provides Sophie with simple tools to delegate entire tasks to Jules.
"""

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from pydantic import BaseModel, Field
from typing import Dict, Any, List


class DelegateTaskRequest(BaseModel):
    """Request to delegate a task to Jules"""

    repo: str = Field(..., description="Repository in 'owner/repo' format")
    task: str = Field(..., description="Task description for Jules")
    parallel: int = Field(default=1, ge=1, le=5, description="Number of parallel sessions")
    auto_apply: bool = Field(
        default=True, description="Automatically apply results when completed"
    )
    timeout: int = Field(default=3600, description="Maximum wait time in seconds")
    check_interval: int = Field(default=30, description="Polling interval in seconds")


class JulesAutonomyPlugin(BasePlugin):
    """
    High-level autonomous Jules workflows.

    Provides Sophie with simple commands to:
    1. Delegate entire tasks to Jules
    2. Automatically monitor progress
    3. Auto-apply results when completed

    This eliminates the need for Sophie to manually orchestrate
    create_session → monitor → pull_results workflows.
    """

    def __init__(self):
        super().__init__()
        self.jules_api_tool = None  # API for session creation
        self.jules_cli_tool = None  # CLI for pulling results
        self.jules_monitor = None
        self.logger = None

    @property
    def name(self) -> str:
        return "cognitive_jules_autonomy"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "2.0.0-hybrid"  # HYBRID: API + CLI strategy

    def setup(self, config):
        """Inject required tools"""
        self.logger = config.get("logger")

        if not self.logger:
            raise ValueError("Logger must be provided in config - dependency injection required")

        all_plugins = config.get("all_plugins", {})

        # Inject Jules API tool (for session creation)
        self.jules_api_tool = all_plugins.get("tool_jules")
        if not self.jules_api_tool:
            self.logger.warning("tool_jules (API) not found - session creation disabled")

        # Inject Jules CLI tool (for pulling results)
        self.jules_cli_tool = all_plugins.get("tool_jules_cli")
        if not self.jules_cli_tool:
            self.logger.warning("tool_jules_cli not found - local result pulling disabled")

        # Inject Jules monitor
        self.jules_monitor = all_plugins.get("cognitive_jules_monitor")
        if not self.jules_monitor:
            self.logger.warning("cognitive_jules_monitor not found - autonomy features disabled")

        # Report status
        if self.jules_api_tool and self.jules_cli_tool and self.jules_monitor:
            self.logger.info(
                "✅ Jules Autonomy Plugin ready - HYBRID MODE (API creation + CLI pull)"
            )
        elif self.jules_api_tool and self.jules_monitor:
            self.logger.info("⚡ Jules Autonomy Plugin ready - API-ONLY MODE (no local pull)")

    async def delegate_task(
        self,
        context: SharedContext,
        repo: str,
        task: str,
        parallel: int = 1,
        auto_apply: bool = True,
        timeout: int = 3600,
        check_interval: int = 30,
    ) -> Dict[str, Any]:
        """
        Delegate a complete task to Jules with autonomous monitoring.

        This is a HIGH-LEVEL autonomous workflow that:
        1. Creates Jules session via API (not CLI)
        2. Monitors progress via API until COMPLETED
        3. Automatically pulls and applies results (if auto_apply=True)

        Sophie can use this single command instead of manually orchestrating
        create_session → monitor_until_completion → pull_results.

        Args:
            context: Shared execution context
            repo: Repository in 'owner/repo' format (e.g., 'ShotyCZ/sophia')
            task: Task description for Jules (e.g., 'Create test file sandbox/test.txt')
            parallel: DEPRECATED (API doesn't support parallel sessions)
            auto_apply: If True, automatically apply results when completed
            timeout: Maximum wait time in seconds
            check_interval: Polling interval in seconds

        Returns:
            Dict with complete workflow results:
            {
                "success": bool,
                "session_id": str,
                "status": JulesSessionStatus,
                "results_applied": bool,
                "changes": str (if applied),
                "workflow": "autonomous"
            }

        Example:
            >>> result = await delegate_task(
            ...     context,
            ...     repo="ShotyCZ/sophia",
            ...     task="Add hello world function to sandbox/utils.py",
            ...     auto_apply=True
            ... )
            >>> print(result["success"])  # True
            >>> print(result["results_applied"])  # True
        """
        # Validate request
        try:
            request = DelegateTaskRequest(
                repo=repo,
                task=task,
                parallel=parallel,
                auto_apply=auto_apply,
                timeout=timeout,
                check_interval=check_interval,
            )
        except Exception as e:
            context.logger.error(f"Invalid delegate_task parameters: {e}")
            return {
                "success": False,
                "error": f"Invalid parameters: {e}",
                "workflow": "autonomous",
            }

        # Check if tools are available
        if not self.jules_api_tool or not self.jules_monitor:
            error = "Jules API tool or monitor not available"
            context.logger.error(error)
            return {"success": False, "error": error, "workflow": "autonomous"}

        context.logger.info(f"🚀 Starting AUTONOMOUS Jules workflow: {request.task[:50]}...")
        context.logger.info(
            f"   Repo: {request.repo}, Parallel: {request.parallel}, "
            f"Auto-apply: {request.auto_apply}"
        )

        # STEP 1: Create Jules session via API
        context.logger.info("📝 STEP 1: Creating Jules session via API...")

        # Convert repo format: "owner/repo" -> "sources/github/owner/repo"
        source = f"sources/github/{request.repo}"

        try:
            jules_session = await self.jules_api_tool.create_session(
                context=context,
                prompt=request.task,
                source=source,
                branch="main",
                auto_pr=False,  # Don't auto-create PR, we'll handle results ourselves
            )

            # JulesSession.name format: "sessions/{session_id}"
            session_id = jules_session.name.split("/")[1]
            context.logger.info(f"✅ Created session: {session_id}")

        except Exception as e:
            context.logger.error(f"❌ Failed to create session: {e}")
            return {"success": False, "error": str(e), "workflow": "autonomous"}

        # STEP 2: Monitor until completion
        context.logger.info(f"👁️  STEP 2: Monitoring session {session_id} until completion...")

        monitor_result = await self.jules_monitor.monitor_until_completion(
            context,
            session_id=session_id,
            check_interval=request.check_interval,
            timeout=request.timeout,
            auto_pull=request.auto_apply,  # Enable hybrid mode if auto_apply
        )

        # Check if monitoring succeeded
        status = monitor_result.get("status")
        if not status or not status.is_completed:
            error = "Session did not complete within timeout"
            context.logger.error(f"❌ {error}")
            return {
                "success": False,
                "error": error,
                "session_id": session_id,  # Changed from session_ids (API returns single session)
                "status": status,
                "workflow": "autonomous",
            }

        # STEP 3: Results handling
        if request.auto_apply:
            context.logger.info("📥 STEP 3: Pulling and applying results...")

            # HYBRID MODE: Use CLI for pulling results (API doesn't support this)
            if self.jules_cli_tool:
                context.logger.info("   Using CLI for `jules pull` (hybrid mode)")
                try:
                    pull_result = await self.jules_cli_tool.pull_results(
                        context,
                        session_id=session_id,
                        apply=True,  # Apply changes to local repository
                    )

                    if pull_result.get("success"):
                        changes = pull_result.get("changes", "")
                        context.logger.info("✅ AUTONOMOUS WORKFLOW COMPLETED SUCCESSFULLY!")
                        context.logger.info(f"   Session: {session_id}")
                        context.logger.info(f"   Status: {status.state}")
                        context.logger.info("   Results: Applied to local repository via CLI")

                        return {
                            "success": True,
                            "session_id": session_id,
                            "status": status,
                            "results_applied": True,
                            "changes": changes,
                            "method": "hybrid_cli_pull",
                            "workflow": "autonomous",
                        }
                    else:
                        error = pull_result.get("error", "Failed to pull results")
                        context.logger.warning(f"⚠️ Session completed but CLI pull failed: {error}")
                        return {
                            "success": True,  # Session completed successfully
                            "session_id": session_id,
                            "status": status,
                            "results_applied": False,
                            "error": error,
                            "workflow": "autonomous",
                        }
                except Exception as e:
                    context.logger.error(f"❌ CLI pull error: {e}")
                    return {
                        "success": True,
                        "session_id": session_id,
                        "status": status,
                        "results_applied": False,
                        "error": str(e),
                        "workflow": "autonomous",
                    }
            else:
                # No CLI tool - fallback to monitor's auto_pull (if it exists)
                results_applied = monitor_result.get("results_applied", False)
                changes = monitor_result.get("changes", "")

                if results_applied:
                    context.logger.info("✅ Results applied via monitor (API mode)")
                    return {
                        "success": True,
                        "session_id": session_id,
                        "status": status,
                        "results_applied": True,
                        "changes": changes,
                        "method": "api_monitor",
                        "workflow": "autonomous",
                    }
                else:
                    context.logger.warning(
                        "⚠️ No CLI tool available and monitor didn't apply results"
                    )
                    return {
                        "success": True,
                        "session_id": session_id,
                        "status": status,
                        "results_applied": False,
                        "error": "No CLI tool for pulling results",
                        "workflow": "autonomous",
                    }
        else:
            # No auto-apply - just report completion
            context.logger.info("✅ Session completed (auto-apply disabled)")
            return {
                "success": True,
                "session_id": session_id,
                "status": status,
                "results_applied": False,
                "message": "Use jules_cli.pull_results() to retrieve changes",
                "workflow": "autonomous",
            }

    async def execute(
        self, context: SharedContext, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool call - route to delegate_task"""
        if tool_name == "delegate_task":
            return await self.delegate_task(
                context=context,
                repo=arguments["repo"],
                task=arguments["task"],
                parallel=arguments.get("parallel", 1),
                auto_apply=arguments.get("auto_apply", True),
                timeout=arguments.get("timeout", 3600),
                check_interval=arguments.get("check_interval", 30),
            )
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Tool definitions for cognitive planner"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "delegate_task",
                    "description": (
                        "AUTONOMOUS workflow: Delegate a complete task to Jules AI agent. "
                        "This single command handles the entire process: creates session, "
                        "monitors progress, and automatically applies results. "
                        "Use this for any coding task you want Jules to complete autonomously. "
                        "Example tasks: 'Create test file', 'Fix bug in auth.py', 'Add documentation'."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository in 'owner/repo' format. Example: 'ShotyCZ/sophia'",
                            },
                            "task": {
                                "type": "string",
                                "description": "Complete task description for Jules. Be specific about what to create/modify. Example: 'Create file sandbox/hello.py with a hello_world() function that prints Hello World'",
                            },
                            "parallel": {
                                "type": "integer",
                                "description": "Number of parallel attempts (1-5). Higher = more solution diversity but slower.",
                                "default": 1,
                                "minimum": 1,
                                "maximum": 5,
                            },
                            "auto_apply": {
                                "type": "boolean",
                                "description": "If true, automatically apply Jules results to local repository when completed. If false, just monitor and report completion.",
                                "default": True,
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Maximum wait time in seconds (default: 3600 = 1 hour)",
                                "default": 3600,
                            },
                            "check_interval": {
                                "type": "integer",
                                "description": "Seconds between progress checks (default: 30)",
                                "default": 30,
                            },
                        },
                        "required": ["repo", "task"],
                    },
                },
            }
        ]
