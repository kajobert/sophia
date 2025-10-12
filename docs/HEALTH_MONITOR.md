# Health Monitor - Guardian Replacement

**Date:** 2025-10-12  
**Phase:** Phase 3 - Health Monitor Implementation  
**Status:** ✅ COMPLETE

## Overview

Replaced **Guardian** (destructive `git reset --hard`) with **HealthMonitor** (safe observation-only monitoring).

## Changes

### 🗑️ Removed (Archived)

**guardian/** → **archive/deprecated_code/guardian/**
- ❌ `guardian/runner.py` - DESTRUCTIVE: Used `git reset --hard` on crashes
- ✅ `guardian/agent.py` - Useful monitoring logic (preserved concepts in new Health Monitor)

**Why removed:**
- **Security risk:** `git reset --hard` destroys uncommitted work
- **Design flaw:** Recovery should be handled by RecoveryManager, not external process
- **Redundancy:** NomadOrchestratorV2 already has crash recovery (RecoveryManager)

### ✨ Added

**backend/health_monitor.py** (450 lines)
- Safe resource monitoring (CPU, memory, disk, file descriptors)
- Configurable thresholds (warning/critical)
- Health status: HEALTHY, DEGRADED, UNHEALTHY
- Process-level resource tracking
- NO destructive operations
- Singleton pattern for global access

**tests/test_health_monitor.py** (16 tests)
- All metrics: disk, memory, CPU, FD count
- Health status detection (healthy/degraded/unhealthy)
- Threshold validation
- Singleton pattern
- **Result:** 16/16 PASSED ✅

### 🔧 Modified

**backend/routes/health.py**
- Integrated HealthMonitor
- Enhanced health checks with configurable thresholds
- Detailed issue reporting

## Architecture

```
┌──────────────────────────────────────┐
│      Backend FastAPI Server          │
│                                      │
│  ┌────────────────────────────────┐ │
│  │   GET /api/v1/health          │ │
│  │   ↓                            │ │
│  │   HealthMonitor.check_health() │ │
│  │   ↓                            │ │
│  │   - psutil metrics             │ │
│  │   - Threshold comparison       │ │
│  │   - Issue detection            │ │
│  │   - Status: HEALTHY/DEGRADED/  │ │
│  │     UNHEALTHY                  │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
```

## Features

### Resource Monitoring

**Disk Usage:**
- Total, used, free (GB)
- Percentage used
- Thresholds: 80% warning, 90% critical

**Memory:**
- Total, available, used (MB)
- Percentage used
- Thresholds: 80% warning, 90% critical

**CPU:**
- Percentage used (1s sample)
- Thresholds: 80% warning, 95% critical

**File Descriptors:**
- Total FD count per user
- High-usage processes (top 5)
- Thresholds: 768 warning, 900 critical

### Health Status

```python
class HealthStatus(Enum):
    HEALTHY = "healthy"      # All metrics within normal range
    DEGRADED = "degraded"    # Some warnings triggered
    UNHEALTHY = "unhealthy"  # Critical thresholds exceeded
```

### Configurable Thresholds

```python
thresholds = ResourceThresholds(
    disk_warning_percent=80.0,
    disk_critical_percent=90.0,
    memory_warning_percent=80.0,
    memory_critical_percent=90.0,
    cpu_warning_percent=80.0,
    cpu_critical_percent=95.0,
    fd_warning_count=768,
    fd_critical_count=900
)
```

## API Response Example

```json
{
  "status": "healthy",
  "checks": {
    "cpu_ok": true,
    "memory_ok": true,
    "disk_ok": true,
    "fd_ok": true
  },
  "metrics": {
    "cpu_percent": 0.0,
    "memory_percent": 1.4,
    "memory_available_mb": 1600.5,
    "disk_percent": 61.7,
    "disk_available_gb": 11.4,
    "open_file_descriptors": 5,
    "uptime_seconds": 443.6
  },
  "issues": [],
  "timestamp": "2025-10-12T18:06:50.881591"
}
```

## Testing

```bash
# Run Health Monitor tests
pytest tests/test_health_monitor.py -v

# Test API endpoint
curl http://localhost:8080/api/v1/health | jq
```

**Results:**
- ✅ 16/16 tests PASSED
- ✅ All metrics calculated correctly
- ✅ Thresholds detected properly
- ✅ Health status determined correctly
- ✅ API integration works

## Comparison: Guardian vs Health Monitor

| Feature | Guardian | Health Monitor |
|---------|----------|---------------|
| **Resource Monitoring** | ✅ Disk, Memory, FD | ✅ Disk, Memory, FD, CPU |
| **Configurable Thresholds** | ❌ Hardcoded | ✅ Dataclass config |
| **Health Status** | ❌ No aggregation | ✅ HEALTHY/DEGRADED/UNHEALTHY |
| **Process Tracking** | ⚠️ Basic | ✅ Per-process CPU/RAM/FD |
| **API Integration** | ❌ Standalone | ✅ FastAPI route |
| **Testing** | ❌ No tests | ✅ 16 unit tests |
| **Crash Recovery** | ❌ `git reset --hard` | ✅ Observation only |
| **Safety** | ⚠️ DESTRUCTIVE | ✅ READ-ONLY |

## Migration Notes

**For users who were using Guardian:**

1. **Stop Guardian:**
   ```bash
   pkill -f "guardian"
   ```

2. **Health monitoring is now automatic:**
   - Backend server includes HealthMonitor
   - Access via `/api/v1/health` endpoint
   - TUI displays health in Health tab

3. **Crash recovery:**
   - Handled by NomadOrchestratorV2's RecoveryManager
   - No external process needed
   - See `core/recovery_manager.py`

## Future Enhancements

- [ ] Prometheus metrics export
- [ ] Alerting webhooks (Slack, Discord)
- [ ] Historical metrics storage
- [ ] Custom threshold profiles (dev/prod)
- [ ] Network I/O monitoring

## Files

**Created:**
- `backend/health_monitor.py` (450 lines)
- `tests/test_health_monitor.py` (16 tests)

**Modified:**
- `backend/routes/health.py` (integrated HealthMonitor)

**Archived:**
- `guardian/` → `archive/deprecated_code/guardian/`

**Lines of Code:**
- Health Monitor: 450 lines
- Tests: 320 lines
- **Total:** 770 lines

---

**Phase 3 Status:** ✅ COMPLETE  
**Next Phase:** Phase 4 - OpenRouter Enhancement
