"""
Core Process Manager Plugin

Manages background processes (Jules sessions, tests, builds) with event-driven
monitoring and automatic status tracking.

Created: 2025-11-03
Phase: 2 - Background Process Management
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any, List

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.events import Event, EventType, EventPriority

logger = logging.getLogger(__name__)


class ProcessType(Enum):
    """Types of background processes."""
    JULES_SESSION = "jules_session"
    TEST_SUITE = "test_suite"
    BUILD = "build"
    SERVER = "server"
    ANALYSIS = "analysis"
    CUSTOM = "custom"


class ProcessState(Enum):
    """Process lifecycle states."""
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


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
        error_output: Captured stderr separately
        metadata: Additional process context
        subprocess: Actual asyncio subprocess object
    """
    process_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    process_type: ProcessType = ProcessType.CUSTOM
    name: str = "unnamed_process"
    command: str = ""
    state: ProcessState = ProcessState.STARTING
    pid: Optional[int] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    output: str = ""
    error_output: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    subprocess: Optional[asyncio.subprocess.Process] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate process duration in seconds."""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_terminal(self) -> bool:
        """Check if process is in a terminal state."""
        return self.state in {
            ProcessState.COMPLETED,
            ProcessState.FAILED,
            ProcessState.TIMEOUT,
            ProcessState.CANCELLED
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "process_id": self.process_id,
            "process_type": self.process_type.value,
            "name": self.name,
            "command": self.command,
            "state": self.state.value,
            "pid": self.pid,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "exit_code": self.exit_code,
            "duration": self.duration,
            "output_length": len(self.output),
            "has_error": bool(self.error_output),
            "metadata": self.metadata
        }


class CoreProcessManager(BasePlugin):
    """
    Core Process Manager Plugin
    
    Manages background processes with event-driven monitoring.
    Provides unified interface for Jules sessions, tests, builds, etc.
    
    Tool Definitions:
    - start_background_process: Start a long-running process
    - get_process_status: Get current status of a process
    - stop_background_process: Stop a running process
    - list_background_processes: List all processes
    """
    
    @property
    def name(self) -> str:
        return "core_process_manager"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.CORE
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.processes: Dict[str, BackgroundProcess] = {}
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._context: Optional[SharedContext] = None
        self._running = False
    
    def setup(self, config: dict) -> None:
        """Setup the process manager."""
        self.logger = logging.getLogger(self.name)
        self.logger.info(
            "Core Process Manager initialized",
            extra={"plugin_name": self.name}
        )
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """Not used for process manager - uses tool methods instead."""
        return context
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Return tool definitions for LLM function calling.
        
        Returns:
            List of tool definition dictionaries
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "start_background_process",
                    "description": "Start a long-running background process (Jules sessions, tests, builds). Process runs asynchronously and emits events on status changes.",
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
            },
            {
                "type": "function",
                "function": {
                    "name": "get_process_status",
                    "description": "Get current status of a background process including output, state, and exit code",
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
            },
            {
                "type": "function",
                "function": {
                    "name": "stop_background_process",
                    "description": "Stop a running background process gracefully or forcefully",
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
                                "default": False
                            }
                        },
                        "required": ["process_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_background_processes",
                    "description": "List all background processes with optional filtering",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter_state": {
                                "type": "string",
                                "enum": ["all", "running", "completed", "failed"],
                                "description": "Filter by process state",
                                "default": "all"
                            }
                        }
                    }
                }
            }
        ]
    
    async def start_background_process(
        self,
        context: SharedContext,
        process_type: str,
        name: str,
        command: str,
        timeout: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a background process.
        
        Args:
            context: Shared context
            process_type: Type of process (jules_session, test_suite, etc.)
            name: Human-readable name
            command: Shell command to execute
            timeout: Maximum runtime in seconds (0 = no timeout)
            metadata: Additional context
            
        Returns:
            Dictionary with process_id and status
        """
        try:
            # Create process object
            process = BackgroundProcess(
                process_type=ProcessType(process_type),
                name=name,
                command=command,
                metadata=metadata or {}
            )
            
            # Store process
            self.processes[process.process_id] = process
            
            # Start subprocess
            process.subprocess = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            process.pid = process.subprocess.pid
            process.state = ProcessState.RUNNING
            
            self.logger.info(
                f"Started background process: {name} (PID: {process.pid})",
                extra={"plugin_name": self.name}
            )
            
            # Emit PROCESS_STARTED event
            if context.event_bus:
                context.event_bus.publish(Event(
                    event_type=EventType.PROCESS_STARTED,
                    source=self.name,
                    priority=EventPriority.NORMAL,
                    data={
                        "process_id": process.process_id,
                        "process_type": process_type,
                        "name": name,
                        "command": command,
                        "pid": process.pid
                    }
                ))
            
            # Start monitoring task
            monitor_task = asyncio.create_task(
                self._monitor_process(context, process, timeout)
            )
            self._monitoring_tasks[process.process_id] = monitor_task
            
            return {
                "success": True,
                "process_id": process.process_id,
                "pid": process.pid,
                "state": process.state.value,
                "message": f"Background process '{name}' started successfully"
            }
            
        except Exception as e:
            self.logger.error(
                f"Failed to start background process: {e}",
                exc_info=True,
                extra={"plugin_name": self.name}
            )
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to start process: {e}"
            }
    
    async def _monitor_process(
        self,
        context: SharedContext,
        process: BackgroundProcess,
        timeout: int
    ):
        """
        Monitor a background process until completion.
        
        Args:
            context: Shared context
            process: Process to monitor
            timeout: Maximum runtime (0 = no timeout)
        """
        try:
            # Wait for process with optional timeout
            if timeout > 0:
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.subprocess.communicate(),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    # Process timed out
                    process.state = ProcessState.TIMEOUT
                    process.subprocess.kill()
                    await process.subprocess.wait()
                    stdout, stderr = b"", b"Process timed out"
            else:
                # No timeout - wait indefinitely
                stdout, stderr = await process.subprocess.communicate()
            
            # Capture output
            process.output = stdout.decode('utf-8', errors='replace')
            process.error_output = stderr.decode('utf-8', errors='replace')
            process.exit_code = process.subprocess.returncode
            process.completed_at = datetime.now()
            
            # Determine final state
            if process.state != ProcessState.TIMEOUT:
                if process.exit_code == 0:
                    process.state = ProcessState.COMPLETED
                else:
                    process.state = ProcessState.FAILED
            
            self.logger.info(
                f"Process completed: {process.name} (exit code: {process.exit_code})",
                extra={"plugin_name": self.name}
            )
            
            # Emit completion event
            if context.event_bus:
                event_type = (
                    EventType.PROCESS_STOPPED if process.state == ProcessState.COMPLETED
                    else EventType.PROCESS_FAILED
                )
                
                context.event_bus.publish(Event(
                    event_type=event_type,
                    source=self.name,
                    priority=EventPriority.HIGH,
                    data={
                        "process_id": process.process_id,
                        "process_type": process.process_type.value,
                        "name": process.name,
                        "exit_code": process.exit_code,
                        "duration": process.duration,
                        "state": process.state.value,
                        "output": process.output[:1000],  # First 1000 chars
                        "error": process.error_output[:1000] if process.error_output else None
                    }
                ))
            
        except Exception as e:
            self.logger.error(
                f"Error monitoring process {process.name}: {e}",
                exc_info=True,
                extra={"plugin_name": self.name}
            )
            process.state = ProcessState.FAILED
            process.error_output = str(e)
        
        finally:
            # Cleanup monitoring task
            if process.process_id in self._monitoring_tasks:
                del self._monitoring_tasks[process.process_id]
    
    async def get_process_status(
        self,
        context: SharedContext,
        process_id: str
    ) -> Dict[str, Any]:
        """
        Get current status of a process.
        
        Args:
            context: Shared context
            process_id: Process ID to query
            
        Returns:
            Dictionary with process status
        """
        if process_id not in self.processes:
            return {
                "success": False,
                "error": f"Process {process_id} not found"
            }
        
        process = self.processes[process_id]
        return {
            "success": True,
            **process.to_dict(),
            "output": process.output,
            "error_output": process.error_output
        }
    
    async def stop_background_process(
        self,
        context: SharedContext,
        process_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Stop a running process.
        
        Args:
            context: Shared context
            process_id: Process ID to stop
            force: Use SIGKILL instead of SIGTERM
            
        Returns:
            Dictionary with stop status
        """
        if process_id not in self.processes:
            return {
                "success": False,
                "error": f"Process {process_id} not found"
            }
        
        process = self.processes[process_id]
        
        if process.is_terminal:
            return {
                "success": False,
                "error": f"Process already in terminal state: {process.state.value}"
            }
        
        try:
            if force:
                process.subprocess.kill()
            else:
                process.subprocess.terminate()
            
            process.state = ProcessState.CANCELLED
            
            self.logger.info(
                f"Stopped process: {process.name}",
                extra={"plugin_name": self.name}
            )
            
            return {
                "success": True,
                "process_id": process_id,
                "message": f"Process stopped {'forcefully' if force else 'gracefully'}"
            }
            
        except Exception as e:
            self.logger.error(
                f"Failed to stop process {process_id}: {e}",
                exc_info=True,
                extra={"plugin_name": self.name}
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_background_processes(
        self,
        context: SharedContext,
        filter_state: str = "all"
    ) -> Dict[str, Any]:
        """
        List all background processes.
        
        Args:
            context: Shared context
            filter_state: Filter by state (all, running, completed, failed)
            
        Returns:
            Dictionary with list of processes
        """
        processes = list(self.processes.values())
        
        # Apply filter
        if filter_state == "running":
            processes = [p for p in processes if p.state == ProcessState.RUNNING]
        elif filter_state == "completed":
            processes = [p for p in processes if p.state == ProcessState.COMPLETED]
        elif filter_state == "failed":
            processes = [p for p in processes if p.state == ProcessState.FAILED]
        
        return {
            "success": True,
            "count": len(processes),
            "processes": [p.to_dict() for p in processes]
        }
