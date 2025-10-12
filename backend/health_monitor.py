"""
Health Monitor - System Resource Monitoring.

Bezpečný monitoring systémových prostředků bez destruktivních operací.
Nahrazuje Guardian s fokusem na observability, ne recovery.

Features:
- Disk usage tracking
- Memory monitoring
- File descriptor tracking
- Process resource usage
- Health status aggregation
- No destructive operations (no git reset!)
"""

import os
import time
import psutil
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """System health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ResourceThresholds:
    """Configurable thresholds for resource monitoring."""
    
    # Disk thresholds
    disk_warning_percent: float = 80.0
    disk_critical_percent: float = 90.0
    
    # Memory thresholds
    memory_warning_percent: float = 80.0
    memory_critical_percent: float = 90.0
    memory_warning_mb: float = 512.0
    
    # File descriptor thresholds
    fd_warning_count: int = 768
    fd_critical_count: int = 900
    fd_per_process_warning: int = 256
    
    # CPU thresholds
    cpu_warning_percent: float = 80.0
    cpu_critical_percent: float = 95.0


@dataclass
class DiskMetrics:
    """Disk usage metrics."""
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent_used: float
    
    @property
    def total_gb(self) -> float:
        return self.total_bytes / (1024**3)
    
    @property
    def used_gb(self) -> float:
        return self.used_bytes / (1024**3)
    
    @property
    def free_gb(self) -> float:
        return self.free_bytes / (1024**3)


@dataclass
class MemoryMetrics:
    """Memory usage metrics."""
    total_bytes: int
    available_bytes: int
    used_bytes: int
    percent_used: float
    
    @property
    def total_mb(self) -> float:
        return self.total_bytes / (1024**2)
    
    @property
    def available_mb(self) -> float:
        return self.available_bytes / (1024**2)
    
    @property
    def used_mb(self) -> float:
        return self.used_bytes / (1024**2)


@dataclass
class ProcessMetrics:
    """Per-process resource metrics."""
    pid: int
    name: str
    username: str
    cpu_percent: float
    memory_mb: float
    num_fds: int


@dataclass
class HealthReport:
    """Complete health report."""
    status: HealthStatus
    timestamp: datetime
    disk: DiskMetrics
    memory: MemoryMetrics
    cpu_percent: float
    total_fds: int
    issues: List[str] = field(default_factory=list)
    high_resource_processes: List[ProcessMetrics] = field(default_factory=list)
    uptime_seconds: float = 0.0


class HealthMonitor:
    """
    System health monitor.
    
    Tracks system resources and provides health status.
    NO destructive operations - only observation.
    """
    
    def __init__(
        self,
        thresholds: Optional[ResourceThresholds] = None,
        check_interval_seconds: float = 30.0
    ):
        """
        Initialize health monitor.
        
        Args:
            thresholds: Resource thresholds (uses defaults if None)
            check_interval_seconds: Interval between health checks
        """
        self.thresholds = thresholds or ResourceThresholds()
        self.check_interval = check_interval_seconds
        self.start_time = time.time()
        
        # History
        self.last_report: Optional[HealthReport] = None
        self.issue_history: List[Tuple[datetime, str]] = []
        
        logger.info(f"HealthMonitor initialized with {self.check_interval}s interval")
    
    def get_disk_metrics(self, path: str = "/") -> DiskMetrics:
        """Get disk usage metrics."""
        try:
            usage = psutil.disk_usage(path)
            return DiskMetrics(
                path=path,
                total_bytes=usage.total,
                used_bytes=usage.used,
                free_bytes=usage.free,
                percent_used=usage.percent
            )
        except Exception as e:
            logger.error(f"Failed to get disk metrics for {path}: {e}")
            # Return dummy metrics on error
            return DiskMetrics(path=path, total_bytes=0, used_bytes=0, free_bytes=0, percent_used=0.0)
    
    def get_memory_metrics(self) -> MemoryMetrics:
        """Get memory usage metrics."""
        try:
            mem = psutil.virtual_memory()
            return MemoryMetrics(
                total_bytes=mem.total,
                available_bytes=mem.available,
                used_bytes=mem.used,
                percent_used=mem.percent
            )
        except Exception as e:
            logger.error(f"Failed to get memory metrics: {e}")
            return MemoryMetrics(total_bytes=0, available_bytes=0, used_bytes=0, percent_used=0.0)
    
    def get_cpu_percent(self) -> float:
        """Get CPU usage percent (blocking for 1s to get accurate reading)."""
        try:
            return psutil.cpu_percent(interval=1.0)
        except Exception as e:
            logger.error(f"Failed to get CPU metrics: {e}")
            return 0.0
    
    def get_file_descriptor_count(self) -> Tuple[int, List[ProcessMetrics]]:
        """
        Get total file descriptor count for current user.
        
        Returns:
            Tuple of (total_fds, high_usage_processes)
        """
        try:
            current_uid = os.getuid()
            total_fds = 0
            high_usage_procs = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'uids']):
                if proc.info['uids'] and proc.info['uids'].real == current_uid:
                    try:
                        num_fds = proc.num_fds()
                        total_fds += num_fds
                        
                        # Track high FD usage processes
                        if num_fds > self.thresholds.fd_per_process_warning:
                            try:
                                cpu = proc.cpu_percent(interval=0.1)
                                mem = proc.memory_info().rss / (1024**2)
                                
                                high_usage_procs.append(ProcessMetrics(
                                    pid=proc.info['pid'],
                                    name=proc.info['name'],
                                    username=proc.info['username'] or "unknown",
                                    cpu_percent=cpu,
                                    memory_mb=mem,
                                    num_fds=num_fds
                                ))
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            # Sort by FD count descending
            high_usage_procs.sort(key=lambda x: x.num_fds, reverse=True)
            
            return total_fds, high_usage_procs[:5]  # Top 5
        
        except Exception as e:
            logger.error(f"Failed to get file descriptor count: {e}")
            return 0, []
    
    def check_health(self) -> HealthReport:
        """
        Perform complete health check.
        
        Returns:
            HealthReport with current system status
        """
        # Collect metrics
        disk = self.get_disk_metrics("/")
        memory = self.get_memory_metrics()
        cpu = self.get_cpu_percent()
        total_fds, high_fd_procs = self.get_file_descriptor_count()
        
        # Analyze issues
        issues = []
        status = HealthStatus.HEALTHY
        
        # Disk checks
        if disk.percent_used >= self.thresholds.disk_critical_percent:
            issues.append(f"CRITICAL: Disk usage at {disk.percent_used:.1f}% (threshold: {self.thresholds.disk_critical_percent}%)")
            status = HealthStatus.UNHEALTHY
        elif disk.percent_used >= self.thresholds.disk_warning_percent:
            issues.append(f"WARNING: Disk usage at {disk.percent_used:.1f}% (threshold: {self.thresholds.disk_warning_percent}%)")
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.DEGRADED
        
        # Memory checks
        if memory.percent_used >= self.thresholds.memory_critical_percent:
            issues.append(f"CRITICAL: Memory usage at {memory.percent_used:.1f}% (threshold: {self.thresholds.memory_critical_percent}%)")
            status = HealthStatus.UNHEALTHY
        elif memory.percent_used >= self.thresholds.memory_warning_percent:
            issues.append(f"WARNING: Memory usage at {memory.percent_used:.1f}% (threshold: {self.thresholds.memory_warning_percent}%)")
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.DEGRADED
        
        if memory.available_mb < self.thresholds.memory_warning_mb:
            issues.append(f"WARNING: Available memory low: {memory.available_mb:.1f} MB (threshold: {self.thresholds.memory_warning_mb} MB)")
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.DEGRADED
        
        # CPU checks
        if cpu >= self.thresholds.cpu_critical_percent:
            issues.append(f"CRITICAL: CPU usage at {cpu:.1f}% (threshold: {self.thresholds.cpu_critical_percent}%)")
            status = HealthStatus.UNHEALTHY
        elif cpu >= self.thresholds.cpu_warning_percent:
            issues.append(f"WARNING: CPU usage at {cpu:.1f}% (threshold: {self.thresholds.cpu_warning_percent}%)")
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.DEGRADED
        
        # File descriptor checks
        if total_fds >= self.thresholds.fd_critical_count:
            issues.append(f"CRITICAL: File descriptors at {total_fds} (threshold: {self.thresholds.fd_critical_count})")
            status = HealthStatus.UNHEALTHY
        elif total_fds >= self.thresholds.fd_warning_count:
            issues.append(f"WARNING: File descriptors at {total_fds} (threshold: {self.thresholds.fd_warning_count})")
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.DEGRADED
        
        # High FD processes
        if high_fd_procs:
            proc_names = ", ".join([f"{p.name}({p.num_fds})" for p in high_fd_procs[:3]])
            issues.append(f"High FD usage: {proc_names}")
        
        # Create report
        report = HealthReport(
            status=status,
            timestamp=datetime.now(),
            disk=disk,
            memory=memory,
            cpu_percent=cpu,
            total_fds=total_fds,
            issues=issues,
            high_resource_processes=high_fd_procs,
            uptime_seconds=time.time() - self.start_time
        )
        
        # Store in history
        self.last_report = report
        for issue in issues:
            self.issue_history.append((report.timestamp, issue))
            # Keep last 100 issues
            if len(self.issue_history) > 100:
                self.issue_history = self.issue_history[-100:]
        
        # Log critical issues
        if status == HealthStatus.UNHEALTHY:
            logger.error(f"UNHEALTHY: {', '.join(issues)}")
        elif status == HealthStatus.DEGRADED:
            logger.warning(f"DEGRADED: {', '.join(issues)}")
        else:
            logger.debug(f"HEALTHY: No issues detected")
        
        return report
    
    def get_health_dict(self) -> Dict:
        """
        Get health report as dict (for API responses).
        
        Returns:
            Dict representation of last health report
        """
        if not self.last_report:
            # Perform check if no report exists
            self.check_health()
        
        report = self.last_report
        
        return {
            "status": report.status.value,
            "timestamp": report.timestamp.isoformat(),
            "metrics": {
                "cpu_percent": round(report.cpu_percent, 2),
                "memory_percent": round(report.memory.percent_used, 2),
                "memory_available_mb": round(report.memory.available_mb, 2),
                "disk_percent": round(report.disk.percent_used, 2),
                "disk_available_gb": round(report.disk.free_gb, 2),
                "open_file_descriptors": report.total_fds,
                "uptime_seconds": round(report.uptime_seconds, 2)
            },
            "issues": report.issues,
            "high_resource_processes": [
                {
                    "pid": p.pid,
                    "name": p.name,
                    "cpu_percent": round(p.cpu_percent, 2),
                    "memory_mb": round(p.memory_mb, 2),
                    "num_fds": p.num_fds
                }
                for p in report.high_resource_processes[:5]
            ]
        }
    
    def run_monitoring_loop(self):
        """
        Run continuous monitoring loop.
        
        This is a blocking function that runs forever.
        Use in dedicated thread or process.
        """
        logger.info(f"Starting health monitoring loop (interval: {self.check_interval}s)")
        logger.info(f"Thresholds: Disk={self.thresholds.disk_warning_percent}%, Memory={self.thresholds.memory_warning_percent}%, CPU={self.thresholds.cpu_warning_percent}%")
        
        try:
            while True:
                try:
                    self.check_health()
                    time.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                    time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Health monitoring stopped by user")


# Global singleton instance
_health_monitor_instance: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get global HealthMonitor instance (singleton)."""
    global _health_monitor_instance
    if _health_monitor_instance is None:
        _health_monitor_instance = HealthMonitor()
    return _health_monitor_instance


if __name__ == "__main__":
    # Standalone monitoring mode
    logging.basicConfig(
        level=logging.INFO,
        format="[HealthMonitor] %(asctime)s - %(levelname)s - %(message)s"
    )
    
    monitor = HealthMonitor(check_interval_seconds=10.0)
    monitor.run_monitoring_loop()
