"""
Cognitive Security Monitor Plugin

Proaktivní bezpečnostní monitoring - detekuje podezřelé vzory v běhu systému.
Výstup je POUZE informativní (neblokuje operace), slouží k visibility.

Author: Sophia Security Team
Created: 2025-10-27
"""

import re
import hashlib
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class SecurityEvent:
    """Security event representation."""
    
    SEVERITY_INFO = "INFO"
    SEVERITY_LOW = "LOW"
    SEVERITY_MEDIUM = "MEDIUM"
    SEVERITY_HIGH = "HIGH"
    SEVERITY_CRITICAL = "CRITICAL"
    
    def __init__(
        self,
        event_type: str,
        severity: str,
        description: str,
        details: Dict = None,
        timestamp: datetime = None
    ):
        self.event_type = event_type
        self.severity = severity
        self.description = description
        self.details = details or {}
        self.timestamp = timestamp or datetime.now()
    
    def __str__(self) -> str:
        return (
            f"[{self.severity}] {self.event_type}: {self.description} "
            f"({self.timestamp.strftime('%H:%M:%S')})"
        )
    
    def to_dict(self) -> Dict:
        return {
            "type": self.event_type,
            "severity": self.severity,
            "description": self.description,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class SecurityMonitor(BasePlugin):
    """
    Proaktivní bezpečnostní monitoring plugin.
    
    Sleduje:
    - Podezřelé příkazy (eval, exec, rm -rf, etc.)
    - Path traversal pokusy
    - Rapidní změny v file systému
    - Podezřelé LLM prompty
    - Anomální chování pluginů
    - Rate limiting útoky
    
    Output je POUZE informativní - plugin NEblokuje operace!
    """
    
    # Required BasePlugin properties
    name = "SecurityMonitor"
    plugin_type = PluginType.COGNITIVE  # Using existing type
    version = "1.0.0"
    
    def __init__(self):
        super().__init__()
        
        # Event storage (in-memory)
        self.events: deque = deque(maxlen=1000)  # Last 1000 events
        self.event_counts: Dict[str, int] = defaultdict(int)
        
        # Rate limiting tracking
        self.command_history: deque = deque(maxlen=100)
        self.file_access_history: deque = deque(maxlen=100)
        
        # Baseline patterns (learned during normal operation)
        self.known_safe_commands: Set[str] = set()
        self.known_file_patterns: Set[str] = set()
        
        # Attack patterns
        self.setup_attack_patterns()
        
        # File integrity baseline
        self.file_hashes: Dict[str, str] = {}
        self.last_integrity_check: Optional[datetime] = None
    
    def setup_attack_patterns(self):
        """Initialize attack detection patterns."""
        
        # Dangerous command patterns
        self.DANGEROUS_COMMANDS = [
            r'\brm\s+-rf\b',
            r'\bdd\s+if=',
            r'\b:\(\)\s*{\s*:\|:&\s*};',  # Fork bomb
            r'\bwget\b.*\|\s*sh\b',
            r'\bcurl\b.*\|\s*bash\b',
            r'\bnc\s+-[el]',  # Netcat
            r'\b/dev/tcp/',
            r'\bbase64\s+-d\b.*\|\s*sh\b',
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'__import__\s*\(',
        ]
        
        # Path traversal patterns
        self.PATH_TRAVERSAL_PATTERNS = [
            r'\.\./\.\.',
            r'%2e%2e%2f',
            r'\.\.\\',
            r'%252e%252e%255c',
        ]
        
        # Prompt injection patterns
        self.PROMPT_INJECTION_PATTERNS = [
            r'ignore\s+previous\s+instructions',
            r'disregard\s+all\s+prior',
            r'forget\s+everything',
            r'system\s*:\s*you\s+are\s+now',
            r'\[SYSTEM\]\s*override',
            r'</system>.*<system>',
        ]
        
        # Sensitive data patterns
        self.SENSITIVE_PATTERNS = [
            r'api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}',
            r'password\s*[:=]\s*["\'][^"\']{8,}',
            r'secret\s*[:=]\s*["\'][^"\']{8,}',
            r'token\s*[:=]\s*["\'][^"\']{20,}',
        ]
    
    def setup(self, config: dict):
        """Initialize monitoring with config."""
        self.enabled = config.get("enabled", True)
        self.report_interval = config.get("report_interval_seconds", 60)
        self.alert_threshold = config.get("alert_threshold", 3)
        
        # Compute baseline file hashes
        self._compute_file_integrity_baseline()
        
        logger.info(
            f"Security Monitor initialized "
            f"(reporting every {self.report_interval}s, "
            f"alert threshold: {self.alert_threshold})"
        )
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """Monitor current context for security anomalies."""
        
        if not self.enabled:
            return context
        
        events = []
        
        # 1. Monitor user input
        user_input = context.payload.get("user_input", "")
        if user_input:
            events.extend(self._check_user_input(user_input))
        
        # 2. Monitor planned commands
        plan = context.payload.get("plan", [])
        if plan:
            events.extend(self._check_plan_safety(plan))
        
        # 3. Monitor LLM response
        llm_response = context.payload.get("llm_response", "")
        if llm_response:
            events.extend(self._check_llm_response(llm_response))
        
        # 4. Monitor file operations
        if "file_path" in context.payload or "path" in context.payload:
            path = context.payload.get("file_path") or context.payload.get("path")
            events.extend(self._check_file_access(path))
        
        # 5. Rate limiting check
        events.extend(self._check_rate_limiting(context))
        
        # 6. Periodic integrity check
        events.extend(self._check_file_integrity())
        
        # Store events
        for event in events:
            self._record_event(event)
        
        # Add security report to context
        if events:
            context.payload["security_events"] = [e.to_dict() for e in events]
            context.payload["security_summary"] = self._generate_summary()
        
        return context
    
    def _check_user_input(self, user_input: str) -> List[SecurityEvent]:
        """Check user input for attacks."""
        events = []
        
        # Check for prompt injection
        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                events.append(SecurityEvent(
                    event_type="PROMPT_INJECTION",
                    severity=SecurityEvent.SEVERITY_HIGH,
                    description=f"Potential prompt injection detected",
                    details={
                        "pattern": pattern,
                        "input_sample": user_input[:100]
                    }
                ))
        
        # Check for path traversal
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, user_input):
                events.append(SecurityEvent(
                    event_type="PATH_TRAVERSAL",
                    severity=SecurityEvent.SEVERITY_MEDIUM,
                    description="Path traversal pattern detected in input",
                    details={"pattern": pattern}
                ))
        
        # Check for sensitive data exposure
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                events.append(SecurityEvent(
                    event_type="SENSITIVE_DATA",
                    severity=SecurityEvent.SEVERITY_MEDIUM,
                    description="Possible sensitive data in user input",
                    details={"pattern": "REDACTED"}
                ))
        
        return events
    
    def _check_plan_safety(self, plan: List[Dict]) -> List[SecurityEvent]:
        """Check execution plan for dangerous operations."""
        events = []
        
        for step in plan:
            action = step.get("action", "")
            tool = step.get("tool", "")
            params = str(step.get("parameters", {}))
            
            # Check dangerous commands
            if tool == "bash" or "command" in action.lower():
                for pattern in self.DANGEROUS_COMMANDS:
                    if re.search(pattern, params, re.IGNORECASE):
                        events.append(SecurityEvent(
                            event_type="DANGEROUS_COMMAND",
                            severity=SecurityEvent.SEVERITY_CRITICAL,
                            description=f"Dangerous command in plan: {action}",
                            details={
                                "tool": tool,
                                "pattern": pattern,
                                "step": step
                            }
                        ))
            
            # Check file operations
            if "delete" in action.lower() or "remove" in action.lower():
                events.append(SecurityEvent(
                    event_type="FILE_DELETION",
                    severity=SecurityEvent.SEVERITY_MEDIUM,
                    description=f"File deletion planned: {action}",
                    details={"step": step}
                ))
        
        return events
    
    def _check_llm_response(self, response: str) -> List[SecurityEvent]:
        """Check LLM response for anomalies."""
        events = []
        
        # Check for sensitive data in response
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                events.append(SecurityEvent(
                    event_type="LLM_DATA_LEAK",
                    severity=SecurityEvent.SEVERITY_HIGH,
                    description="LLM response may contain sensitive data",
                    details={"pattern": "REDACTED"}
                ))
        
        # Check for code injection in response
        if re.search(r'```(?:python|bash).*(?:eval|exec|__import__)', 
                     response, re.DOTALL | re.IGNORECASE):
            events.append(SecurityEvent(
                event_type="CODE_INJECTION_RESPONSE",
                severity=SecurityEvent.SEVERITY_MEDIUM,
                description="LLM suggested dangerous code",
                details={"language": "python/bash"}
            ))
        
        return events
    
    def _check_file_access(self, path: str) -> List[SecurityEvent]:
        """Monitor file access patterns."""
        events = []
        
        # Track access
        self.file_access_history.append({
            "path": path,
            "timestamp": datetime.now()
        })
        
        # Check path traversal
        if ".." in path or path.startswith("/"):
            events.append(SecurityEvent(
                event_type="SUSPICIOUS_PATH",
                severity=SecurityEvent.SEVERITY_MEDIUM,
                description=f"Suspicious file path: {path}",
                details={"path": path}
            ))
        
        # Check access to critical files
        critical_files = [
            "config/settings.yaml",
            "core/kernel.py",
            "core/plugin_manager.py",
            ".env"
        ]
        
        if any(critical in path for critical in critical_files):
            events.append(SecurityEvent(
                event_type="CRITICAL_FILE_ACCESS",
                severity=SecurityEvent.SEVERITY_HIGH,
                description=f"Access to critical file: {path}",
                details={"path": path}
            ))
        
        # Check rapid access (potential scanning)
        recent_accesses = [
            a for a in self.file_access_history
            if datetime.now() - a["timestamp"] < timedelta(seconds=5)
        ]
        
        if len(recent_accesses) > 20:
            events.append(SecurityEvent(
                event_type="RAPID_FILE_ACCESS",
                severity=SecurityEvent.SEVERITY_MEDIUM,
                description=f"Rapid file access detected ({len(recent_accesses)} in 5s)",
                details={"count": len(recent_accesses)}
            ))
        
        return events
    
    def _check_rate_limiting(self, context: SharedContext) -> List[SecurityEvent]:
        """Check for rate limiting attacks."""
        events = []
        
        # Track command
        self.command_history.append({
            "session_id": context.session_id,
            "timestamp": datetime.now()
        })
        
        # Check commands in last minute
        recent = [
            c for c in self.command_history
            if datetime.now() - c["timestamp"] < timedelta(seconds=60)
        ]
        
        if len(recent) > 50:
            events.append(SecurityEvent(
                event_type="RATE_LIMIT_EXCEEDED",
                severity=SecurityEvent.SEVERITY_HIGH,
                description=f"Possible DoS attack: {len(recent)} commands in 60s",
                details={"count": len(recent)}
            ))
        
        return events
    
    def _check_file_integrity(self) -> List[SecurityEvent]:
        """Periodic integrity check of critical files."""
        events = []
        
        # Only check every 5 minutes
        if (self.last_integrity_check and 
            datetime.now() - self.last_integrity_check < timedelta(minutes=5)):
            return events
        
        self.last_integrity_check = datetime.now()
        
        critical_files = [
            "config/settings.yaml",
            "core/kernel.py",
            "core/plugin_manager.py",
            "plugins/base_plugin.py",
        ]
        
        for filepath in critical_files:
            path = Path(filepath)
            if not path.exists():
                events.append(SecurityEvent(
                    event_type="FILE_MISSING",
                    severity=SecurityEvent.SEVERITY_CRITICAL,
                    description=f"Critical file missing: {filepath}",
                    details={"path": filepath}
                ))
                continue
            
            # Compute current hash
            with open(path, "rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Compare with baseline
            if filepath in self.file_hashes:
                if current_hash != self.file_hashes[filepath]:
                    events.append(SecurityEvent(
                        event_type="FILE_MODIFIED",
                        severity=SecurityEvent.SEVERITY_HIGH,
                        description=f"Critical file modified: {filepath}",
                        details={
                            "path": filepath,
                            "expected_hash": self.file_hashes[filepath][:16],
                            "actual_hash": current_hash[:16]
                        }
                    ))
        
        return events
    
    def _compute_file_integrity_baseline(self):
        """Compute SHA256 hashes of critical files."""
        critical_files = [
            "config/settings.yaml",
            "core/kernel.py",
            "core/plugin_manager.py",
            "plugins/base_plugin.py",
        ]
        
        for filepath in critical_files:
            path = Path(filepath)
            if path.exists():
                with open(path, "rb") as f:
                    self.file_hashes[filepath] = hashlib.sha256(f.read()).hexdigest()
    
    def _record_event(self, event: SecurityEvent):
        """Record security event."""
        self.events.append(event)
        self.event_counts[event.event_type] += 1
        
        # Log based on severity
        if event.severity == SecurityEvent.SEVERITY_CRITICAL:
            logger.error(f"🚨 CRITICAL: {event}")
        elif event.severity == SecurityEvent.SEVERITY_HIGH:
            logger.warning(f"⚠️  HIGH: {event}")
        elif event.severity == SecurityEvent.SEVERITY_MEDIUM:
            logger.warning(f"📊 MEDIUM: {event}")
        else:
            logger.info(f"ℹ️  {event.severity}: {event}")
    
    def _generate_summary(self) -> Dict:
        """Generate summary of recent security events."""
        
        # Events in last hour
        recent_events = [
            e for e in self.events
            if datetime.now() - e.timestamp < timedelta(hours=1)
        ]
        
        # Count by severity
        severity_counts = defaultdict(int)
        for event in recent_events:
            severity_counts[event.severity] += 1
        
        # Count by type
        type_counts = defaultdict(int)
        for event in recent_events:
            type_counts[event.event_type] += 1
        
        return {
            "total_events_last_hour": len(recent_events),
            "severity_breakdown": dict(severity_counts),
            "event_type_breakdown": dict(type_counts),
            "critical_count": severity_counts.get(SecurityEvent.SEVERITY_CRITICAL, 0),
            "high_count": severity_counts.get(SecurityEvent.SEVERITY_HIGH, 0),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_recent_events(self, limit: int = 20, min_severity: str = None) -> List[Dict]:
        """Get recent security events."""
        
        severity_order = {
            SecurityEvent.SEVERITY_INFO: 0,
            SecurityEvent.SEVERITY_LOW: 1,
            SecurityEvent.SEVERITY_MEDIUM: 2,
            SecurityEvent.SEVERITY_HIGH: 3,
            SecurityEvent.SEVERITY_CRITICAL: 4,
        }
        
        min_level = severity_order.get(min_severity, 0) if min_severity else 0
        
        filtered = [
            e.to_dict() for e in reversed(self.events)
            if severity_order.get(e.severity, 0) >= min_level
        ]
        
        return filtered[:limit]
    
    def get_statistics(self) -> Dict:
        """Get monitoring statistics."""
        return {
            "total_events": len(self.events),
            "event_type_counts": dict(self.event_counts),
            "monitoring_since": (
                self.events[0].timestamp.isoformat() 
                if self.events else None
            ),
            "last_event": (
                self.events[-1].timestamp.isoformat() 
                if self.events else None
            ),
            "file_integrity_baseline_count": len(self.file_hashes),
            "last_integrity_check": (
                self.last_integrity_check.isoformat() 
                if self.last_integrity_check else None
            )
        }


# Export
__all__ = ["SecurityMonitor", "SecurityEvent"]
