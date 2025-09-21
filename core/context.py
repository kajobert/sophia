from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field

class SharedContext(BaseModel):
    """
    A data class to hold shared information across different agents in a session.
    Now supports structured plans and execution history.
    """
    session_id: str
    original_prompt: str
    user: Optional[str] = None

    # New structured planning fields
    current_plan: Optional[List[Dict[str, Any]]] = Field(default=None, description="The structured plan currently being executed.")
    step_history: List[Dict[str, Any]] = Field(default_factory=list, description="A log of all executed steps and their outcomes.")
    last_step_output: Optional[Dict[str, Any]] = Field(default=None, description="The output from the last executed step.")

    # Legacy or other workflow fields
    full_history: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    code: Optional[str] = None
    test_results: Optional[str] = None
    feedback: Optional[str] = None  # For retry loops or general feedback
    available_tools: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
