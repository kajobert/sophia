"""
Budget API routes.

Endpoints for querying budget and cost information.
"""

from fastapi import APIRouter

from backend.models import BudgetResponse
from backend.orchestrator_manager import orchestrator_manager

router = APIRouter(prefix="/api/v1/budget", tags=["budget"])


@router.get("", response_model=BudgetResponse)
async def get_budget():
    """
    Get budget information for current mission.
    
    Returns:
        BudgetResponse with budget details
    """
    return orchestrator_manager.get_budget()
