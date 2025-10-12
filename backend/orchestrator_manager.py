"""
Orchestrator Manager - Wrapper around NomadOrchestratorV2 for backend API.

This module provides a singleton manager that controls the NomadOrchestratorV2
instance and exposes it to the FastAPI backend in a thread-safe way.
"""

import asyncio
import uuid
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
            await self._orchestrator.start_mission(
                mission_goal=description,
                recover_if_crashed=True
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
            budget_limit=self._orchestrator.budget_tracker.max_cost,
            budget_used=self._orchestrator.budget_tracker.total_cost,
            success=state == State.COMPLETED,
            error=state_data.get("error") if state == State.ERROR else None,
        )
    
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
        
        # Convert call history to API models
        calls = []
        for call in tracker.call_history:
            calls.append(LLMCallCost(
                timestamp=call.get("timestamp", datetime.now()),
                model=call.get("model", "unknown"),
                provider=call.get("provider", "unknown"),
                usage=TokenUsage(
                    prompt_tokens=call.get("prompt_tokens", 0),
                    completion_tokens=call.get("completion_tokens", 0),
                    total_tokens=call.get("total_tokens", 0),
                ),
                cost_usd=call.get("cost", 0.0),
                purpose=call.get("purpose"),
            ))
        
        # Calculate breakdowns
        breakdown_provider: Dict[str, float] = {}
        breakdown_model: Dict[str, float] = {}
        breakdown_purpose: Dict[str, float] = {}
        
        for call in tracker.call_history:
            provider = call.get("provider", "unknown")
            model = call.get("model", "unknown")
            purpose = call.get("purpose", "unknown")
            cost = call.get("cost", 0.0)
            
            breakdown_provider[provider] = breakdown_provider.get(provider, 0.0) + cost
            breakdown_model[model] = breakdown_model.get(model, 0.0) + cost
            breakdown_purpose[purpose] = breakdown_purpose.get(purpose, 0.0) + cost
        
        # Calculate remaining budget
        budget_remaining = None
        budget_percent = None
        if tracker.max_cost:
            budget_remaining = tracker.max_cost - tracker.total_cost
            budget_percent = (tracker.total_cost / tracker.max_cost) * 100
        
        return BudgetResponse(
            mission_id=self._current_mission_id,
            total_spent=tracker.total_cost,
            budget_limit=tracker.max_cost,
            budget_remaining=budget_remaining,
            budget_used_percent=budget_percent,
            total_tokens=tracker.total_tokens,
            total_calls=len(tracker.call_history),
            calls=calls,
            breakdown_by_provider=breakdown_provider,
            breakdown_by_model=breakdown_model,
            breakdown_by_purpose=breakdown_purpose,
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


# Singleton instance
orchestrator_manager = OrchestratorManager()
