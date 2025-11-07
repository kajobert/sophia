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
        self.jules_plan_validator = None  # NEW: LLM-based plan validation
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

        # Inject Jules plan validator (NEW - Phase 3.8)
        self.jules_plan_validator = all_plugins.get("cognitive_jules_plan_validator")
        if not self.jules_plan_validator:
            self.logger.warning("cognitive_jules_plan_validator not found - using simple keyword validation")

        # Report status
        if self.jules_api_tool and self.jules_cli_tool and self.jules_monitor:
            self.logger.info(
                "✅ Jules Autonomy Plugin ready - HYBRID MODE (API creation + CLI pull)"
            )
            if self.jules_plan_validator:
                self.logger.info("   ✅ LLM-based plan validation enabled")
        elif self.jules_api_tool and self.jules_monitor:
            self.logger.info("⚡ Jules Autonomy Plugin ready - API-ONLY MODE (no local pull)")

    def _enhance_prompt_for_jules(self, sophia_task: str, context: SharedContext) -> str:
        """
        Enhance Sophia's task description for Jules with better structure.
        
        IMPORTANT: Jules has access to:
        - Full GitHub repo (including files in .gitignore if configured in jules.google.com)
        - Secrets configured in jules.google.com UI for this repo
        - Web search, bash commands, file editing
        
        This function ONLY improves prompt clarity, NOT sanitization.
        
        Args:
            sophia_task: Original task from Sophia
            context: Shared context (for logging)
            
        Returns:
            Enhanced prompt with better structure for Jules
            
        Example:
            Input:  "Fix benchmark runner"
            Output: "Task: Fix benchmark runner
                     
                     File: plugins/benchmark_runner.py
                     Issue: [extracted from context]
                     Expected: [clear success criteria]"
        """
        # If task is already well-structured (has "Task:", "File:", etc.), use as-is
        if any(keyword in sophia_task for keyword in ["Task:", "File:", "Issue:", "Expected:"]):
            context.logger.info("📋 Task already well-structured, using as-is")
            return sophia_task
        
        # Otherwise, add minimal structure
        enhanced = f"""Task for Jules AI Agent:

{sophia_task}

IMPORTANT:
- You have access to secrets configured in jules.google.com for this repo
- Use web search if you need documentation or examples
- Run tests to verify your changes work
- Create clear commit messages
"""
        
        return enhanced

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

        # STEP 0: Enhance task prompt for Jules (add structure, not sanitize)
        jules_prompt = self._enhance_prompt_for_jules(request.task, context)
        context.logger.info(f"📝 Jules prompt (enhanced): {jules_prompt[:100]}...")

        # STEP 1: Create Jules session via API
        context.logger.info("📝 STEP 1: Creating Jules session via API...")

        # Convert repo format: "owner/repo" -> "sources/github/owner/repo"
        source = f"sources/github/{request.repo}"

        try:
            jules_session = await self.jules_api_tool.create_session(
                context=context,
                prompt=jules_prompt,  # Use enhanced prompt
                source=source,
                branch="master",  # FIX: repo uses 'master' not 'main'
                auto_pr=False,  # Don't auto-create PR, we'll handle results ourselves
                require_plan_approval=True,  # CRITICAL: Sophia must approve plan first!
            )

            # JulesSession.name format: "sessions/{session_id}"
            session_id = jules_session.name.split("/")[1]
            context.logger.info(f"✅ Created session: {session_id}")

        except Exception as e:
            context.logger.error(f"❌ Failed to create session: {e}")
            return {"success": False, "error": str(e), "workflow": "autonomous"}

        # STEP 1.5: Get and review plan (CRITICAL SAFETY STEP)
        context.logger.info(f"📋 STEP 1.5: Getting Jules plan for review...")
        
        try:
            # Wait a bit for Jules to generate plan
            import asyncio
            await asyncio.sleep(5)
            
            plan_details = self.jules_api_tool.get_plan_details(context, session_id)
            
            if not plan_details.get("has_plan"):
                error = "Jules didn't generate a plan"
                context.logger.error(f"❌ {error}")
                return {
                    "success": False,
                    "error": error,
                    "session_id": session_id,
                    "workflow": "autonomous",
                }
            
            # Extract plan
            plan = plan_details.get("plan", {})
            context.logger.info("📋 Jules Plan received:")
            context.logger.info(f"   {plan}")
            
            # VALIDATE PLAN using LLM (if validator available)
            if self.jules_plan_validator:
                context.logger.info("🔍 Running LLM-based plan validation...")
                
                validation_result = await self.jules_plan_validator.validate_plan(
                    context=context,
                    sophia_task=request.task,  # Original Sophia task
                    jules_plan=plan,
                    session_id=session_id
                )
                
                # Log validation decision
                if validation_result.approved:
                    context.logger.info(
                        f"✅ Plan APPROVED by LLM validator (confidence: {validation_result.confidence:.2f})"
                    )
                    context.logger.info(f"   Reasoning: {validation_result.reasoning}")
                else:
                    error = f"Plan REJECTED by LLM validator: {validation_result.reasoning}"
                    context.logger.error(f"❌ {error}")
                    context.logger.warning(f"   Risks identified: {validation_result.risks}")
                    
                    return {
                        "success": False,
                        "error": error,
                        "session_id": session_id,
                        "plan": plan,
                        "validation": validation_result.model_dump(),
                        "workflow": "autonomous",
                    }
            else:
                # Fallback: Simple keyword-based validation
                context.logger.warning("⚠️  Using fallback keyword validation (LLM validator not available)")
                
                plan_str = str(plan)
                dangerous_keywords = [".env delete", "rm -rf", "DROP TABLE", "DELETE FROM users"]
                
                if any(keyword in plan_str for keyword in dangerous_keywords):
                    error = f"Plan contains dangerous operation: {plan_str[:200]}"
                    context.logger.error(f"❌ {error}")
                    return {
                        "success": False,
                        "error": error,
                        "session_id": session_id,
                        "plan": plan,
                        "workflow": "autonomous",
                    }
            
            # Approve plan
            context.logger.info("✅ Plan approved, submitting approval to Jules...")
            self.jules_api_tool.approve_plan(context, session_id)
            
        except Exception as e:
            context.logger.error(f"❌ Plan review failed: {e}")
            return {
                "success": False,
                "error": f"Plan review failed: {e}",
                "session_id": session_id,
                "workflow": "autonomous",
            }

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

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Cognitive plugin execute method (not used for autonomous workflows).
        
        This plugin is called via delegate_task() method, not execute().
        """
        context.payload["info"] = "Use delegate_task() method for Jules workflows"
        context.payload["available_methods"] = ["delegate_task"]
        return context

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
