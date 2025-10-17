"""
Orchestrator Manager - Wrapper around NomadOrchestratorV2 for backend API.

This module provides a singleton manager that controls the NomadOrchestratorV2
instance and exposes it to the FastAPI backend in a thread-safe way.
"""

import asyncio
import uuid
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from threading import Lock
import logging

from core.nomad_orchestrator_v2 import NomadOrchestratorV2
from core.state_manager import State
from backend.models import (
    StateEnum,
    MissionResponse,
    PlanResponse,
    PlanStep,
    ExecutionStep,
    BudgetResponse,
    LLMCallCost,
    TokenUsage,
    HealthMetrics,
    LogEntry,
    LogLevelEnum,
)

logger = logging.getLogger(__name__)


class OrchestratorManager:
    """
    Singleton manager for NomadOrchestratorV2.
    
    Manages:
    - Single orchestrator instance
    - Mission lifecycle
    - Real-time event streaming (WebSocket)
    - State queries
    - Thread-safe access
    """
    
    _instance: Optional['OrchestratorManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize manager (only once)."""
        if self._initialized:
            return
        
        self._orchestrator: Optional[NomadOrchestratorV2] = None
        self._current_mission_id: Optional[str] = None
        self._current_mission_description: Optional[str] = None
        self._mission_created_at: Optional[datetime] = None
        self._mission_started_at: Optional[datetime] = None
        self._mission_completed_at: Optional[datetime] = None
        self._mission_task: Optional[asyncio.Task] = None
        
        # Mission control flags
        self._is_paused: bool = False
        self._is_cancelled: bool = False
        self._cancel_reason: Optional[str] = None
        
        # Event callbacks for WebSocket streaming
        self._event_callbacks: List[Callable] = []
        
        # Execution history
        self._execution_history: List[ExecutionStep] = []
        
        # Log buffer
        self._log_buffer: List[LogEntry] = []
        self._max_log_buffer = 1000
        
        self._initialized = True
        logger.info("OrchestratorManager initialized")
    
    async def initialize_orchestrator(
        self,
        project_root: str = ".",
        max_tokens: int = 100000,
        max_time_seconds: int = 3600,
    ) -> None:
        """
        Initialize the orchestrator instance.
        
        Args:
            project_root: Project root path
            max_tokens: Maximum tokens for mission
            max_time_seconds: Maximum time for mission (seconds)
        """
        if self._orchestrator is not None:
            logger.warning("Orchestrator already initialized, skipping")
            return
        
        self._orchestrator = NomadOrchestratorV2(
            project_root=project_root,
            max_tokens=max_tokens,
            max_time_seconds=max_time_seconds,
        )
        await self._orchestrator.initialize()
        logger.info("NomadOrchestratorV2 initialized")
    
    def register_event_callback(self, callback: Callable) -> None:
        """Register callback for real-time events (WebSocket)."""
        self._event_callbacks.append(callback)
        logger.debug(f"Registered event callback: {callback}")
    
    def unregister_event_callback(self, callback: Callable) -> None:
        """Unregister event callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)
            logger.debug(f"Unregistered event callback: {callback}")
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit event to all registered callbacks."""
        event = {
            "type": event_type,
            "timestamp": datetime.now(),
            "mission_id": self._current_mission_id,
            "data": data
        }
        
        for callback in self._event_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    def _add_log(
        self,
        level: LogLevelEnum,
        source: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add log entry to buffer."""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            source=source,
            message=message,
            metadata=metadata or {}
        )
        
        self._log_buffer.append(entry)
        
        # Trim buffer if too large
        if len(self._log_buffer) > self._max_log_buffer:
            self._log_buffer = self._log_buffer[-self._max_log_buffer:]
        
        # Emit log event
        asyncio.create_task(
            self._emit_event("log_stream", entry.model_dump())
        )
    
    async def create_mission(
        self,
        description: str,
        max_steps: int = 50,
        budget_limit: Optional[float] = None,
    ) -> MissionResponse:
        """
        Create and start a new mission.
        
        Args:
            description: Mission description/goal
            max_steps: Maximum steps
            budget_limit: Budget limit in USD
        
        Returns:
            MissionResponse with mission details
        
        Raises:
            RuntimeError: If mission is already running
        """
        if self._mission_task and not self._mission_task.done():
            raise RuntimeError("Mission already running")
        
        if self._orchestrator is None:
            raise RuntimeError("Orchestrator not initialized")
        
        # Generate mission ID
        self._current_mission_id = f"mission_{uuid.uuid4().hex[:8]}"
        self._current_mission_description = description
        self._mission_created_at = datetime.now()
        self._mission_started_at = None
        self._mission_completed_at = None
        self._execution_history = []
        self._log_buffer = []
        
        # Set budget limit if provided
        if budget_limit is not None:
            self._orchestrator.budget_tracker.max_cost = budget_limit
        
        self._add_log(
            LogLevelEnum.INFO,
            "orchestrator_manager",
            f"Mission created: {description}",
            {"mission_id": self._current_mission_id}
        )
        
        # Start mission in background
        self._mission_task = asyncio.create_task(
            self._run_mission(description)
        )
        
        return self.get_mission_status()
    
    async def _run_mission(self, description: str) -> None:
        """
        Run mission (internal).
        
        This runs in a background task and emits events via WebSocket.
        """
        try:
            self._mission_started_at = datetime.now()
            self._add_log(
                LogLevelEnum.INFO,
                "orchestrator",
                f"Mission started: {description}"
            )
            
            await self._emit_event("state_update", self.get_state().model_dump())
            
            # Run the mission
            await self._orchestrator.execute_mission(
                mission_goal=description
            )
            
            self._mission_completed_at = datetime.now()
            self._add_log(
                LogLevelEnum.INFO,
                "orchestrator",
                "Mission completed successfully"
            )
            
        except Exception as e:
            logger.error(f"Mission failed: {e}", exc_info=True)
            self._add_log(
                LogLevelEnum.ERROR,
                "orchestrator",
                f"Mission failed: {str(e)}",
                {"error": str(e)}
            )
            await self._emit_event("error", {"error": str(e)})
        
        finally:
            await self._emit_event("state_update", self.get_state().model_dump())
    
    def get_mission_status(self) -> MissionResponse:
        """Get current mission status."""
        if self._orchestrator is None or self._current_mission_id is None:
            raise RuntimeError("No active mission")
        
        state = self._orchestrator.state_manager.get_state()
        state_data = self._orchestrator.state_manager.state_data
        
        return MissionResponse(
            mission_id=self._current_mission_id,
            description=self._current_mission_description or "",
            state=self._map_state(state),
            created_at=self._mission_created_at or datetime.now(),
            started_at=self._mission_started_at,
            completed_at=self._mission_completed_at,
            max_steps=50,  # TODO: Get from orchestrator
            current_step=state_data.get("current_step", 0),
            budget_limit=float(self._orchestrator.budget_tracker.max_tokens),
            budget_used=float(self._orchestrator.budget_tracker.tokens_used),
            success=state == State.COMPLETED,
            error=state_data.get("error") if state == State.ERROR else None,
        )
    
    async def pause_mission(self) -> Dict[str, Any]:
        """
        Pause current mission execution.
        
        Returns:
            Success message with status
        
        Raises:
            RuntimeError: If no active mission or mission cannot be paused
        """
        if self._orchestrator is None or self._current_mission_id is None:
            raise RuntimeError("No active mission to pause")
        
        state = self._orchestrator.state_manager.get_state()
        
        # Validate state - can only pause during execution
        if state not in [State.EXECUTING_STEP, State.AWAITING_TOOL_RESULT, State.PLANNING]:
            raise RuntimeError(
                f"Cannot pause mission in state: {state.value}. "
                f"Only missions in EXECUTING_STEP, AWAITING_TOOL_RESULT, or PLANNING can be paused."
            )
        
        if self._is_paused:
            raise RuntimeError("Mission is already paused")
        
        self._is_paused = True
        
        self._add_log(
            LogLevelEnum.INFO,
            "orchestrator_manager",
            f"Mission {self._current_mission_id} paused",
            {"state": state.value}
        )
        
        await self._emit_event("mission_paused", {
            "mission_id": self._current_mission_id,
            "paused_state": state.value,
        })
        
        return {
            "success": True,
            "message": "Mission paused successfully",
            "mission_id": self._current_mission_id,
            "paused_at_state": state.value,
        }
    
    async def resume_mission(self) -> Dict[str, Any]:
        """
        Resume paused mission execution.
        
        Returns:
            Success message with status
        
        Raises:
            RuntimeError: If no active mission or mission is not paused
        """
        if self._orchestrator is None or self._current_mission_id is None:
            raise RuntimeError("No active mission to resume")
        
        if not self._is_paused:
            raise RuntimeError("Mission is not paused")
        
        if self._is_cancelled:
            raise RuntimeError("Cannot resume cancelled mission")
        
        state = self._orchestrator.state_manager.get_state()
        
        self._is_paused = False
        
        self._add_log(
            LogLevelEnum.INFO,
            "orchestrator_manager",
            f"Mission {self._current_mission_id} resumed",
            {"state": state.value}
        )
        
        await self._emit_event("mission_resumed", {
            "mission_id": self._current_mission_id,
            "resumed_from_state": state.value,
        })
        
        return {
            "success": True,
            "message": "Mission resumed successfully",
            "mission_id": self._current_mission_id,
            "current_state": state.value,
        }
    
    async def cancel_mission(self, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel current mission execution.
        
        Args:
            reason: Optional cancellation reason
        
        Returns:
            Success message with status
        
        Raises:
            RuntimeError: If no active mission
        """
        if self._orchestrator is None or self._current_mission_id is None:
            raise RuntimeError("No active mission to cancel")
        
        if self._is_cancelled:
            raise RuntimeError("Mission is already cancelled")
        
        state = self._orchestrator.state_manager.get_state()
        
        self._is_cancelled = True
        self._cancel_reason = reason or "User requested cancellation"
        
        # If mission is running, cancel the task
        if self._mission_task and not self._mission_task.done():
            self._mission_task.cancel()
            logger.info(f"Cancelled mission task: {self._current_mission_id}")
        
        self._add_log(
            LogLevelEnum.WARNING,
            "orchestrator_manager",
            f"Mission {self._current_mission_id} cancelled: {self._cancel_reason}",
            {"state": state.value}
        )
        
        await self._emit_event("mission_cancelled", {
            "mission_id": self._current_mission_id,
            "cancelled_at_state": state.value,
            "reason": self._cancel_reason,
        })
        
        # Mark mission as completed with cancellation
        self._mission_completed_at = datetime.now()
        
        return {
            "success": True,
            "message": "Mission cancelled successfully",
            "mission_id": self._current_mission_id,
            "cancelled_at_state": state.value,
            "reason": self._cancel_reason,
        }
    
    def is_paused(self) -> bool:
        """Check if mission is paused."""
        return self._is_paused
    
    def is_cancelled(self) -> bool:
        """Check if mission is cancelled."""
        return self._is_cancelled
    
    def get_state(self) -> Any:
        """Get current state details."""
        from backend.models import StateResponse
        
        if self._orchestrator is None:
            return StateResponse(
                mission_id=None,
                state=StateEnum.IDLE,
                state_entered_at=datetime.now(),
                state_duration=0.0,
            )
        
        state = self._orchestrator.state_manager.get_state()
        state_data = self._orchestrator.state_manager.state_data
        state_history = self._orchestrator.state_manager.state_history
        
        # Get previous state
        previous_state = None
        if len(state_history) >= 2:
            prev_state_str = state_history[-2].get("state")
            if prev_state_str and isinstance(prev_state_str, str):
                from core.state_manager import State
                try:
                    previous_state = State(prev_state_str)
                except ValueError:
                    previous_state = None
        
        # Calculate duration
        entered_at = state_data.get("entered_at", datetime.now())
        if isinstance(entered_at, str):
            entered_at = datetime.fromisoformat(entered_at)
        elif not isinstance(entered_at, datetime):
            entered_at = datetime.now()
        duration = (datetime.now() - entered_at).total_seconds()
        
        # Get valid transitions - hardcoded to avoid circular import
        can_transition_to = []  # TODO: Get from StateManager.VALID_TRANSITIONS
        
        return StateResponse(
            mission_id=self._current_mission_id,
            state=self._map_state(state),
            previous_state=self._map_state(previous_state) if previous_state else None,
            state_entered_at=entered_at,
            state_duration=duration,
            can_transition_to=can_transition_to,
            metadata=state_data,
        )
    
    def get_plan(self) -> PlanResponse:
        """Get current mission plan."""
        if self._orchestrator is None or self._current_mission_id is None:
            raise RuntimeError("No active mission")
        
        plan = self._orchestrator.plan_manager.get_plan()
        
        # Convert plan to steps
        steps = []
        if plan and "steps" in plan:
            for i, step in enumerate(plan["steps"], 1):
                steps.append(PlanStep(
                    step_number=i,
                    description=step.get("description", ""),
                    status=step.get("status", "pending"),
                    dependencies=step.get("dependencies", []),
                    started_at=None,  # TODO: Track this
                    completed_at=None,
                ))
        
        completed = sum(1 for s in steps if s.status == "completed")
        
        return PlanResponse(
            mission_id=self._current_mission_id,
            plan_text=plan.get("plan_text") if plan else None,
            steps=steps,
            total_steps=len(steps),
            completed_steps=completed,
            current_step=completed + 1 if completed < len(steps) else None,
        )
    
    def get_budget(self) -> BudgetResponse:
        """Get budget information."""
        if self._orchestrator is None:
            return BudgetResponse(
                mission_id=None,
                total_spent=0.0,
                total_tokens=0,
                total_calls=0,
            )
        
        tracker = self._orchestrator.budget_tracker
        
        # BudgetTracker uses tokens, not USD cost
        # Convert step_costs to API format
        calls = []
        total_tokens = tracker.tokens_used
        
        for step_id, step_data in tracker.step_costs.items():
            # Create LLMCallCost from step data
            calls.append(LLMCallCost(
                timestamp=datetime.fromtimestamp(step_data.get("timestamp", time.time())),
                model="unknown",  # BudgetTracker doesn't store model
                provider="unknown",  # BudgetTracker doesn't store provider
                usage=TokenUsage(
                    prompt_tokens=0,  # Not tracked separately
                    completion_tokens=0,  # Not tracked separately
                    total_tokens=step_data.get("tokens", 0),
                ),
                cost_usd=0.0,  # BudgetTracker doesn't track USD cost
                purpose=step_data.get("description", f"Step {step_id}"),
            ))
        
        # Calculate budget remaining
        budget_remaining = None
        budget_percent = None
        if tracker.max_tokens:
            budget_remaining = float(tracker.max_tokens - tracker.tokens_used)
            budget_percent = (tracker.tokens_used / tracker.max_tokens) * 100
        
        return BudgetResponse(
            mission_id=self._current_mission_id,
            total_spent=0.0,  # BudgetTracker doesn't track USD
            budget_limit=float(tracker.max_tokens) if tracker.max_tokens else None,
            budget_remaining=budget_remaining,
            budget_used_percent=budget_percent,
            total_tokens=total_tokens,
            total_calls=len(tracker.step_costs),
            calls=calls,
            breakdown_by_provider={},  # Not tracked
            breakdown_by_model={},  # Not tracked
            breakdown_by_purpose={},  # Not tracked
        )
    
    def get_logs(
        self,
        level: Optional[LogLevelEnum] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[LogEntry]:
        """Get logs with optional filtering."""
        logs = self._log_buffer
        
        # Filter by level
        if level:
            logs = [log for log in logs if log.level == level]
        
        # Filter by source
        if source:
            logs = [log for log in logs if log.source == source]
        
        # Limit
        return logs[-limit:]
    
    def get_execution_history(self) -> List[ExecutionStep]:
        """Get execution history."""
        return self._execution_history
    
    def get_health_metrics(self) -> HealthMetrics:
        """Get system health metrics."""
        import psutil
        import time
        
        process = psutil.Process()
        
        return HealthMetrics(
            cpu_percent=process.cpu_percent(interval=0.1),
            memory_percent=process.memory_percent(),
            memory_available_mb=psutil.virtual_memory().available / (1024 * 1024),
            disk_percent=psutil.disk_usage('/').percent,
            disk_available_gb=psutil.disk_usage('/').free / (1024 * 1024 * 1024),
            open_file_descriptors=len(process.open_files()),
            uptime_seconds=time.time() - process.create_time(),
        )
    
    @staticmethod
    def _map_state(state: Optional[State]) -> StateEnum:
        """Map internal State to API StateEnum."""
        if state is None:
            return StateEnum.IDLE
        
        mapping = {
            State.IDLE: StateEnum.IDLE,
            State.PLANNING: StateEnum.PLANNING,
            State.EXECUTING_STEP: StateEnum.EXECUTING_STEP,
            State.AWAITING_TOOL_RESULT: StateEnum.AWAITING_TOOL_RESULT,
            State.REFLECTION: StateEnum.REFLECTION,
            State.RESPONDING: StateEnum.RESPONDING,
            State.COMPLETED: StateEnum.COMPLETED,
            State.ERROR: StateEnum.ERROR,
        }
        return mapping.get(state, StateEnum.IDLE)
    
    async def shutdown(self) -> None:
        """Shutdown orchestrator gracefully."""
        if self._mission_task and not self._mission_task.done():
            self._mission_task.cancel()
            try:
                await self._mission_task
            except asyncio.CancelledError:
                pass
        
        if self._orchestrator:
            await self._orchestrator.mcp_client.shutdown_servers()
        
        logger.info("OrchestratorManager shutdown complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregated statistics.
        
        Returns:
            Statistics including total missions, success rate, cost, etc.
        """
        if self._orchestrator is None:
            return {
                "total_missions": 0,
                "completed_missions": 0,
                "failed_missions": 0,
                "success_rate": 0.0,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "average_mission_duration": 0.0,
                "current_mission": None,
            }
        
        # Get budget info
        budget = self.get_budget()
        
        # Calculate mission stats (simplified - in real implementation, track history)
        has_mission = self._current_mission_id is not None
        is_completed = False
        is_failed = False
        
        if has_mission:
            state = self._orchestrator.state_manager.get_state()
            is_completed = state == State.COMPLETED
            is_failed = state == State.ERROR
        
        total_missions = 1 if has_mission else 0
        completed = 1 if is_completed else 0
        failed = 1 if is_failed else 0
        
        success_rate = (completed / total_missions * 100) if total_missions > 0 else 0.0
        
        # Calculate average duration
        avg_duration = 0.0
        if self._mission_started_at and is_completed and self._mission_completed_at:
            duration = (self._mission_completed_at - self._mission_started_at).total_seconds()
            avg_duration = duration
        
        return {
            "total_missions": total_missions,
            "completed_missions": completed,
            "failed_missions": failed,
            "success_rate": round(success_rate, 2),
            "total_cost_usd": budget.total_spent,
            "total_tokens": budget.total_tokens,
            "total_llm_calls": budget.total_calls,
            "average_mission_duration": round(avg_duration, 2),
            "current_mission": {
                "mission_id": self._current_mission_id,
                "description": self._current_mission_description,
                "state": self._map_state(self._orchestrator.state_manager.get_state()).value,
                "is_paused": self._is_paused,
                "is_cancelled": self._is_cancelled,
            } if has_mission else None,
            "uptime_seconds": (datetime.now() - self._mission_created_at).total_seconds() if self._mission_created_at else 0,
        }
    
    def get_models(self) -> Dict[str, Any]:
        """
        Get available LLM models with metadata.
        
        Returns:
            Dictionary of available models with pricing and capabilities
        """
        if self._orchestrator is None:
            return {
                "models": [],
                "total": 0,
                "current_model": None,
            }
        
        # Get models from LLM manager
        llm_manager = self._orchestrator.llm_manager
        
        models = []
        
        # Add configured models from config
        for model_name, config in llm_manager.models_config.items():
            # Determine provider
            provider = "gemini" if "gemini" in model_name.lower() else "openrouter"
            
            # Get pricing from llm_adapters if available
            pricing = None
            if provider == "openrouter":
                try:
                    from core.llm_adapters import PRICING
                    if model_name in PRICING:
                        pricing = PRICING[model_name]
                except ImportError:
                    pass
            
            model_info = {
                "name": model_name,
                "provider": provider,
                "config": config,
                "pricing": pricing,
                "available": True,  # Assume available unless we check
            }
            models.append(model_info)
        
        # Get current model
        current_model = llm_manager.default_model_name
        
        return {
            "models": models,
            "total": len(models),
            "current_model": current_model,
            "aliases": llm_manager.aliases,
        }
    
    def get_available_models(self) -> list:
        """
        Get available LLM models (simple list format).
        
        Alias for get_models() that returns just the models list.
        Used by some API endpoints and tests.
        
        Returns:
            List of model dictionaries
        """
        full_data = self.get_models()
        return full_data.get("models", [])


# Singleton instance
orchestrator_manager = OrchestratorManager()
