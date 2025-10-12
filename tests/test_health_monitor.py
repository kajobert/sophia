"""
Tests for HealthMonitor.

Validates resource monitoring, threshold detection, and health reporting.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from backend.health_monitor import (
    HealthMonitor,
    HealthStatus,
    ResourceThresholds,
    DiskMetrics,
    MemoryMetrics,
    ProcessMetrics,
    get_health_monitor,
)


class TestDiskMetrics:
    """Test DiskMetrics dataclass."""
    
    def test_disk_metrics_properties(self):
        """Test GB conversions."""
        metrics = DiskMetrics(
            path="/",
            total_bytes=100 * 1024**3,  # 100 GB
            used_bytes=50 * 1024**3,    # 50 GB
            free_bytes=50 * 1024**3,    # 50 GB
            percent_used=50.0
        )
        
        assert metrics.total_gb == pytest.approx(100.0, rel=0.01)
        assert metrics.used_gb == pytest.approx(50.0, rel=0.01)
        assert metrics.free_gb == pytest.approx(50.0, rel=0.01)


class TestMemoryMetrics:
    """Test MemoryMetrics dataclass."""
    
    def test_memory_metrics_properties(self):
        """Test MB conversions."""
        metrics = MemoryMetrics(
            total_bytes=16 * 1024**3,     # 16 GB
            available_bytes=8 * 1024**3,  # 8 GB
            used_bytes=8 * 1024**3,       # 8 GB
            percent_used=50.0
        )
        
        assert metrics.total_mb == pytest.approx(16 * 1024, rel=0.01)
        assert metrics.available_mb == pytest.approx(8 * 1024, rel=0.01)
        assert metrics.used_mb == pytest.approx(8 * 1024, rel=0.01)


class TestHealthMonitor:
    """Test HealthMonitor class."""
    
    def test_init_default_thresholds(self):
        """Test initialization with default thresholds."""
        monitor = HealthMonitor()
        
        assert monitor.thresholds.disk_warning_percent == 80.0
        assert monitor.thresholds.memory_warning_percent == 80.0
        assert monitor.check_interval == 30.0
        assert monitor.last_report is None
    
    def test_init_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        thresholds = ResourceThresholds(
            disk_warning_percent=70.0,
            memory_warning_percent=75.0
        )
        monitor = HealthMonitor(thresholds=thresholds, check_interval_seconds=60.0)
        
        assert monitor.thresholds.disk_warning_percent == 70.0
        assert monitor.thresholds.memory_warning_percent == 75.0
        assert monitor.check_interval == 60.0
    
    @patch('backend.health_monitor.psutil.disk_usage')
    def test_get_disk_metrics(self, mock_disk_usage):
        """Test disk metrics collection."""
        # Mock psutil response
        mock_usage = Mock()
        mock_usage.total = 100 * 1024**3
        mock_usage.used = 60 * 1024**3
        mock_usage.free = 40 * 1024**3
        mock_usage.percent = 60.0
        mock_disk_usage.return_value = mock_usage
        
        monitor = HealthMonitor()
        metrics = monitor.get_disk_metrics("/")
        
        assert metrics.path == "/"
        assert metrics.percent_used == 60.0
        assert metrics.total_gb == pytest.approx(100.0, rel=0.01)
        assert metrics.used_gb == pytest.approx(60.0, rel=0.01)
    
    @patch('backend.health_monitor.psutil.virtual_memory')
    def test_get_memory_metrics(self, mock_virtual_memory):
        """Test memory metrics collection."""
        # Mock psutil response
        mock_mem = Mock()
        mock_mem.total = 16 * 1024**3
        mock_mem.available = 8 * 1024**3
        mock_mem.used = 8 * 1024**3
        mock_mem.percent = 50.0
        mock_virtual_memory.return_value = mock_mem
        
        monitor = HealthMonitor()
        metrics = monitor.get_memory_metrics()
        
        assert metrics.percent_used == 50.0
        assert metrics.total_mb == pytest.approx(16 * 1024, rel=0.01)
        assert metrics.available_mb == pytest.approx(8 * 1024, rel=0.01)
    
    @patch('backend.health_monitor.psutil.cpu_percent')
    def test_get_cpu_percent(self, mock_cpu_percent):
        """Test CPU metrics collection."""
        mock_cpu_percent.return_value = 45.5
        
        monitor = HealthMonitor()
        cpu = monitor.get_cpu_percent()
        
        assert cpu == 45.5
        mock_cpu_percent.assert_called_once_with(interval=1.0)
    
    @patch('backend.health_monitor.os.getuid')
    @patch('backend.health_monitor.psutil.process_iter')
    def test_get_file_descriptor_count(self, mock_process_iter, mock_getuid):
        """Test file descriptor counting."""
        mock_getuid.return_value = 1000
        
        # Mock processes
        mock_proc1 = Mock()
        mock_proc1.info = {
            'pid': 100,
            'name': 'python',
            'username': 'user',
            'uids': Mock(real=1000)
        }
        mock_proc1.num_fds.return_value = 50
        
        mock_proc2 = Mock()
        mock_proc2.info = {
            'pid': 200,
            'name': 'bash',
            'username': 'user',
            'uids': Mock(real=1000)
        }
        mock_proc2.num_fds.return_value = 300  # High usage
        mock_proc2.cpu_percent.return_value = 10.0
        mock_proc2.memory_info.return_value = Mock(rss=100 * 1024**2)
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2]
        
        monitor = HealthMonitor()
        total_fds, high_procs = monitor.get_file_descriptor_count()
        
        assert total_fds == 350
        assert len(high_procs) == 1
        assert high_procs[0].name == 'bash'
        assert high_procs[0].num_fds == 300
    
    @patch('backend.health_monitor.HealthMonitor.get_cpu_percent')
    @patch('backend.health_monitor.HealthMonitor.get_file_descriptor_count')
    @patch('backend.health_monitor.HealthMonitor.get_memory_metrics')
    @patch('backend.health_monitor.HealthMonitor.get_disk_metrics')
    def test_check_health_healthy(
        self,
        mock_disk,
        mock_memory,
        mock_fds,
        mock_cpu
    ):
        """Test health check when everything is healthy."""
        # Mock all metrics within healthy thresholds
        mock_disk.return_value = DiskMetrics("/", 100*1024**3, 50*1024**3, 50*1024**3, 50.0)
        mock_memory.return_value = MemoryMetrics(16*1024**3, 10*1024**3, 6*1024**3, 37.5)
        mock_cpu.return_value = 30.0
        mock_fds.return_value = (400, [])
        
        monitor = HealthMonitor()
        report = monitor.check_health()
        
        assert report.status == HealthStatus.HEALTHY
        assert len(report.issues) == 0
        assert report.disk.percent_used == 50.0
        assert report.memory.percent_used == 37.5
        assert report.cpu_percent == 30.0
        assert report.total_fds == 400
    
    @patch('backend.health_monitor.HealthMonitor.get_cpu_percent')
    @patch('backend.health_monitor.HealthMonitor.get_file_descriptor_count')
    @patch('backend.health_monitor.HealthMonitor.get_memory_metrics')
    @patch('backend.health_monitor.HealthMonitor.get_disk_metrics')
    def test_check_health_degraded_disk(
        self,
        mock_disk,
        mock_memory,
        mock_fds,
        mock_cpu
    ):
        """Test health check with degraded disk."""
        # Disk at warning threshold
        mock_disk.return_value = DiskMetrics("/", 100*1024**3, 85*1024**3, 15*1024**3, 85.0)
        mock_memory.return_value = MemoryMetrics(16*1024**3, 10*1024**3, 6*1024**3, 37.5)
        mock_cpu.return_value = 30.0
        mock_fds.return_value = (400, [])
        
        monitor = HealthMonitor()
        report = monitor.check_health()
        
        assert report.status == HealthStatus.DEGRADED
        assert len(report.issues) > 0
        assert any("Disk usage" in issue for issue in report.issues)
    
    @patch('backend.health_monitor.HealthMonitor.get_cpu_percent')
    @patch('backend.health_monitor.HealthMonitor.get_file_descriptor_count')
    @patch('backend.health_monitor.HealthMonitor.get_memory_metrics')
    @patch('backend.health_monitor.HealthMonitor.get_disk_metrics')
    def test_check_health_unhealthy_memory(
        self,
        mock_disk,
        mock_memory,
        mock_fds,
        mock_cpu
    ):
        """Test health check with critical memory usage."""
        mock_disk.return_value = DiskMetrics("/", 100*1024**3, 50*1024**3, 50*1024**3, 50.0)
        # Memory at critical threshold
        mock_memory.return_value = MemoryMetrics(16*1024**3, 1*1024**3, 15*1024**3, 93.7)
        mock_cpu.return_value = 30.0
        mock_fds.return_value = (400, [])
        
        monitor = HealthMonitor()
        report = monitor.check_health()
        
        assert report.status == HealthStatus.UNHEALTHY
        assert len(report.issues) > 0
        assert any("CRITICAL" in issue and "Memory" in issue for issue in report.issues)
    
    @patch('backend.health_monitor.HealthMonitor.get_cpu_percent')
    @patch('backend.health_monitor.HealthMonitor.get_file_descriptor_count')
    @patch('backend.health_monitor.HealthMonitor.get_memory_metrics')
    @patch('backend.health_monitor.HealthMonitor.get_disk_metrics')
    def test_check_health_unhealthy_cpu(
        self,
        mock_disk,
        mock_memory,
        mock_fds,
        mock_cpu
    ):
        """Test health check with critical CPU usage."""
        mock_disk.return_value = DiskMetrics("/", 100*1024**3, 50*1024**3, 50*1024**3, 50.0)
        mock_memory.return_value = MemoryMetrics(16*1024**3, 10*1024**3, 6*1024**3, 37.5)
        # CPU at critical threshold
        mock_cpu.return_value = 96.0
        mock_fds.return_value = (400, [])
        
        monitor = HealthMonitor()
        report = monitor.check_health()
        
        assert report.status == HealthStatus.UNHEALTHY
        assert len(report.issues) > 0
        assert any("CRITICAL" in issue and "CPU" in issue for issue in report.issues)
    
    @patch('backend.health_monitor.HealthMonitor.check_health')
    def test_get_health_dict(self, mock_check_health):
        """Test health dict conversion."""
        # Mock health report
        mock_report = Mock()
        mock_report.status = HealthStatus.HEALTHY
        mock_report.timestamp = datetime(2025, 10, 12, 18, 0, 0)
        mock_report.cpu_percent = 45.5
        mock_report.memory = MemoryMetrics(16*1024**3, 8*1024**3, 8*1024**3, 50.0)
        mock_report.disk = DiskMetrics("/", 100*1024**3, 60*1024**3, 40*1024**3, 60.0)
        mock_report.total_fds = 500
        mock_report.uptime_seconds = 3600.0
        mock_report.issues = []
        mock_report.high_resource_processes = []
        
        monitor = HealthMonitor()
        monitor.last_report = mock_report
        
        health_dict = monitor.get_health_dict()
        
        assert health_dict["status"] == "healthy"
        assert health_dict["metrics"]["cpu_percent"] == 45.5
        assert health_dict["metrics"]["memory_percent"] == 50.0
        assert health_dict["metrics"]["disk_percent"] == 60.0
        assert health_dict["metrics"]["open_file_descriptors"] == 500
        assert health_dict["issues"] == []
    
    def test_singleton_get_health_monitor(self):
        """Test singleton pattern for get_health_monitor()."""
        monitor1 = get_health_monitor()
        monitor2 = get_health_monitor()
        
        assert monitor1 is monitor2  # Same instance


class TestResourceThresholds:
    """Test ResourceThresholds configuration."""
    
    def test_default_thresholds(self):
        """Test default threshold values."""
        thresholds = ResourceThresholds()
        
        assert thresholds.disk_warning_percent == 80.0
        assert thresholds.disk_critical_percent == 90.0
        assert thresholds.memory_warning_percent == 80.0
        assert thresholds.memory_critical_percent == 90.0
        assert thresholds.fd_warning_count == 768
        assert thresholds.fd_critical_count == 900
        assert thresholds.cpu_warning_percent == 80.0
        assert thresholds.cpu_critical_percent == 95.0
    
    def test_custom_thresholds(self):
        """Test custom threshold values."""
        thresholds = ResourceThresholds(
            disk_warning_percent=70.0,
            disk_critical_percent=85.0,
            memory_warning_mb=256.0,
            cpu_warning_percent=60.0
        )
        
        assert thresholds.disk_warning_percent == 70.0
        assert thresholds.disk_critical_percent == 85.0
        assert thresholds.memory_warning_mb == 256.0
        assert thresholds.cpu_warning_percent == 60.0
