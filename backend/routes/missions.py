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
        request: Control request with action
    
    Returns:
        Success message with status
    
    Raises:
        HTTPException: If action is invalid or fails
    """
    action = request.action.lower()
    
    try:
        if action == "pause":
            result = await orchestrator_manager.pause_mission()
        elif action == "resume":
            result = await orchestrator_manager.resume_mission()
        elif action == "cancel":
            result = await orchestrator_manager.cancel_mission(
                reason=getattr(request, 'reason', None)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {action}. Must be one of: pause, resume, cancel"
            )
        
        return result
        
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to {action} mission: {str(e)}"
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


# ============================================================================
# Phase 8: Mission Control Endpoints
# ============================================================================

@router.post("/{mission_id}/pause", response_model=dict)
async def pause_mission(mission_id: str, reason: str = "User requested pause"):
    """
    Pause a running mission.
    
    Args:
        mission_id: Mission ID to pause
        reason: Optional reason for pausing
    
    Returns:
        Success message with mission status
    
    Raises:
        HTTPException: If mission not found or cannot be paused
    """
    # Check if mission exists
    try:
        status_data = orchestrator_manager.get_mission_status()
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission {mission_id} not found"
            )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission {mission_id} not found"
        )
    
    # Pause mission
    success = await orchestrator_manager.pause_mission(reason)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mission {mission_id} cannot be paused in current state"
        )
    
    return {
        "status": "success",
        "mission_id": mission_id,
        "message": f"Mission {mission_id} paused successfully",
        "reason": reason
    }


@router.post("/{mission_id}/resume", response_model=dict)
async def resume_mission(mission_id: str):
    """
    Resume a paused mission.
    
    Args:
        mission_id: Mission ID to resume
    
    Returns:
        Success message with mission status
    
    Raises:
        HTTPException: If mission not found or not paused
    """
    # Check if mission exists
    try:
        status_data = orchestrator_manager.get_mission_status()
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission {mission_id} not found"
            )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission {mission_id} not found"
        )
    
    # Resume mission
    success = await orchestrator_manager.resume_mission()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mission {mission_id} is not paused or cannot be resumed"
        )
    
    return {
        "status": "success",
        "mission_id": mission_id,
        "message": f"Mission {mission_id} resumed successfully"
    }


@router.post("/{mission_id}/cancel", response_model=dict)
async def cancel_mission(mission_id: str, reason: str = "User requested cancellation"):
    """
    Cancel a running or paused mission.
    
    Args:
        mission_id: Mission ID to cancel
        reason: Optional reason for cancellation
    
    Returns:
        Success message with mission status
    
    Raises:
        HTTPException: If mission not found or already completed
    """
    # Check if mission exists
    try:
        status_data = orchestrator_manager.get_mission_status()
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission {mission_id} not found"
            )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission {mission_id} not found"
        )
    
    # Cancel mission
    success = await orchestrator_manager.cancel_mission(reason)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mission {mission_id} cannot be cancelled (may already be completed)"
        )
    
    return {
        "status": "success",
        "mission_id": mission_id,
        "message": f"Mission {mission_id} cancellation requested",
        "reason": reason
    }
