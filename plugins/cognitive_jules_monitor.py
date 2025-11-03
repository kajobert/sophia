"""
Cognitive Jules Monitor Plugin
Monitors Jules API sessions and provides autonomous task tracking for Sophie.

Created: 2025-11-03
Purpose: Autonomous monitoring of delegated Jules tasks
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
import time
import logging

logger = logging.getLogger(__name__)


# Request Models
class StartMonitoringRequest(BaseModel):
    """Request to start monitoring a Jules session"""
    session_id: str = Field(..., min_length=1, description="Jules session ID to monitor")
    check_interval: int = Field(default=30, ge=10, le=300, description="Check interval in seconds")
    max_duration: int = Field(default=3600, ge=60, le=86400, description="Maximum monitoring duration in seconds")
    notify_on_completion: bool = Field(default=True, description="Notify when task completes")
    notify_on_error: bool = Field(default=True, description="Notify on errors")


class GetSessionStatusRequest(BaseModel):
    """Request to get current status of monitored session"""
    session_id: str = Field(..., min_length=1)


class MonitorUntilCompletionRequest(BaseModel):
    """Request to monitor session until completion"""
    session_id: str = Field(..., min_length=1, description="Jules session ID to monitor")
    check_interval: int = Field(default=30, ge=10, le=300, description="Check interval in seconds")
    timeout: int = Field(default=3600, ge=60, le=86400, description="Maximum wait time in seconds")


# Response Models
class JulesSessionStatus(BaseModel):
    """Current status of a Jules session"""
    session_id: str
    state: str  # ACTIVE, COMPLETED, FAILED, etc.
    title: Optional[str] = None
    prompt: str
    create_time: Optional[str] = None
    update_time: Optional[str] = None
    last_check: datetime
    is_completed: bool
    is_error: bool
    error_message: Optional[str] = None
    completion_summary: Optional[str] = None


class MonitoringTask(BaseModel):
    """Represents an active monitoring task"""
    session_id: str
    started_at: datetime
    check_interval: int
    max_duration: int
    last_check: datetime
    check_count: int = 0
    status: str = "monitoring"  # monitoring, completed, timeout, error
    last_state: Optional[str] = None


class CognitiveJulesMonitor(BasePlugin):
    """
    Cognitive Jules Monitor Plugin
    
    Provides autonomous monitoring of Jules API sessions, allowing Sophie to:
    - Track progress of delegated tasks
    - Detect completion and errors
    - Read Jules responses and outputs
    - Make autonomous decisions based on Jules status
    """
    
    @property
    def name(self) -> str:
        return "cognitive_jules_monitor"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.active_monitors: Dict[str, MonitoringTask] = {}
        self.jules_tool = None
        self.jules_cli_tool = None  # For hybrid mode
    
    def setup(self, config: dict) -> None:
        """
        Sets up the Jules monitor plugin and injects Jules API tool dependency.

        Args:
            config: Configuration dictionary containing 'plugins' map
        """
        logger.info("Cognitive Jules Monitor initialized")
        
        # Get reference to tool_jules from plugins map
        all_plugins = config.get("plugins", {})
        jules_tool = all_plugins.get("tool_jules")
        jules_cli_tool = all_plugins.get("tool_jules_cli")
        
        if jules_tool:
            self.jules_tool = jules_tool
            logger.info("Jules API tool successfully injected into monitor")
        else:
            logger.warning(
                "tool_jules not found in plugin map. "
                "Monitoring methods will fail until set_jules_tool() is called."
            )
        
        # Inject Jules CLI tool for hybrid mode (optional)
        if jules_cli_tool:
            self.jules_cli_tool = jules_cli_tool
            logger.info("✅ Jules CLI tool injected - HYBRID MODE enabled")
        else:
            logger.info(
                "tool_jules_cli not found. Hybrid mode disabled. "
                "Results auto-pull will not be available."
            )
    
    def set_jules_tool(self, jules_tool):
        """
        Inject Jules API tool dependency.
        
        Args:
            jules_tool: Instance of JulesAPITool plugin
        """
        self.jules_tool = jules_tool
        logger.info("Jules API tool injected into monitor")
    
    def start_monitoring(
        self,
        context: SharedContext,
        session_id: str,
        check_interval: int = 30,
        max_duration: int = 3600,
        notify_on_completion: bool = True,
        notify_on_error: bool = True
    ) -> MonitoringTask:
        """
        Starts monitoring a Jules session.
        
        Args:
            context: Shared context
            session_id: Jules session ID to monitor
            check_interval: How often to check status (seconds, 10-300)
            max_duration: Maximum monitoring time (seconds, 60-86400)
            notify_on_completion: Whether to notify on completion
            notify_on_error: Whether to notify on errors
            
        Returns:
            MonitoringTask with monitoring details
            
        Example:
            >>> monitor.start_monitoring(ctx, "sessions/123", check_interval=60)
            >>> # Monitor will check every 60 seconds
        """
        # Validate input
        try:
            request = StartMonitoringRequest(
                session_id=session_id,
                check_interval=check_interval,
                max_duration=max_duration,
                notify_on_completion=notify_on_completion,
                notify_on_error=notify_on_error
            )
        except Exception as e:
            context.logger.error(f"Invalid start_monitoring parameters: {e}")
            raise ValueError(f"Invalid parameters: {e}")
        
        # Create monitoring task
        now = datetime.now()
        task = MonitoringTask(
            session_id=request.session_id,
            started_at=now,
            check_interval=request.check_interval,
            max_duration=request.max_duration,
            last_check=now,
            check_count=0,
            status="monitoring"
        )
        
        # Store in active monitors
        self.active_monitors[session_id] = task
        
        context.logger.info(
            f"Started monitoring Jules session {session_id} "
            f"(interval: {check_interval}s, max: {max_duration}s)"
        )
        
        return task
    
    def check_session_status(
        self,
        context: SharedContext,
        session_id: str
    ) -> JulesSessionStatus:
        """
        Checks current status of a Jules session.
        
        Args:
            context: Shared context
            session_id: Jules session ID to check
            
        Returns:
            JulesSessionStatus with current session state
            
        Raises:
            ValueError: If session_id is invalid
            RuntimeError: If Jules tool is not available
        """
        # Validate input
        try:
            request = GetSessionStatusRequest(session_id=session_id)
        except Exception as e:
            context.logger.error(f"Invalid session_id: {e}")
            raise ValueError(f"Invalid session_id: {e}")
        
        if not self.jules_tool:
            raise RuntimeError("Jules API tool not available. Call set_jules_tool() first.")
        
        # Get session from Jules API
        try:
            session = self.jules_tool.get_session(context, session_id)
        except Exception as e:
            context.logger.error(f"Failed to get Jules session: {e}")
            raise RuntimeError(f"Failed to get Jules session: {e}")
        
        # Determine completion and error states
        is_completed = session.state in ["COMPLETED", "FINISHED", "DONE"]
        is_error = session.state in ["FAILED", "ERROR"]
        
        # Extract error message if present
        error_message = None
        if is_error and hasattr(session, 'error'):
            error_message = session.error
        
        # Create status response
        status = JulesSessionStatus(
            session_id=session.name,
            state=session.state or "UNKNOWN",
            title=session.title,
            prompt=session.prompt,
            create_time=session.create_time,
            update_time=session.update_time,
            last_check=datetime.now(),
            is_completed=is_completed,
            is_error=is_error,
            error_message=error_message,
            completion_summary=self._extract_completion_summary(session) if is_completed else None
        )
        
        # Update monitoring task if exists
        if session_id in self.active_monitors:
            task = self.active_monitors[session_id]
            task.last_check = datetime.now()
            task.check_count += 1
            task.last_state = session.state
            
            # Update task status
            if is_completed:
                task.status = "completed"
                context.logger.info(f"✅ Jules session {session_id} completed!")
            elif is_error:
                task.status = "error"
                context.logger.warning(f"❌ Jules session {session_id} failed: {error_message}")
        
        return status
    
    def _extract_completion_summary(self, session) -> Optional[str]:
        """
        Extracts completion summary from Jules session.
        
        Args:
            session: Jules session object
            
        Returns:
            Summary string if available
        """
        # Try to extract summary from session data
        # This depends on Jules API response structure
        if hasattr(session, 'summary'):
            return session.summary
        elif hasattr(session, 'result'):
            return str(session.result)
        
        return f"Session completed at {session.update_time}"
    
    def monitor_until_completion(
        self,
        context: SharedContext,
        session_id: str,
        check_interval: int = 30,
        timeout: int = 3600,
        auto_pull: bool = False
    ) -> Dict[str, Any]:
        """
        Monitors a Jules session until completion or timeout.
        
        BLOCKING OPERATION - polls until done.
        HYBRID MODE: If auto_pull=True and CLI tool available, automatically pulls results.
        
        Args:
            context: Shared context
            session_id: Jules session ID to monitor
            check_interval: Seconds between checks (default: 30)
            timeout: Maximum wait time in seconds (default: 3600)
            auto_pull: If True, automatically pull results via CLI when COMPLETED (hybrid mode)
            
        Returns:
            Dict with status and optional results (if auto_pull=True)
            
        Example:
            >>> # Standard API-only mode
            >>> result = monitor.monitor_until_completion(ctx, "sessions/123")
            >>> print(result["status"].state)  # COMPLETED
            
            >>> # HYBRID mode with auto-pull
            >>> result = monitor.monitor_until_completion(ctx, "sessions/123", auto_pull=True)
            >>> print(result["results_applied"])  # True
            >>> print(result["changes"])  # Diff or success message
        """
        # Validate input
        try:
            request = MonitorUntilCompletionRequest(
                session_id=session_id,
                check_interval=check_interval,
                timeout=timeout
            )
        except Exception as e:
            context.logger.error(f"Invalid monitor_until_completion parameters: {e}")
            raise ValueError(f"Invalid parameters: {e}")
        
        start_time = datetime.now()
        max_time = start_time + timedelta(seconds=request.timeout)
        
        mode = "HYBRID (auto-pull enabled)" if auto_pull and self.jules_cli_tool else "API-only"
        context.logger.info(
            f"Monitoring Jules session {request.session_id} until completion "
            f"(timeout: {request.timeout}s, interval: {request.check_interval}s, mode: {mode})"
        )
        
        while datetime.now() < max_time:
            # Check current status via API
            status = self.check_session_status(context, request.session_id)
            
            # Check if completed
            if status.is_completed:
                context.logger.info(f"✅ Session completed: {status.completion_summary}")
                
                # HYBRID MODE: Auto-pull results via CLI
                if auto_pull and self.jules_cli_tool:
                    context.logger.info("🔄 Auto-pulling results via Jules CLI (hybrid mode)...")
                    
                    try:
                        pull_result = self.jules_cli_tool.pull_results(
                            context,
                            session_id=request.session_id,
                            apply=True  # Apply changes to local repo
                        )
                        
                        if pull_result["success"]:
                            context.logger.info("✅ Results pulled and applied via CLI!")
                            return {
                                "status": status,
                                "results_applied": True,
                                "changes": pull_result.get("output", ""),
                                "mode": "hybrid"
                            }
                        else:
                            context.logger.warning(
                                f"⚠️ Failed to pull results: {pull_result.get('error')}"
                            )
                            return {
                                "status": status,
                                "results_applied": False,
                                "error": pull_result.get("error"),
                                "mode": "hybrid"
                            }
                    
                    except Exception as e:
                        context.logger.error(f"❌ Failed to auto-pull results: {e}")
                        return {
                            "status": status,
                            "results_applied": False,
                            "error": str(e),
                            "mode": "hybrid"
                        }
                
                # API-only mode (no auto-pull)
                return {
                    "status": status,
                    "results_applied": False,
                    "mode": "api-only"
                }
            
            # Check if failed
            if status.is_error:
                context.logger.error(f"❌ Session failed: {status.error_message}")
                return {
                    "status": status,
                    "results_applied": False,
                    "error": status.error_message,
                    "mode": "api-only"
                }
            
            # Log current state
            elapsed = (datetime.now() - start_time).total_seconds()
            context.logger.info(
                f"Session {request.session_id} state: {status.state} "
                f"(elapsed: {elapsed:.0f}s)"
            )
            
            # Wait before next check
            time.sleep(request.check_interval)
        
        # Timeout reached
        context.logger.warning(f"⏱️ Monitoring timeout reached for session {request.session_id}")
        status = self.check_session_status(context, request.session_id)
        
        if request.session_id in self.active_monitors:
            self.active_monitors[request.session_id].status = "timeout"
        
        return {
            "status": status,
            "results_applied": False,
            "timeout": True,
            "mode": "api-only"
        }
    
    def list_active_monitors(self, context: SharedContext) -> List[MonitoringTask]:
        """
        Lists all active monitoring tasks.
        
        Args:
            context: Shared context
            
        Returns:
            List of active MonitoringTask objects
        """
        tasks = []
        now = datetime.now()
        
        for session_id, task in self.active_monitors.items():
            # Check if task has timed out
            elapsed = (now - task.started_at).total_seconds()
            if elapsed > task.max_duration and task.status == "monitoring":
                task.status = "timeout"
                context.logger.info(f"Monitoring task {session_id} timed out")
            
            tasks.append(task)
        
        return tasks
    
    def stop_monitoring(self, context: SharedContext, session_id: str) -> bool:
        """
        Stops monitoring a Jules session.
        
        Args:
            context: Shared context
            session_id: Jules session ID
            
        Returns:
            True if stopped, False if not found
        """
        if session_id in self.active_monitors:
            task = self.active_monitors[session_id]
            task.status = "stopped"
            del self.active_monitors[session_id]
            context.logger.info(f"Stopped monitoring session {session_id}")
            return True
        
        return False
    
    def get_monitoring_summary(self, context: SharedContext) -> Dict[str, Any]:
        """
        Gets summary of all monitoring activities.
        
        Args:
            context: Shared context
            
        Returns:
            Dict with monitoring statistics
        """
        active_count = len([t for t in self.active_monitors.values() if t.status == "monitoring"])
        completed_count = len([t for t in self.active_monitors.values() if t.status == "completed"])
        error_count = len([t for t in self.active_monitors.values() if t.status == "error"])
        timeout_count = len([t for t in self.active_monitors.values() if t.status == "timeout"])
        
        return {
            "total_monitors": len(self.active_monitors),
            "active": active_count,
            "completed": completed_count,
            "errors": error_count,
            "timeouts": timeout_count,
            "sessions": list(self.active_monitors.keys())
        }
    
    async def execute(self, context: SharedContext, method_name: str, **kwargs) -> Any:
        """
        Executes a cognitive method dynamically.
        
        Args:
            context: The shared context for the session
            method_name: Name of the method to execute
            **kwargs: Method arguments
            
        Returns:
            Method execution result
        """
        if not hasattr(self, method_name):
            raise ValueError(f"Unknown method: {method_name}")
        
        method = getattr(self, method_name)
        return method(context, **kwargs)

    def get_tool_definitions(self) -> List[dict]:
        """
        Returns the tool definitions for this plugin in JSON Schema format.
        
        Returns:
            List of tool definition dictionaries compatible with OpenAI function calling
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "start_monitoring",
                    "description": "Start monitoring a Jules session for completion. Returns monitoring task details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Jules session ID to monitor (e.g., 'sessions/123456')"
                            },
                            "check_interval": {
                                "type": "integer",
                                "description": "Check interval in seconds (10-300)",
                                "default": 30
                            },
                            "max_duration": {
                                "type": "integer",
                                "description": "Maximum monitoring duration in seconds (60-86400)",
                                "default": 3600
                            },
                            "notify_on_completion": {
                                "type": "boolean",
                                "description": "Notify when task completes",
                                "default": True
                            },
                            "notify_on_error": {
                                "type": "boolean",
                                "description": "Notify on errors",
                                "default": True
                            }
                        },
                        "required": ["session_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_session_status",
                    "description": "Check current status of a Jules session. Returns session state and completion info.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Jules session ID to check (e.g., 'sessions/123456')"
                            }
                        },
                        "required": ["session_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "monitor_until_completion",
                    "description": (
                        "Monitor Jules session until completion or timeout (BLOCKING OPERATION). "
                        "Supports HYBRID MODE: set auto_pull=True to automatically pull and apply results via CLI when completed. "
                        "Polls every check_interval seconds using API, then optionally pulls results via CLI."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Jules session ID to monitor (e.g., 'sessions/123456')"
                            },
                            "check_interval": {
                                "type": "integer",
                                "description": "Seconds between status checks (10-300)",
                                "default": 30
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Maximum wait time in seconds before giving up (60-86400)",
                                "default": 3600
                            },
                            "auto_pull": {
                                "type": "boolean",
                                "description": (
                                    "HYBRID MODE: If True, automatically pull and apply results via Jules CLI when session completes. "
                                    "Requires tool_jules_cli to be available. Changes will be applied to local repository."
                                ),
                                "default": False
                            }
                        },
                        "required": ["session_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_active_monitors",
                    "description": "List all active monitoring tasks. Returns list of MonitoringTask objects.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "stop_monitoring",
                    "description": "Stop monitoring a Jules session. Removes from active monitors.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "Jules session ID to stop monitoring"
                            }
                        },
                        "required": ["session_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_monitoring_summary",
                    "description": "Get summary of all monitoring activities. Returns statistics and status.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
