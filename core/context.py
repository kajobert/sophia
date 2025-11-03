from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import logging

# Avoid circular imports
if TYPE_CHECKING:
    from core.event_bus import EventBus
    from core.task_queue import TaskQueue


@dataclass
class SharedContext:
    """
    The data bus and "lifeblood" of the system.
    An instance of this class is passed to all plugins.
    It contains the entire state for the current cycle.
    """

    session_id: str
    current_state: str
    logger: logging.Logger
    user_input: Optional[str] = None
    history: List[Dict[str, str]] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # NEW: Event-driven components (optional for backwards compatibility)
    event_bus: Optional["EventBus"] = None
    task_queue: Optional["TaskQueue"] = None
    
    # Feature flag to enable new architecture
    use_event_driven: bool = False
