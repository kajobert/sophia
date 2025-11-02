from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging


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
