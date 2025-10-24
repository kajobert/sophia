from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging


@dataclass
class SharedContext:
    """
    Datova sbernice a "krevni obeh" systemu.
    Instance teto tridy se predava vsem pluginum.
    Obsahuje veskery stav pro aktualni cyklus.
    """

    session_id: str
    current_state: str
    logger: logging.Logger
    user_input: Optional[str] = None
    history: List[Dict[str, str]] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
