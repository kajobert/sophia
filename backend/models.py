"""
Pydantic models for Nomad Backend API.

This module defines all request/response models used by the FastAPI backend.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class StateEnum(str, Enum):
    """Mission state enum (matching core.state_manager.State)."""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING_STEP = "executing_step"
    AWAITING_TOOL_RESULT = "awaiting_tool_result"
    REFLECTION = "reflection"
    RESPONDING = "responding"
    COMPLETED = "completed"
    ERROR = "error"


class ReflectionActionEnum(str, Enum):
    """Reflection action enum (matching core.reflection_engine)."""
    RETRY = "retry"
    RETRY_MODIFIED = "retry_modified"
    REPLANNING = "replanning"
    ASK_USER = "ask_user"
    SKIP_STEP = "skip_step"


class LogLevelEnum(str, Enum):
    """Log level enum."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# Mission Models
# ============================================================================

class MissionCreateRequest(BaseModel):
    """Request to create and start a new mission."""
    description: str = Field(..., description="Mission description/goal")
    max_steps: Optional[int] = Field(None, description="Maximum steps (default: 50)")
    budget_limit: Optional[float] = Field(None, description="Budget limit in USD")
    
    model_config = {"json_schema_extra": {
        "example": {
            "description": "Create a simple REST API with FastAPI",
            "max_steps": 30,
            "budget_limit": 1.0
        }
    }}


class MissionResponse(BaseModel):
    """Response with mission details."""
    mission_id: str
    description: str
    state: StateEnum
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    max_steps: int
    current_step: int
    budget_limit: Optional[float] = None
    budget_used: float
    success: Optional[bool] = None
    error: Optional[str] = None


class MissionListResponse(BaseModel):
    """Response with list of missions."""
    missions: List[MissionResponse]
    total: int


class MissionControlRequest(BaseModel):
    """Request to control mission execution."""
    action: str = Field(..., description="Action: pause, resume, cancel")
    
    model_config = {"json_schema_extra": {
        "example": {"action": "pause"}
    }}


# ============================================================================
# Plan Models
# ============================================================================

class PlanStep(BaseModel):
    """Single plan step."""
    step_number: int
    description: str
    status: str  # "pending", "in_progress", "completed", "failed", "skipped"
    dependencies: List[int] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class PlanResponse(BaseModel):
    """Response with mission plan."""
    mission_id: str
    plan_text: Optional[str] = None
    steps: List[PlanStep] = Field(default_factory=list)
    total_steps: int
    completed_steps: int
    current_step: Optional[int] = None


# ============================================================================
# Execution Models
# ============================================================================

class ToolCall(BaseModel):
    """Tool call information."""
    tool_name: str
    arguments: Dict[str, Any]
    timestamp: datetime


class ToolResult(BaseModel):
    """Tool execution result."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float  # seconds
    timestamp: datetime


class ExecutionStep(BaseModel):
    """Single execution step."""
    step_number: int
    description: str
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[ToolResult] = None
    llm_thinking: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExecutionHistoryResponse(BaseModel):
    """Response with execution history."""
    mission_id: str
    steps: List[ExecutionStep]
    total_steps: int


# ============================================================================
# State Models
# ============================================================================

class StateResponse(BaseModel):
    """Response with current state."""
    mission_id: Optional[str] = None
    state: StateEnum
    previous_state: Optional[StateEnum] = None
    state_entered_at: datetime
    state_duration: float  # seconds
    can_transition_to: List[StateEnum] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StateTransitionRequest(BaseModel):
    """Request to transition state (debug only)."""
    new_state: StateEnum
    reason: Optional[str] = None


# ============================================================================
# Budget Models
# ============================================================================

class TokenUsage(BaseModel):
    """Token usage details."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMCallCost(BaseModel):
    """Single LLM call cost."""
    timestamp: datetime
    model: str
    provider: str
    usage: TokenUsage
    cost_usd: float
    purpose: Optional[str] = None  # "planning", "execution", "reflection"


class BudgetResponse(BaseModel):
    """Response with budget information."""
    mission_id: Optional[str] = None
    total_spent: float  # USD
    budget_limit: Optional[float] = None  # USD
    budget_remaining: Optional[float] = None  # USD
    budget_used_percent: Optional[float] = None
    total_tokens: int
    total_calls: int
    calls: List[LLMCallCost] = Field(default_factory=list)
    breakdown_by_provider: Dict[str, float] = Field(default_factory=dict)
    breakdown_by_model: Dict[str, float] = Field(default_factory=dict)
    breakdown_by_purpose: Dict[str, float] = Field(default_factory=dict)


# ============================================================================
# Log Models
# ============================================================================

class LogEntry(BaseModel):
    """Single log entry."""
    timestamp: datetime
    level: LogLevelEnum
    source: str  # "orchestrator", "llm", "tool", "state_manager"
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LogQueryRequest(BaseModel):
    """Request to query logs."""
    level: Optional[LogLevelEnum] = None
    source: Optional[str] = None
    since: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)


class LogResponse(BaseModel):
    """Response with logs."""
    logs: List[LogEntry]
    total: int


# ============================================================================
# Health Models
# ============================================================================

class HealthMetrics(BaseModel):
    """System health metrics."""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_percent: float
    disk_available_gb: float
    open_file_descriptors: int
    uptime_seconds: float


class HealthStatus(BaseModel):
    """Health status."""
    status: str  # "healthy", "degraded", "unhealthy"
    checks: Dict[str, bool] = Field(default_factory=dict)
    metrics: HealthMetrics
    issues: List[str] = Field(default_factory=list)
    timestamp: datetime


# ============================================================================
# WebSocket Models
# ============================================================================

class WSMessage(BaseModel):
    """WebSocket message base."""
    type: str
    timestamp: datetime
    mission_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class WSStateUpdate(WSMessage):
    """WebSocket state update."""
    type: str = "state_update"
    data: Dict[str, Any]  # StateResponse as dict


class WSLogStream(WSMessage):
    """WebSocket log stream."""
    type: str = "log_stream"
    data: Dict[str, Any]  # LogEntry as dict


class WSLLMThinking(WSMessage):
    """WebSocket LLM thinking stream."""
    type: str = "llm_thinking"
    data: Dict[str, str]  # {"content": str, "model": str}


class WSToolExecution(WSMessage):
    """WebSocket tool execution update."""
    type: str = "tool_execution"
    data: Dict[str, Any]  # ToolCall or ToolResult as dict


class WSPlanUpdate(WSMessage):
    """WebSocket plan update."""
    type: str = "plan_update"
    data: Dict[str, Any]  # PlanResponse as dict


class WSBudgetUpdate(WSMessage):
    """WebSocket budget update."""
    type: str = "budget_update"
    data: Dict[str, Any]  # BudgetResponse as dict


# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    mission_id: Optional[str] = None


# ============================================================================
# Session Models
# ============================================================================

class SessionInfo(BaseModel):
    """Session information."""
    session_id: str
    started_at: datetime
    missions_completed: int
    total_budget_spent: float
    uptime_seconds: float


class SessionListResponse(BaseModel):
    """Response with session list."""
    sessions: List[SessionInfo]
    current_session: Optional[str] = None
    total: int
