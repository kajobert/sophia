# Background Process Management - Design Specification

**Version:** 1.0  
**Date:** 2025-11-03  
**Status:** Design Specification  
**Phase:** 2 - Background Process Management  
**Author:** Sophia AI Agent

---

## 📋 Overview

The Background Process Management system enables Sophia to spawn, monitor, and react to long-running background processes such as:
- Jules AI agent sessions
- Test suite execution (pytest, unit tests)
- Build processes (CI/CD pipelines)
- Code analysis tools
- Web servers / development servers

### **Goals**
1. ✅ Unified process management - single interface for all background tasks
2. ✅ Event-driven monitoring - emit events on status changes
3. ✅ Non-blocking execution - processes run in background
4. ✅ Automatic cleanup - graceful shutdown and resource management
5. ✅ Error recovery - detect and handle process failures

---

## 🎯 Core Concepts

### **Process**
A long-running background task that Sophia monitors.

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessType(Enum):
    """Types of background processes"""
    JULES_SESSION = "jules_session"      # Jules AI agent task
    TEST_SUITE = "test_suite"            # pytest/unittest execution
    BUILD = "build"                       # Build process
    SERVER = "server"                    # Development server
    ANALYSIS = "analysis"                # Code analysis tool
    CUSTOM = "custom"                    # User-defined process

class ProcessState(Enum):
    """Process lifecycle states"""
    STARTING = "starting"        # Process is being spawned
    RUNNING = "running"          # Process is active
    COMPLETED = "completed"      # Process finished successfully
    FAILED = "failed"            # Process failed with error
    TIMEOUT = "timeout"          # Process exceeded max duration
    CANCELLED = "cancelled"      # Process was manually stopped

@dataclass
class BackgroundProcess:
    """
    Represents a background process being monitored.
    
    Attributes:
        process_id: Unique identifier
        process_type: Type of process
        name: Human-readable name
        command: Shell command being executed
        state: Current process state
        pid: System process ID
        started_at: When process started
        completed_at: When process finished
        exit_code: Process exit code
        output: Captured stdout/stderr
        metadata: Additional process context
    """
    process_id: str
    process_type: ProcessType
    name: str
    command: str
    state: ProcessState = ProcessState.STARTING
    pid: Optional[int] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    output: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            CoreProcessManager (Plugin)                      │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Process Registry                                     │  │
│  │  process_id → BackgroundProcess                       │  │
│  │  • jules_123 → BackgroundProcess(type=JULES, ...)    │  │
│  │  • test_456 → BackgroundProcess(type=TEST, ...)      │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Process Pool (asyncio.create_subprocess_shell)       │  │
│  │  Manages actual OS processes                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Monitoring Loop                                      │  │
│  │  • Polls process status                               │  │
│  │  • Captures output                                    │  │
│  │  • Emits events on state changes                      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
            ↓ Events                    ↑ Control
┌──────────────────────┐    ┌──────────────────────┐
│  Event Bus           │    │  Task Queue          │
│  • PROCESS_STARTED   │    │  • start_process()   │
│  • PROCESS_STOPPED   │    │  • stop_process()    │
│  • PROCESS_FAILED    │    │  • get_status()      │
└──────────────────────┘    └──────────────────────┘
```

---

## 🔧 API Design

### **Tool Definitions**

```python
{
    "type": "function",
    "function": {
        "name": "start_background_process",
        "description": "Start a long-running background process (Jules, tests, builds)",
        "parameters": {
            "type": "object",
            "properties": {
                "process_type": {
                    "type": "string",
                    "enum": ["jules_session", "test_suite", "build", "server", "analysis", "custom"],
                    "description": "Type of process to start"
                },
                "name": {
                    "type": "string",
                    "description": "Human-readable name for the process"
                },
                "command": {
                    "type": "string",
                    "description": "Shell command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Maximum runtime in seconds (0 = no timeout)",
                    "default": 0
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional context (session_id, test_file, etc.)"
                }
            },
            "required": ["process_type", "name", "command"]
        }
    }
}

{
    "type": "function",
    "function": {
        "name": "get_process_status",
        "description": "Get current status of a background process",
        "parameters": {
            "type": "object",
            "properties": {
                "process_id": {
                    "type": "string",
                    "description": "Process ID to query"
                }
            },
            "required": ["process_id"]
        }
    }
}

