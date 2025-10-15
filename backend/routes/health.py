"""
Health API routes.

Endpoints for system health monitoring.
Uses HealthMonitor for detailed resource tracking.
"""

from fastapi import APIRouter
from datetime import datetime

from backend.models import HealthStatus
from backend.health_monitor import get_health_monitor

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("", response_model=HealthStatus)
async def get_health():
    """
    Get comprehensive system health status.
    
    Uses HealthMonitor for detailed resource tracking:
    - CPU, memory, disk usage
    - File descriptor count
    - High-resource processes
    - Configurable thresholds
    
    Returns:
        HealthStatus with health metrics and checks
    """
    monitor = get_health_monitor()
    report = monitor.check_health()
    
    # Build health checks
    checks = {
        "cpu_ok": report.cpu_percent < monitor.thresholds.cpu_warning_percent,
        "memory_ok": report.memory.percent_used < monitor.thresholds.memory_warning_percent,
        "disk_ok": report.disk.percent_used < monitor.thresholds.disk_warning_percent,
        "fd_ok": report.total_fds < monitor.thresholds.fd_warning_count,
    }
    
    # Build metrics (compatible with existing HealthMetrics model)
    from backend.models import HealthMetrics
    metrics = HealthMetrics(
        cpu_percent=report.cpu_percent,
        memory_percent=report.memory.percent_used,
        memory_available_mb=report.memory.available_mb,
        disk_percent=report.disk.percent_used,
        disk_available_gb=report.disk.free_gb,
        open_file_descriptors=report.total_fds,
        uptime_seconds=report.uptime_seconds,
    )
    
    return HealthStatus(
        status=report.status.value,
        checks=checks,
        metrics=metrics,
        issues=report.issues,
        timestamp=report.timestamp,
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint for uptime monitoring."""
    return {"status": "ok", "timestamp": datetime.now()}
