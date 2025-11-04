# Guardrails Design Specification

**Version:** 1.0  
**Date:** 2025-11-03  
**Status:** Design Specification  
**Phase:** 1 - Continuous Loop  
**Author:** Sophia AI Agent

---

## 📋 Overview

Guardrails are safety mechanisms that prevent Sophia from causing harm, violating constraints, or operating outside acceptable boundaries during autonomous operation. This spec defines the comprehensive guardrail system for the event-driven architecture.

### **Core Principles**
Based on Sophia's DNA (`docs/en/AGENTS.md` and `config/prompts/sophia_dna.txt`):

1. **Ahimsa (Non-Harm)** - Never cause harm or damage
2. **Satya (Truth)** - Operate transparently, never deceive
3. **Kaizen (Continuous Improvement)** - Learn and improve within safe boundaries

---

## 🎯 Guardrail Categories

### **1. Resource Guardrails**
Prevent resource exhaustion and budget violations.

### **2. Security Guardrails**
Prevent unauthorized access, data leaks, and security violations.

### **3. Operational Guardrails**
Ensure safe execution of tasks and prevent system damage.

### **4. Ethical Guardrails**
Enforce DNA principles and prevent harmful actions.

### **5. Performance Guardrails**
Prevent degradation and ensure responsive operation.

---

## 🛡️ Resource Guardrails

### **Budget Limits**

```python
# core/guardrails/budget_guardrail.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import logging

@dataclass
class BudgetLimit:
    """Budget constraints for LLM usage"""
    daily_limit: float = 1.00        # $1/day base
    monthly_limit: float = 30.00     # $30/month hard limit
    per_task_limit: float = 0.50     # $0.50/task max
    emergency_reserve: float = 5.00  # Emergency reserve
    
class BudgetGuardrail:
    """
    Enforces budget limits on LLM usage.
    
    Tracks spending and prevents operations that would exceed limits.
    """
    
    def __init__(self, limits: BudgetLimit):
        self.logger = logging.getLogger("sophia.guardrails.budget")
        self.limits = limits
        
        # Spending tracking
        self.daily_spent = 0.0
        self.monthly_spent = 0.0
        self.last_reset_daily = datetime.now()
        self.last_reset_monthly = datetime.now()
        
        # Warning thresholds
        self.daily_warning_threshold = 0.80  # 80% of daily limit
        self.monthly_warning_threshold = 0.90  # 90% of monthly limit
    
    def check_budget(self, estimated_cost: float) -> tuple[bool, Optional[str]]:
        """
        Check if operation is within budget.
        
        Args:
            estimated_cost: Estimated cost of operation
        
        Returns:
            (allowed, reason) - True if within budget, False with reason if not
        """
        # Reset counters if needed
        self._reset_counters()
        
        # Check per-task limit
        if estimated_cost > self.limits.per_task_limit:
            return False, f"Task cost ${estimated_cost:.2f} exceeds per-task limit ${self.limits.per_task_limit:.2f}"
        
        # Check daily limit
        if self.daily_spent + estimated_cost > self.limits.daily_limit:
            return False, f"Daily budget exceeded (${self.daily_spent:.2f}/${self.limits.daily_limit:.2f})"
        
        # Check monthly limit
        if self.monthly_spent + estimated_cost > self.limits.monthly_limit:
            return False, f"Monthly budget exceeded (${self.monthly_spent:.2f}/${self.limits.monthly_limit:.2f})"
        
        # Check warnings
        if self.daily_spent + estimated_cost > self.limits.daily_limit * self.daily_warning_threshold:
            self.logger.warning(
                f"Approaching daily limit: ${self.daily_spent:.2f}/${self.limits.daily_limit:.2f}"
            )
        
        if self.monthly_spent + estimated_cost > self.limits.monthly_limit * self.monthly_warning_threshold:
            self.logger.warning(
                f"Approaching monthly limit: ${self.monthly_spent:.2f}/${self.limits.monthly_limit:.2f}"
            )
        
        return True, None
    
    def record_spending(self, actual_cost: float):
        """Record actual spending"""
        self.daily_spent += actual_cost
        self.monthly_spent += actual_cost
        
        self.logger.info(
            f"Spent ${actual_cost:.4f} | "
            f"Daily: ${self.daily_spent:.2f}/${self.limits.daily_limit:.2f} | "
            f"Monthly: ${self.monthly_spent:.2f}/${self.limits.monthly_limit:.2f}"
        )
    
    def _reset_counters(self):
        """Reset daily/monthly counters if needed"""
        now = datetime.now()
        
        # Reset daily
        if now - self.last_reset_daily > timedelta(days=1):
            self.daily_spent = 0.0
            self.last_reset_daily = now
            self.logger.info("Daily budget counter reset")
        
        # Reset monthly
        if now.month != self.last_reset_monthly.month:
            self.monthly_spent = 0.0
            self.last_reset_monthly = now
            self.logger.info("Monthly budget counter reset")
    
    def can_use_emergency_reserve(self) -> bool:
        """Check if emergency reserve can be used"""
        return self.monthly_spent < self.limits.monthly_limit + self.limits.emergency_reserve
```

