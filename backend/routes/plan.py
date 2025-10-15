"""
Plan API routes.

Endpoints for querying mission plans.
"""

from fastapi import APIRouter, HTTPException, status

from backend.models import PlanResponse
from backend.orchestrator_manager import orchestrator_manager

router = APIRouter(prefix="/api/v1/plan", tags=["plan"])


@router.get("", response_model=PlanResponse)
async def get_plan():
    """
    Get current mission plan.
    
    Returns:
        PlanResponse with plan details
    
    Raises:
        HTTPException: If no active mission
    """
    try:
        return orchestrator_manager.get_plan()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
