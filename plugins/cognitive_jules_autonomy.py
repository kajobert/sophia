# plugins/cognitive_jules_autonomy.py
"""
Cognitive Jules Autonomy Plugin

High-level autonomous workflows for Jules AI agent integration.
Provides Sophie with simple tools to delegate entire tasks to Jules.
"""

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio


class DelegateTaskRequest(BaseModel):
    """Request to delegate a task to Jules"""
    repo: str = Field(..., description="Repository in 'owner/repo' format")
    task: str = Field(..., description="Task description for Jules")
    parallel: int = Field(default=1, ge=1, le=5, description="Number of parallel sessions")
    auto_apply: bool = Field(default=True, description="Automatically apply results when completed")
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
        self.jules_cli_tool = None
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
        return "1.0.0"
    
    def setup(self, config):
        """Inject required tools"""
        self.logger = config.get("logger")
        all_plugins = config.get("all_plugins", {})
        
        # Inject Jules CLI tool
        self.jules_cli_tool = all_plugins.get("tool_jules_cli")
        if not self.jules_cli_tool:
            self.logger.warning("tool_jules_cli not found - autonomy features disabled")
        
        # Inject Jules monitor
        self.jules_monitor = all_plugins.get("cognitive_jules_monitor")
        if not self.jules_monitor:
            self.logger.warning("cognitive_jules_monitor not found - autonomy features disabled")
        
        if self.jules_cli_tool and self.jules_monitor:
            self.logger.info("✅ Jules Autonomy Plugin ready - full autonomous workflow enabled")
    
    async def delegate_task(
        self,
        context: SharedContext,
        repo: str,
        task: str,
        parallel: int = 1,
        auto_apply: bool = True,
        timeout: int = 3600,
        check_interval: int = 30
    ) -> Dict[str, Any]:
        """
        Delegate a complete task to Jules with autonomous monitoring.
        
        This is a HIGH-LEVEL autonomous workflow that:
        1. Creates Jules session via CLI
        2. Monitors progress via API until COMPLETED
        3. Automatically pulls and applies results (if auto_apply=True)
        
        Sophie can use this single command instead of manually orchestrating
        create_session → monitor_until_completion → pull_results.
        
        Args:
            context: Shared execution context
            repo: Repository in 'owner/repo' format (e.g., 'ShotyCZ/sophia')
            task: Task description for Jules (e.g., 'Create test file sandbox/test.txt')
            parallel: Number of parallel sessions (1-5)
            auto_apply: If True, automatically apply results when completed
            timeout: Maximum wait time in seconds
            check_interval: Polling interval in seconds
        
        Returns:
            Dict with complete workflow results:
            {
                "success": bool,
                "session_ids": List[str],
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
                check_interval=check_interval
            )
        except Exception as e:
            context.logger.error(f"Invalid delegate_task parameters: {e}")
            return {
                "success": False,
                "error": f"Invalid parameters: {e}",
                "workflow": "autonomous"
            }
        
        # Check if tools are available
        if not self.jules_cli_tool or not self.jules_monitor:
            error = "Jules CLI tool or monitor not available"
            context.logger.error(error)
            return {
                "success": False,
                "error": error,
                "workflow": "autonomous"
            }
        
        context.logger.info(
            f"🚀 Starting AUTONOMOUS Jules workflow: {request.task[:50]}..."
        )
        context.logger.info(
            f"   Repo: {request.repo}, Parallel: {request.parallel}, "
            f"Auto-apply: {request.auto_apply}"
        )
        
        # STEP 1: Create Jules session
        context.logger.info("📝 STEP 1: Creating Jules session...")
        
        create_result = await self.jules_cli_tool.create_session(
            context,
            repo=request.repo,
            task=request.task,
            parallel=request.parallel
        )
        
        if not create_result["success"]:
            context.logger.error(f"❌ Failed to create session: {create_result.get('error')}")
            return {
                "success": False,
                "error": create_result.get("error"),
                "workflow": "autonomous"
            }
        
        session_ids = create_result["session_ids"]
        context.logger.info(f"✅ Created {len(session_ids)} session(s): {session_ids}")
        
        # Use first session for monitoring (in parallel mode, all sessions work on same task)
        session_id = session_ids[0]
        
        # STEP 2: Monitor until completion
        context.logger.info(
            f"👁️  STEP 2: Monitoring session {session_id} until completion..."
        )
        
        monitor_result = self.jules_monitor.monitor_until_completion(
            context,
            session_id=session_id,
            check_interval=request.check_interval,
            timeout=request.timeout,
            auto_pull=request.auto_apply  # Enable hybrid mode if auto_apply
        )
        
        # Check if monitoring succeeded
        status = monitor_result.get("status")
        if not status or not status.is_completed:
            error = "Session did not complete within timeout"
            context.logger.error(f"❌ {error}")
            return {
                "success": False,
                "error": error,
                "session_ids": session_ids,
                "status": status,
                "workflow": "autonomous"
            }
        
        # STEP 3: Results handling
        if request.auto_apply:
            # Hybrid mode already pulled results
            results_applied = monitor_result.get("results_applied", False)
            changes = monitor_result.get("changes", "")
            
            if results_applied:
                context.logger.info("✅ AUTONOMOUS WORKFLOW COMPLETED SUCCESSFULLY!")
                context.logger.info(f"   Session: {session_id}")
                context.logger.info(f"   Status: {status.state}")
                context.logger.info(f"   Results: Applied to local repository")
                
                return {
                    "success": True,
                    "session_ids": session_ids,
                    "status": status,
                    "results_applied": True,
                    "changes": changes,
                    "workflow": "autonomous"
                }
            else:
                error = monitor_result.get("error", "Failed to apply results")
                context.logger.warning(f"⚠️ Session completed but results not applied: {error}")
                return {
                    "success": True,  # Session completed successfully
                    "session_ids": session_ids,
                    "status": status,
                    "results_applied": False,
                    "error": error,
                    "workflow": "autonomous"
                }
        else:
            # No auto-apply - just report completion
            context.logger.info("✅ Session completed (auto-apply disabled)")
            return {
                "success": True,
                "session_ids": session_ids,
                "status": status,
                "results_applied": False,
                "message": "Use pull_results to retrieve changes",
                "workflow": "autonomous"
            }
    
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
                                "description": "Repository in 'owner/repo' format. Example: 'ShotyCZ/sophia'"
                            },
                            "task": {
                                "type": "string",
                                "description": "Complete task description for Jules. Be specific about what to create/modify. Example: 'Create file sandbox/hello.py with a hello_world() function that prints Hello World'"
                            },
                            "parallel": {
                                "type": "integer",
                                "description": "Number of parallel attempts (1-5). Higher = more solution diversity but slower.",
                                "default": 1,
                                "minimum": 1,
                                "maximum": 5
                            },
                            "auto_apply": {
                                "type": "boolean",
                                "description": "If true, automatically apply Jules results to local repository when completed. If false, just monitor and report completion.",
                                "default": True
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Maximum wait time in seconds (default: 3600 = 1 hour)",
                                "default": 3600
                            },
                            "check_interval": {
                                "type": "integer",
                                "description": "Seconds between progress checks (default: 30)",
                                "default": 30
                            }
                        },
                        "required": ["repo", "task"]
                    }
                }
            }
        ]