### **Memory Limits**

```python
# core/guardrails/memory_guardrail.py

import psutil
import logging

class MemoryGuardrail:
    """
    Enforces memory usage limits.
    
    Prevents memory exhaustion by monitoring usage and triggering cleanup.
    """
    
    def __init__(self, max_memory_mb: int = 20480):  # 20GB default
        self.logger = logging.getLogger("sophia.guardrails.memory")
        self.max_memory_mb = max_memory_mb
        self.warning_threshold = 0.80  # 80% of limit
        self.critical_threshold = 0.95  # 95% of limit
    
    def check_memory(self) -> tuple[bool, Optional[str]]:
        """
        Check current memory usage.
        
        Returns:
            (ok, reason) - True if within limits, False with reason if exceeded
        """
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        usage_percent = memory_mb / self.max_memory_mb
        
        if usage_percent > 1.0:
            return False, f"Memory limit exceeded: {memory_mb:.0f}MB/{self.max_memory_mb}MB"
        
        if usage_percent > self.critical_threshold:
            self.logger.error(
                f"CRITICAL: Memory usage at {usage_percent*100:.1f}% "
                f"({memory_mb:.0f}MB/{self.max_memory_mb}MB)"
            )
            # Trigger emergency cleanup
            self._trigger_emergency_cleanup()
            return True, "Critical memory - cleanup triggered"
        
        if usage_percent > self.warning_threshold:
            self.logger.warning(
                f"Memory usage at {usage_percent*100:.1f}% "
                f"({memory_mb:.0f}MB/{self.max_memory_mb}MB)"
            )
        
        return True, None
    
    def _trigger_emergency_cleanup(self):
        """Trigger emergency memory cleanup"""
        # Publish event for cleanup
        # Event handlers will:
        # - Clear old event history
        # - Compress memory database
        # - Clear caches
        # - Pause low-priority tasks
        pass
```

### **Task Queue Limits**

```python
# core/guardrails/task_queue_guardrail.py

class TaskQueueGuardrail:
    """Prevents task queue overflow"""
    
    def __init__(self, max_queue_size: int = 1000, max_concurrent: int = 10):
        self.logger = logging.getLogger("sophia.guardrails.task_queue")
        self.max_queue_size = max_queue_size
        self.max_concurrent = max_concurrent
    
    def check_can_add_task(self, current_queue_size: int, current_running: int) -> tuple[bool, Optional[str]]:
        """Check if new task can be added"""
        
        if current_queue_size >= self.max_queue_size:
            return False, f"Task queue full ({current_queue_size}/{self.max_queue_size})"
        
        if current_running >= self.max_concurrent:
            return False, f"Too many concurrent tasks ({current_running}/{self.max_concurrent})"
        
        return True, None
```

