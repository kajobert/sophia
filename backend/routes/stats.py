"""
Stats API routes.

Endpoints for system and mission statistics.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from backend.orchestrator_manager import orchestrator_manager

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("", response_model=Dict[str, Any])
async def get_stats():
    """
    Get aggregated system statistics.
    
    Returns:
        Statistics including:
        - Total missions (completed, failed)
        - Success rate
        - Total cost and tokens
        - Average mission duration
        - Current mission status
    
    Example:
        ```
        GET /api/v1/stats
        
        Response:
        {
            "total_missions": 5,
            "completed_missions": 4,
            "failed_missions": 1,
            "success_rate": 80.0,
            "total_cost_usd": 0.15,
            "total_tokens": 15000,
            "total_llm_calls": 42,
            "average_mission_duration": 120.5,
            "current_mission": {
                "mission_id": "abc123",
                "description": "Create API",
                "state": "executing_step",
                "is_paused": false,
                "is_cancelled": false
            },
            "uptime_seconds": 3600.0
        }
        ```
    """
    try:
        return orchestrator_manager.get_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )
