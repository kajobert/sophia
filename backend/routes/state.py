"""
State API routes.

Endpoints for querying orchestrator state.
"""

from fastapi import APIRouter, HTTPException, status

from backend.models import StateResponse, StateTransitionRequest
from backend.orchestrator_manager import orchestrator_manager

router = APIRouter(prefix="/api/v1/state", tags=["state"])


@router.get("", response_model=StateResponse)
async def get_state():
    """
    Get current orchestrator state.
    
    Returns:
        StateResponse with state details
    """
    return orchestrator_manager.get_state()


@router.post("/transition", response_model=StateResponse)
async def transition_state(request: StateTransitionRequest):
    """
    Force state transition (DEBUG ONLY).
    
    Args:
        request: State transition request
    
    Returns:
        StateResponse with new state
    
    Raises:
        HTTPException: If transition is invalid
    """
    # TODO: Implement state transition via orchestrator
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Manual state transitions not yet implemented"
    )