---

## 🔒 Security Guardrails

### **File System Access**

```python
# core/guardrails/filesystem_guardrail.py

import os
from pathlib import Path
from typing import List
import logging

class FileSystemGuardrail:
    """
    Enforces safe file system access.
    
    Prevents access to sensitive directories and files.
    """
    
    def __init__(self, workspace_root: str):
        self.logger = logging.getLogger("sophia.guardrails.filesystem")
        self.workspace_root = Path(workspace_root).resolve()
        
        # Blacklisted directories (cannot access)
        self.blacklist = [
            "/etc",
            "/root",
            "/boot",
            "/sys",
            "/proc",
            "~/.ssh",
            "~/.aws",
            "~/.config/gh"  # GitHub CLI credentials
        ]
        
        # Whitelist patterns (can access)
        self.whitelist_patterns = [
            str(self.workspace_root),  # Workspace root
            "/tmp/sophia-*",           # Temp files
        ]
        
        # Protected files (read-only or restricted)
        self.protected_files = [
            "config/autonomy.yaml",    # Read-only unless HITL approves
            "docs/en/AGENTS.md",       # DNA - immutable
            "core/kernel.py"           # Core - requires HITL approval
        ]
    
    def check_access(self, path: str, operation: str = "read") -> tuple[bool, Optional[str]]:
        """
        Check if file system access is allowed.
        
        Args:
            path: Path to check
            operation: "read", "write", "delete", "execute"
        
        Returns:
            (allowed, reason)
        """
        path = Path(path).resolve()
        
        # Check blacklist
        for blacklisted in self.blacklist:
            blacklisted_path = Path(blacklisted).expanduser().resolve()
            if path == blacklisted_path or blacklisted_path in path.parents:
                return False, f"Access denied: {path} is in blacklisted directory {blacklisted}"
        
        # Check whitelist
        allowed = False
        for pattern in self.whitelist_patterns:
            pattern_path = Path(pattern).expanduser().resolve()
            if path == pattern_path or pattern_path in path.parents:
                allowed = True
                break
        
        if not allowed:
            return False, f"Access denied: {path} not in whitelisted directories"
        
        # Check protected files
        relative_path = path.relative_to(self.workspace_root) if self.workspace_root in path.parents else None
        
        if relative_path and str(relative_path) in self.protected_files:
            if operation in ["write", "delete"]:
                return False, f"Protected file: {relative_path} requires HITL approval for {operation}"
        
        return True, None
    
    def check_workspace_boundary(self, path: str) -> bool:
        """Check if path is within workspace"""
        path = Path(path).resolve()
        return self.workspace_root in path.parents or path == self.workspace_root
```

### **Git Operations**

```python
# core/guardrails/git_guardrail.py

class GitGuardrail:
    """
    Enforces safe git operations.
    
    Prevents direct commits to master, force pushes, etc.
    """
    
    def __init__(self, autonomous_branch_prefix: str = "master-sophia/"):
        self.logger = logging.getLogger("sophia.guardrails.git")
        self.autonomous_branch_prefix = autonomous_branch_prefix
        self.protected_branches = ["master", "main", "production"]
    
    def check_operation(self, operation: str, branch: str, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Check if git operation is allowed.
        
        Args:
            operation: "commit", "push", "force_push", "merge", "delete_branch"
            branch: Target branch
        
        Returns:
            (allowed, reason)
        """
        # Never allow operations on protected branches
        if branch in self.protected_branches:
            if operation in ["commit", "push", "force_push"]:
                return False, f"Cannot {operation} to protected branch {branch}"
        
        # Force push only allowed on autonomous branches
        if operation == "force_push":
            if not branch.startswith(self.autonomous_branch_prefix):
                return False, f"Force push only allowed on {self.autonomous_branch_prefix}* branches"
        
        # Merge to protected branches requires HITL
        if operation == "merge" and kwargs.get("target_branch") in self.protected_branches:
            return False, f"Merging to {kwargs['target_branch']} requires HITL approval (use PR)"
        
        return True, None
```

### **External API Access**

```python
# core/guardrails/api_guardrail.py

class APIGuardrail:
    """
    Enforces safe external API access.
    
    Rate limiting, allowed domains, etc.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("sophia.guardrails.api")
        
        # Allowed API domains
        self.allowed_domains = [
            "api.openrouter.ai",
            "api.tavily.com",
            "api.github.com",
            "localhost",
            "127.0.0.1"
        ]
        
        # Rate limits (requests per minute)
        self.rate_limits = {
            "api.openrouter.ai": 60,
            "api.tavily.com": 30,
            "api.github.com": 60
        }
    
    def check_api_call(self, url: str) -> tuple[bool, Optional[str]]:
        """Check if API call is allowed"""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc
        
        if domain not in self.allowed_domains:
            return False, f"API domain not allowed: {domain}"
        
        # Check rate limit
        # ... implementation ...
        
        return True, None
```

---

## ⚙️ Operational Guardrails

### **Task Execution Safety**

```python
# core/guardrails/execution_guardrail.py

class ExecutionGuardrail:
    """
    Enforces safe task execution.
    
    Prevents dangerous operations, infinite loops, etc.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("sophia.guardrails.execution")
        
        # Dangerous bash commands
        self.dangerous_commands = [
            "rm -rf /",
            "mkfs",
            "dd if=/dev/zero",
            ":(){ :|:& };:",  # Fork bomb
            "chmod -R 777 /",
            "sudo rm",
        ]
        
        # Task timeouts
        self.default_timeout = 300  # 5 minutes
        self.max_timeout = 3600     # 1 hour max
    
    def check_bash_command(self, command: str) -> tuple[bool, Optional[str]]:
        """Check if bash command is safe"""
        command_lower = command.lower()
        
        # Check for dangerous patterns
        for dangerous in self.dangerous_commands:
            if dangerous in command_lower:
                return False, f"Dangerous command detected: {dangerous}"
        
        # Check for destructive flags
        if "rm" in command_lower and "-rf" in command_lower and "/" in command_lower:
            return False, "Potentially destructive rm -rf command"
        
        # Check for sudo without specific command
        if command_lower.strip() == "sudo":
            return False, "Bare 'sudo' not allowed - must specify command"
        
        return True, None
    
    def check_task_timeout(self, timeout: Optional[float]) -> tuple[bool, Optional[str]]:
        """Check if task timeout is reasonable"""
        if timeout is None:
            # Use default
            return True, None
        
        if timeout > self.max_timeout:
            return False, f"Timeout {timeout}s exceeds maximum {self.max_timeout}s"
        
        return True, None
```

### **Infinite Loop Detection**

```python
# core/guardrails/loop_guardrail.py

from collections import defaultdict
from datetime import datetime, timedelta

class LoopGuardrail:
    """
    Detects and prevents infinite loops.
    
    Tracks repeated operations and breaks if threshold exceeded.
    """
    
    def __init__(self, max_iterations: int = 100, time_window: int = 60):
        self.logger = logging.getLogger("sophia.guardrails.loop")
        self.max_iterations = max_iterations
        self.time_window = time_window  # seconds
        
        # Track operation counts
        self.operation_counts = defaultdict(list)  # operation_id → [timestamps]
    
    def check_iteration(self, operation_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if operation is in infinite loop.
        
        Args:
            operation_id: Unique ID for this operation (e.g., "task_123_retry")
        
        Returns:
            (ok, reason)
        """
        now = datetime.now()
        
        # Add this iteration
        self.operation_counts[operation_id].append(now)
        
        # Clean old iterations
        self.operation_counts[operation_id] = [
            ts for ts in self.operation_counts[operation_id]
            if now - ts < timedelta(seconds=self.time_window)
        ]
        
        # Check count
        count = len(self.operation_counts[operation_id])
        
        if count > self.max_iterations:
            return False, f"Infinite loop detected: {operation_id} executed {count} times in {self.time_window}s"
        
        if count > self.max_iterations * 0.8:
            self.logger.warning(
                f"Approaching loop limit: {operation_id} executed {count}/{self.max_iterations} times"
            )
        
        return True, None
```

