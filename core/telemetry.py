"""Lightweight runtime telemetry for Sophia's command interfaces.

This module keeps in-memory aggregates about LLM usage, API cost,
active asynchronous tasks, and recent system events so that rich
terminal dashboards can render real-time status without querying
multiple plugins.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from threading import Lock
from typing import Deque, Dict, List, Literal, Optional

from core.events import Event, EventType


@dataclass
class ProviderStats:
    """Aggregated metrics for a single model provider."""

    name: str
    mode: Literal["online", "offline", "hybrid"]
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class TaskRecord:
    """Snapshot of a task managed by the async queue."""

    task_id: str
    name: str
    status: str
    source: str = "task_queue"
    priority: Optional[str] = None
    worker_id: Optional[int] = None
    duration: Optional[float] = None
    started_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EventLogEntry:
    """Single high-level event for the activity feed."""

    timestamp: datetime
    level: str
    message: str
    source: str


@dataclass
class TelemetrySnapshot:
    """Serializable view that dashboards or APIs can consume."""

    generated_at: datetime
    uptime_seconds: float
    phase: str
    phase_detail: str
    runtime_mode: str
    total_calls: int
    total_failures: int
    total_tokens_prompt: int
    total_tokens_completion: int
    total_cost_usd: float
    last_call_at: Optional[datetime]
    online_calls: int
    offline_calls: int
    hybrid_calls: int
    online_tokens: int
    offline_tokens: int
    hybrid_tokens: int
    provider_stats: List[ProviderStats]
    tasks: List[TaskRecord]
    recent_events: List[EventLogEntry]

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-serialisable dictionary."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "phase": self.phase,
            "phase_detail": self.phase_detail,
            "runtime_mode": self.runtime_mode,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_tokens_prompt": self.total_tokens_prompt,
            "total_tokens_completion": self.total_tokens_completion,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "last_call_at": self.last_call_at.isoformat() if self.last_call_at else None,
            "online_calls": self.online_calls,
            "offline_calls": self.offline_calls,
            "hybrid_calls": self.hybrid_calls,
            "online_tokens": self.online_tokens,
            "offline_tokens": self.offline_tokens,
            "hybrid_tokens": self.hybrid_tokens,
            "provider_stats": [
                {
                    **asdict(stat),
                    "total_tokens": stat.total_tokens,
                }
                for stat in self.provider_stats
            ],
            "tasks": [
                {
                    **asdict(task),
                    "updated_at": task.updated_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                }
                for task in self.tasks
            ],
            "recent_events": [
                {
                    "timestamp": entry.timestamp.isoformat(),
                    "level": entry.level,
                    "message": entry.message,
                    "source": entry.source,
                }
                for entry in self.recent_events
            ],
        }


class TelemetryHub:
    """Thread-safe aggregation of runtime metrics."""

    _TASK_LIMIT = 50

    def __init__(self) -> None:
        self._lock = Lock()
        self._start_time = datetime.now(timezone.utc)
        self._phase = "BOOT"
        self._phase_detail = "Kernel initialization sequence"
        self._runtime_mode = "legacy"
        self._provider_stats: Dict[str, ProviderStats] = {}
        self._tasks: Dict[str, TaskRecord] = {}
        self._recent_events: Deque[EventLogEntry] = deque(maxlen=50)
        self._total_calls = 0
        self._total_failures = 0
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._total_cost = 0.0
        self._last_call_at: Optional[datetime] = None
        self._mode_counts = {"online": 0, "offline": 0, "hybrid": 0}
        self._mode_tokens = {"online": 0, "offline": 0, "hybrid": 0}
        self._event_bus = None

    def set_runtime_mode(self, mode: str) -> None:
        """Record whether Sophia runs in event-driven or classic mode."""
        with self._lock:
            self._runtime_mode = mode
            self._recent_events.append(
                EventLogEntry(
                    timestamp=datetime.now(timezone.utc),
                    level="info",
                    message=f"Runtime mode set to {mode}",
                    source="kernel",
                )
            )

    def update_phase(self, phase: str, detail: str = "") -> None:
        """Update the current high-level phase (planning, executing, ...)."""
        with self._lock:
            self._phase = phase
            self._phase_detail = detail
            self._recent_events.append(
                EventLogEntry(
                    timestamp=datetime.now(timezone.utc),
                    level="info",
                    message=f"Phase → {phase}: {detail}".strip(),
                    source="kernel",
                )
            )

    def push_event(self, level: str, message: str, source: str = "system") -> None:
        """Append an arbitrary message to the activity log."""
        with self._lock:
            self._recent_events.append(
                EventLogEntry(
                    timestamp=datetime.now(timezone.utc),
                    level=level,
                    message=message,
                    source=source,
                )
            )

    def record_llm_call(
        self,
        *,
        provider: str,
        mode: Literal["online", "offline", "hybrid"],
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        model: Optional[str] = None,
    ) -> None:
        """Track a successful LLM invocation."""
        with self._lock:
            stats = self._provider_stats.setdefault(
                provider,
                ProviderStats(name=provider, mode=mode),
            )
            stats.calls += 1
            stats.mode = mode
            stats.prompt_tokens += prompt_tokens
            stats.completion_tokens += completion_tokens
            stats.cost_usd += cost_usd

            self._total_calls += 1
            self._prompt_tokens += prompt_tokens
            self._completion_tokens += completion_tokens
            self._total_cost += cost_usd
            self._last_call_at = datetime.now(timezone.utc)
            self._mode_counts[mode] += 1
            self._mode_tokens[mode] += prompt_tokens + completion_tokens

            model_label = model or provider
            self._recent_events.append(
                EventLogEntry(
                    timestamp=self._last_call_at,
                    level="info",
                    message=(
                        f"LLM {model_label} · {prompt_tokens + completion_tokens} tok · ${cost_usd:.4f}"
                    ),
                    source=provider,
                )
            )

    def record_llm_error(
        self,
        *,
        provider: str,
        mode: Literal["online", "offline", "hybrid"],
        reason: str,
    ) -> None:
        """Track a failed LLM invocation."""
        with self._lock:
            self._total_failures += 1
            self._recent_events.append(
                EventLogEntry(
                    timestamp=datetime.now(timezone.utc),
                    level="error",
                    message=f"LLM failure ({provider}): {reason}",
                    source=provider,
                )
            )

    def attach_event_bus(self, event_bus) -> None:
        """Subscribe to task-related events for richer insights."""
        if not event_bus:
            return
        self._event_bus = event_bus
        for event_type in (
            EventType.TASK_CREATED,
            EventType.TASK_STARTED,
            EventType.TASK_PROGRESS,
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED,
            EventType.TASK_CANCELLED,
            EventType.SYSTEM_ERROR,
        ):
            event_bus.subscribe(event_type, self._handle_event)

    async def _handle_event(self, event: Event) -> None:
        self._ingest_event(event)

    def _ingest_event(self, event: Event) -> None:
        if event.event_type in {
            EventType.TASK_CREATED,
            EventType.TASK_STARTED,
            EventType.TASK_PROGRESS,
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED,
            EventType.TASK_CANCELLED,
        }:
            self._update_task_record(event)
        elif event.event_type == EventType.SYSTEM_ERROR:
            self.push_event("error", event.data.get("error", "System error"), event.source)

    def _update_task_record(self, event: Event) -> None:
        data = event.data or {}
        task_id = data.get("task_id") or data.get("id")
        if not task_id:
            return

        status_map = {
            EventType.TASK_CREATED: "pending",
            EventType.TASK_STARTED: "running",
            EventType.TASK_PROGRESS: "running",
            EventType.TASK_COMPLETED: "completed",
            EventType.TASK_FAILED: "failed",
            EventType.TASK_CANCELLED: "cancelled",
        }

        with self._lock:
            record = self._tasks.get(task_id)
            if not record:
                record = TaskRecord(
                    task_id=task_id,
                    name=data.get("name", "task"),
                    status=status_map.get(event.event_type, "pending"),
                    priority=data.get("priority"),
                )
                self._tasks[task_id] = record

            record.status = status_map.get(event.event_type, record.status)
            record.updated_at = datetime.now(timezone.utc)
            record.worker_id = data.get("worker_id", record.worker_id)
            record.duration = data.get("duration", record.duration)
            if event.event_type == EventType.TASK_STARTED:
                record.started_at = datetime.now(timezone.utc)

            # Trim very old records to keep dashboard lightweight
            if len(self._tasks) > self._TASK_LIMIT:
                oldest = sorted(self._tasks.values(), key=lambda r: r.updated_at)[:5]
                for item in oldest:
                    self._tasks.pop(item.task_id, None)

    def get_snapshot(self) -> TelemetrySnapshot:
        with self._lock:
            providers = [replace(stat) for stat in self._provider_stats.values()]
            tasks = sorted(self._tasks.values(), key=lambda r: r.updated_at, reverse=True)
            recent = list(self._recent_events)
            now = datetime.now(timezone.utc)
            uptime = (now - self._start_time).total_seconds()

            return TelemetrySnapshot(
                generated_at=now,
                uptime_seconds=uptime,
                phase=self._phase,
                phase_detail=self._phase_detail,
                runtime_mode=self._runtime_mode,
                total_calls=self._total_calls,
                total_failures=self._total_failures,
                total_tokens_prompt=self._prompt_tokens,
                total_tokens_completion=self._completion_tokens,
                total_cost_usd=self._total_cost,
                last_call_at=self._last_call_at,
                online_calls=self._mode_counts["online"],
                offline_calls=self._mode_counts["offline"],
                hybrid_calls=self._mode_counts["hybrid"],
                online_tokens=self._mode_tokens["online"],
                offline_tokens=self._mode_tokens["offline"],
                hybrid_tokens=self._mode_tokens["hybrid"],
                provider_stats=providers,
                tasks=tasks[:10],
                recent_events=recent[-15:],
            )
