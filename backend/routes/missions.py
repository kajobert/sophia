"""
Mission API routes.

Endpoints for creating, querying, and controlling missions.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List

from backend.models import (
    MissionCreateRequest,
    MissionResponse,
    MissionListResponse,
    MissionControlRequest,
    ErrorResponse,
)
from backend.orchestrator_manager import orchestrator_manager

router = APIRouter(prefix="/api/v1/missions", tags=["missions"])


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(request: MissionCreateRequest):
    """
    Create and start a new mission.
    
    Args:
        request: Mission creation request
    
    Returns:
        MissionResponse with mission details
    
    Raises:
        HTTPException: If mission creation fails
    """
    try:
        mission = await orchestrator_manager.create_mission(
            description=request.description,
            max_steps=request.max_steps or 50,
            budget_limit=request.budget_limit,
        )
        return mission
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create mission: {str(e)}"
        )


@router.get("/current", response_model=MissionResponse)
async def get_current_mission():
    """
    Get current mission status.
    
    Returns:
        MissionResponse with current mission details
    
    Raises:
        HTTPException: If no active mission
    """
    try:
        return orchestrator_manager.get_mission_status()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/current/control", response_model=dict)
async def control_mission(request: MissionControlRequest):
    """
    Control current mission (pause, resume, cancel).
    
    Args:
        request: Control request
    
    Returns:
        Success message
    
    Raises:
        HTTPException: If action is invalid or fails
    """
    # TODO: Implement pause/resume/cancel
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Mission control not yet implemented"
    )


@router.get("", response_model=MissionListResponse)
async def list_missions():
    """
    List all missions (current + history).
    
    Returns:
        MissionListResponse with mission list
    """
    # TODO: Implement mission history
    # For now, just return current mission if exists
    try:
        current = orchestrator_manager.get_mission_status()
        return MissionListResponse(
            missions=[current],
            total=1
        )
    except RuntimeError:
        return MissionListResponse(
            missions=[],
            total=0
        )