{
    "type": "function",
    "function": {
        "name": "stop_background_process",
        "description": "Stop a running background process",
        "parameters": {
            "type": "object",
            "properties": {
                "process_id": {
                    "type": "string",
                    "description": "Process ID to stop"
                },
                "force": {
                    "type": "boolean",
                    "description": "Use SIGKILL instead of SIGTERM",
                    "default": false
                }
            },
            "required": ["process_id"]
        }
    }
}

{
    "type": "function",
    "function": {
        "name": "list_background_processes",
        "description": "List all active background processes",
        "parameters": {
            "type": "object",
            "properties": {
                "filter_type": {
                    "type": "string",
                    "enum": ["all", "running", "completed", "failed"],
                    "description": "Filter by process state",
                    "default": "all"
                }
            }
        }
    }
}
```

---

## 📡 Event Emissions

The Process Manager emits events to the Event Bus:

```python
# Process started
Event(
    event_type=EventType.PROCESS_STARTED,
    source="core_process_manager",
    priority=EventPriority.NORMAL,
    data={
        "process_id": "jules_abc123",
        "process_type": "jules_session",
        "name": "Implement login feature",
        "command": "jules session create --prompt '...'",
        "pid": 12345
    }
)

# Process completed
Event(
    event_type=EventType.PROCESS_STOPPED,
    source="core_process_manager",
    priority=EventPriority.HIGH,
    data={
        "process_id": "jules_abc123",
        "exit_code": 0,
        "duration": 123.45,
        "output": "Task completed successfully..."
    }
)

# Process failed
Event(
    event_type=EventType.PROCESS_FAILED,
    source="core_process_manager",
    priority=EventPriority.HIGH,
    data={
        "process_id": "test_def456",
        "exit_code": 1,
        "error": "AssertionError: test_login failed",
        "output": "Full traceback..."
    }
)
```

---

## 🔌 Integration with Existing Systems

### **Jules Monitor Integration**
The existing `cognitive_jules_monitor` can be enhanced to use Process Manager:

```python
# OLD: Direct subprocess management
subprocess.run(["jules", "session", "status", session_id])

# NEW: Use Process Manager + Events
process_manager.start_background_process(
    process_type=ProcessType.JULES_SESSION,
    name=f"Jules: {task_title}",
    command=f"jules session create --prompt '{prompt}'",
    metadata={"session_id": session_id}
)

# Subscribe to completion event
event_bus.subscribe(EventType.PROCESS_STOPPED, handle_jules_completion)
```

---

## ✅ Implementation Checklist

**Phase 2.1: Core Process Manager (Day 1-2)**
- [ ] Create `plugins/core_process_manager.py`
- [ ] Implement `BackgroundProcess` dataclass
- [ ] Implement `CoreProcessManager` plugin
- [ ] Add `start_background_process()` method
- [ ] Add `get_process_status()` method
- [ ] Add `stop_background_process()` method
- [ ] Add `list_background_processes()` method
- [ ] Implement monitoring loop
- [ ] Add event emissions
- [ ] Write unit tests

**Phase 2.2: Jules Integration (Day 2-3)**
- [ ] Update `cognitive_jules_monitor` to use Process Manager
- [ ] Add Jules-specific event handlers
- [ ] Implement auto-result pulling on completion
- [ ] Add Jules CLI integration for results

**Phase 2.3: Test Execution Support (Day 3-4)**
- [ ] Add pytest execution support
- [ ] Capture test results and failures
- [ ] Emit test completion events
- [ ] Add test failure analysis

**Phase 2.4: E2E Testing (Day 4)**
- [ ] Test Jules session monitoring
- [ ] Test pytest execution
- [ ] Test concurrent process management
- [ ] Test graceful shutdown

---

## 🎯 Success Criteria

1. ✅ Can start Jules sessions as background processes
2. ✅ Events are emitted on process state changes
3. ✅ Process output is captured and accessible
4. ✅ Processes can be stopped gracefully
5. ✅ Multiple concurrent processes can run
6. ✅ Integration with existing Jules monitor works
7. ✅ All tests pass (>90% coverage)

---

## 📚 Related Documents

- `docs/en/AUTONOMOUS_MVP_ROADMAP.md` - Overall roadmap
- `docs/en/design/EVENT_SYSTEM.md` - Event architecture
- `docs/en/design/TASK_QUEUE.md` - Task management
- `plugins/cognitive_jules_monitor.py` - Existing Jules monitoring

---

**Status:** Ready for Implementation  
**Estimated Time:** 3-4 days  
**Priority:** HIGH