---

## 🧭 Ethical Guardrails

### **DNA Enforcement**

```python
# core/guardrails/dna_guardrail.py

class DNAGuardrail:
    """
    Enforces Sophia's DNA principles.
    
    Based on docs/en/AGENTS.md and config/prompts/sophia_dna.txt
    """
    
    def __init__(self):
        self.logger = logging.getLogger("sophia.guardrails.dna")
        
        # Core principles
        self.principles = {
            "ahimsa": "Non-harm - prevent damage to systems, data, or users",
            "satya": "Truthfulness - operate transparently, never deceive",
            "kaizen": "Continuous improvement - learn within safe boundaries"
        }
    
    def check_action(self, action: str, context: dict) -> tuple[bool, Optional[str]]:
        """
        Check if action aligns with DNA.
        
        Args:
            action: Description of action to take
            context: Additional context
        
        Returns:
            (allowed, reason)
        """
        action_lower = action.lower()
        
        # Ahimsa - Non-harm checks
        harmful_keywords = ["delete all", "drop database", "format", "destroy", "corrupt"]
        if any(keyword in action_lower for keyword in harmful_keywords):
            return False, f"Violates Ahimsa (non-harm): potentially destructive action"
        
        # Satya - Truthfulness checks
        deceptive_keywords = ["hide", "conceal", "fake", "mislead", "lie"]
        if any(keyword in action_lower for keyword in deceptive_keywords):
            return False, f"Violates Satya (truthfulness): potentially deceptive action"
        
        # Kaizen - Safe improvement checks
        # Improvements must be reversible and tested
        if "improve" in action_lower or "optimize" in action_lower:
            if not context.get("has_tests"):
                self.logger.warning(
                    "Improvement without tests - proceeding with caution (Kaizen)"
                )
        
        return True, None
    
    def check_immutable_files(self, file_path: str) -> tuple[bool, Optional[str]]:
        """Check if file is immutable per DNA"""
        immutable_files = [
            "docs/en/AGENTS.md",
            "docs/cs/AGENTS.md",
            "config/prompts/sophia_dna.txt"
        ]
        
        if file_path in immutable_files:
            return False, f"DNA file {file_path} is immutable - requires creator modification"
        
        return True, None
```

### **Human-in-the-Loop (HITL) Requirements**

```python
# core/guardrails/hitl_guardrail.py

class HITLGuardrail:
    """
    Enforces Human-in-the-Loop requirements.
    
    Some operations require explicit human approval.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("sophia.guardrails.hitl")
        
        # Operations requiring HITL
        self.hitl_operations = {
            "merge_to_master": "Merging to master branch",
            "modify_core": "Modifying core/ files",
            "change_dna": "Changing DNA files",
            "large_budget": "Operation exceeding budget limits",
            "delete_data": "Deleting important data",
            "external_communication": "Communicating externally (email, etc.)"
        }
    
    def requires_approval(self, operation: str, context: dict) -> tuple[bool, str]:
        """
        Check if operation requires human approval.
        
        Args:
            operation: Operation type
            context: Additional context
        
        Returns:
            (requires_approval, reason)
        """
        if operation in self.hitl_operations:
            return True, self.hitl_operations[operation]
        
        # Budget-based HITL
        if context.get("estimated_cost", 0) > 1.0:  # $1 threshold
            return True, f"High cost operation (${context['estimated_cost']:.2f})"
        
        # File modification HITL
        if operation == "modify_file":
            if context.get("file_path", "").startswith("core/"):
                return True, "Modifying core system files"
        
        return False, ""
    
    async def request_approval(self, operation: str, reason: str, details: dict) -> bool:
        """
        Request human approval for operation.
        
        Args:
            operation: Operation requiring approval
            reason: Why approval is needed
            details: Operation details
        
        Returns:
            True if approved, False if denied
        """
        self.logger.info(
            f"\n{'='*60}\n"
            f"HUMAN APPROVAL REQUIRED\n"
            f"Operation: {operation}\n"
            f"Reason: {reason}\n"
            f"Details: {details}\n"
            f"{'='*60}\n"
        )
        
        # In terminal mode, prompt user
        # In autonomous mode, create GitHub issue and wait
        # ... implementation ...
        
        return False  # Default to deny
```

