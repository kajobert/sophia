from enum import Enum
from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime

class State(Enum):
    """All possible states for the orchestrator."""
    AWAITING_USER_INPUT = "awaiting_user_input"
    PLANNING = "planning"
    EXECUTING_STEP = "executing_step"
    AWAITING_TOOL_RESULT = "awaiting_tool_result"
    REFLECTION = "reflection"
    RESPONDING = "responding"

class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass

class StateManager:
    """Manages the state of the orchestrator, including validation and persistence."""

    VALID_TRANSITIONS: Dict[State, List[State]] = {
        State.AWAITING_USER_INPUT: [State.PLANNING],
        State.PLANNING: [State.EXECUTING_STEP, State.RESPONDING],
        State.EXECUTING_STEP: [State.AWAITING_TOOL_RESULT],
        State.AWAITING_TOOL_RESULT: [State.EXECUTING_STEP, State.REFLECTION],
        State.REFLECTION: [State.RESPONDING],
        State.RESPONDING: [State.AWAITING_USER_INPUT],
    }

    def __init__(self, project_root: str = ".", session_id: Optional[str] = None):
        self.project_root = project_root
        self.session_id = session_id or self._generate_session_id()
        self.current_state = State.AWAITING_USER_INPUT
        self.state_data: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.session_file = os.path.join(self.project_root, "memory", "session.json")

    def _generate_session_id(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def transition_to(self, new_state: State, reason: str = ""):
        allowed_states = self.VALID_TRANSITIONS.get(self.current_state, [])
        if new_state not in allowed_states:
            raise StateTransitionError(
                f"Invalid transition from {self.current_state.value} to {new_state.value}. "
                f"Allowed transitions: {[s.value for s in allowed_states]}"
            )

        transition_record = {
            "from": self.current_state.value,
            "to": new_state.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        }
        self.history.append(transition_record)
        self.current_state = new_state
        self.persist()

    def set_data(self, key: str, value: Any):
        self.state_data[key] = value
        self.persist()

    def get_data(self, key: str, default: Any = None) -> Any:
        return self.state_data.get(key, default)

    def persist(self):
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
        state_snapshot = {
            "session_id": self.session_id,
            "current_state": self.current_state.value,
            "plan": self.get_data("plan", {}),
            "history": self.history,
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(state_snapshot, f, indent=2, ensure_ascii=False)

    def restore(self) -> bool:
        if not os.path.exists(self.session_file):
            return False

        with open(self.session_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)

        self.session_id = snapshot["session_id"]
        self.current_state = State(snapshot["current_state"])
        self.set_data("plan", snapshot.get("plan", {}))
        self.history = snapshot["history"]
        return True