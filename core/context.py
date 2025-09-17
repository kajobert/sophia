from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class SharedContext:
    """
    A data class to hold shared information across different agents in a session.
    """
    session_id: str
    original_prompt: str
    full_history: List[str] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