---

## 📊 Performance Guardrails

### **Response Time Monitoring**

```python
# core/guardrails/performance_guardrail.py

class PerformanceGuardrail:
    """
    Monitors and enforces performance requirements.
    
    Ensures system remains responsive.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("sophia.guardrails.performance")
        
        # Performance targets
        self.max_response_time = 5.0  # seconds for user input
        self.max_event_latency = 0.1  # seconds for event processing
        self.max_cpu_usage = 80.0     # percent
    
    def check_response_time(self, duration: float) -> tuple[bool, Optional[str]]:
        """Check if response time is acceptable"""
        if duration > self.max_response_time:
            return False, f"Response time {duration:.2f}s exceeds limit {self.max_response_time}s"
        
        if duration > self.max_response_time * 0.8:
            self.logger.warning(f"Slow response: {duration:.2f}s")
        
        return True, None
    
    def check_cpu_usage(self) -> tuple[bool, Optional[str]]:
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        if cpu_percent > self.max_cpu_usage:
            return False, f"CPU usage {cpu_percent:.1f}% exceeds limit {self.max_cpu_usage}%"
        
        return True, None
```

---

## 🔧 Guardrail Manager

Central manager for all guardrails.

```python
# core/guardrails/manager.py

from typing import Dict, List, Tuple, Optional
import logging

class GuardrailManager:
    """
    Central manager for all guardrails.
    
    Coordinates checking across all guardrail types.
    """
    
    def __init__(self, context: SharedContext):
        self.logger = logging.getLogger("sophia.guardrails")
        self.context = context
        
        # Initialize all guardrails
        self.budget = BudgetGuardrail(BudgetLimit())
        self.memory = MemoryGuardrail(max_memory_mb=20480)
        self.filesystem = FileSystemGuardrail(workspace_root="/workspaces/sophia")
        self.git = GitGuardrail()
        self.api = APIGuardrail()
        self.execution = ExecutionGuardrail()
        self.loop = LoopGuardrail()
        self.dna = DNAGuardrail()
        self.hitl = HITLGuardrail()
        self.performance = PerformanceGuardrail()
        
        # Violation tracking
        self.violations: List[dict] = []
    
    def check_all(self, operation_type: str, **kwargs) -> Tuple[bool, List[str]]:
        """
        Run all relevant guardrail checks for an operation.
        
        Args:
            operation_type: Type of operation to check
            **kwargs: Operation-specific parameters
        
        Returns:
            (allowed, [reasons]) - True if all checks pass, reasons if not
        """
        reasons = []
        
        # Memory check (always)
        ok, reason = self.memory.check_memory()
        if not ok:
            reasons.append(f"Memory: {reason}")
        
        # Performance check (always)
        ok, reason = self.performance.check_cpu_usage()
        if not ok:
            reasons.append(f"Performance: {reason}")
        
        # Operation-specific checks
        if operation_type == "llm_call":
            ok, reason = self.budget.check_budget(kwargs.get("estimated_cost", 0))
            if not ok:
                reasons.append(f"Budget: {reason}")
        
        elif operation_type == "file_access":
            ok, reason = self.filesystem.check_access(
                kwargs.get("path", ""),
                kwargs.get("operation", "read")
            )
            if not ok:
                reasons.append(f"FileSystem: {reason}")
            
            # DNA check for immutable files
            ok, reason = self.dna.check_immutable_files(kwargs.get("path", ""))
            if not ok:
                reasons.append(f"DNA: {reason}")
        
        elif operation_type == "git_operation":
            ok, reason = self.git.check_operation(
                kwargs.get("operation", ""),
                kwargs.get("branch", ""),
                **kwargs
            )
            if not ok:
                reasons.append(f"Git: {reason}")
        
        elif operation_type == "bash_command":
            ok, reason = self.execution.check_bash_command(kwargs.get("command", ""))
            if not ok:
                reasons.append(f"Execution: {reason}")
        
        elif operation_type == "api_call":
            ok, reason = self.api.check_api_call(kwargs.get("url", ""))
            if not ok:
                reasons.append(f"API: {reason}")
        
        # DNA check (always for actions)
        if "action" in kwargs:
            ok, reason = self.dna.check_action(kwargs["action"], kwargs)
            if not ok:
                reasons.append(f"DNA: {reason}")
        
        # HITL check
        requires_hitl, hitl_reason = self.hitl.requires_approval(operation_type, kwargs)
        if requires_hitl:
            reasons.append(f"HITL: {hitl_reason}")
        
        # Log violations
        if reasons:
            violation = {
                "timestamp": datetime.now(),
                "operation": operation_type,
                "reasons": reasons,
                "context": kwargs
            }
            self.violations.append(violation)
            self.logger.warning(f"Guardrail violation: {operation_type} - {reasons}")
        
        return len(reasons) == 0, reasons
    
    def get_violations(self, limit: int = 100) -> List[dict]:
        """Get recent violations"""
        return self.violations[-limit:]
```

