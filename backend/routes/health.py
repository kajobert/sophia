"""
Health API routes.

Endpoints for system health monitoring.
"""

from fastapi import APIRouter
from datetime import datetime

from backend.models import HealthStatus
from backend.orchestrator_manager import orchestrator_manager

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("", response_model=HealthStatus)
async def get_health():
    """
    Get system health status.
    
    Returns:
        HealthStatus with health metrics and checks
    """
    metrics = orchestrator_manager.get_health_metrics()
    
    # Perform health checks
    checks = {
        "cpu_ok": metrics.cpu_percent < 80.0,
        "memory_ok": metrics.memory_percent < 90.0,
        "disk_ok": metrics.disk_percent < 90.0,
        "fd_ok": metrics.open_file_descriptors < 1000,
    }
    
    # Determine overall status
    all_ok = all(checks.values())
    some_ok = any(checks.values())
    
    if all_ok:
        status_val = "healthy"
    elif some_ok:
        status_val = "degraded"
    else:
        status_val = "unhealthy"
    
    # Collect issues
    issues = []
    if not checks["cpu_ok"]:
        issues.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
    if not checks["memory_ok"]:
        issues.append(f"High memory usage: {metrics.memory_percent:.1f}%")
    if not checks["disk_ok"]:
        issues.append(f"High disk usage: {metrics.disk_percent:.1f}%")
    if not checks["fd_ok"]:
        issues.append(f"Many open file descriptors: {metrics.open_file_descriptors}")
    
    return HealthStatus(
        status=status_val,
        checks=checks,
        metrics=metrics,
        issues=issues,
        timestamp=datetime.now(),
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint for uptime monitoring."""
    return {"status": "ok", "timestamp": datetime.now()}
