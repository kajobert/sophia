"""
Logs API routes.

Endpoints for querying logs.
"""

from fastapi import APIRouter, Query
from typing import Optional

from backend.models import LogResponse, LogLevelEnum
from backend.orchestrator_manager import orchestrator_manager

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.get("", response_model=LogResponse)
async def get_logs(
    level: Optional[LogLevelEnum] = Query(None, description="Filter by log level"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs"),
):
    """
    Get logs with optional filtering.
    
    Args:
        level: Filter by log level
        source: Filter by source
        limit: Maximum number of logs to return
    
    Returns:
        LogResponse with logs
    """
    logs = orchestrator_manager.get_logs(
        level=level,
        source=source,
        limit=limit
    )
    
    return LogResponse(
        logs=logs,
        total=len(logs)
    )