---

## 🧪 Testing Guardrails

### **Unit Tests**

```python
# tests/core/test_guardrails.py

import pytest
from core.guardrails.manager import GuardrailManager
from core.guardrails.budget_guardrail import BudgetLimit

def test_budget_guardrail():
    """Test budget limits"""
    budget = BudgetGuardrail(BudgetLimit(daily_limit=1.0))
    
    # Should allow small cost
    ok, reason = budget.check_budget(0.10)
    assert ok
    
    # Should block if exceeds daily
    ok, reason = budget.check_budget(1.50)
    assert not ok
    assert "daily" in reason.lower()

def test_filesystem_guardrail():
    """Test file system access"""
    fs = FileSystemGuardrail("/workspaces/sophia")
    
    # Should allow workspace access
    ok, reason = fs.check_access("/workspaces/sophia/README.md", "read")
    assert ok
    
    # Should block /etc access
    ok, reason = fs.check_access("/etc/passwd", "read")
    assert not ok

def test_dna_guardrail():
    """Test DNA enforcement"""
    dna = DNAGuardrail()
    
    # Should block harmful actions
    ok, reason = dna.check_action("delete all users", {})
    assert not ok
    assert "ahimsa" in reason.lower()
    
    # Should allow safe actions
    ok, reason = dna.check_action("read configuration", {})
    assert ok
```

---

## ✅ Success Criteria

- [ ] All guardrails implemented and tested
- [ ] Budget limits enforced (no overages)
- [ ] Memory stays under 20GB
- [ ] No access to blacklisted directories
- [ ] No direct commits to master
- [ ] DNA files remain immutable
- [ ] HITL approval working
- [ ] Violation logging functional
- [ ] Performance maintained

---

## 🔗 Related Documents

- `EVENT_SYSTEM.md` - Event system design
- `TASK_QUEUE.md` - Task queue design
- `LOOP_MIGRATION.md` - Migration strategy
- `docs/en/AGENTS.md` - AI agent DNA
- `config/autonomy.yaml` - Autonomy configuration

---

**Status:** Ready for Implementation ✅  
**Next Steps:** Implement guardrails alongside event system and task queue
