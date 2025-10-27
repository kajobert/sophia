"""
Cognitive Integrity Monitor Plugin

SECURITY: Monitors critical files for unauthorized modifications.
Runs as COGNITIVE plugin - no core modifications needed.
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict
from plugins.base_plugin import BasePlugin, PluginType

logger = logging.getLogger(__name__)


class CognitiveIntegrityMonitor(BasePlugin):
    """Monitors file integrity using SHA256 hashing."""
    
    CRITICAL_FILES = [
        "config/settings.yaml",
        "core/kernel.py",
        "core/plugin_manager.py",
        "core/context.py",
        "plugins/base_plugin.py",
    ]
    
    @property
    def name(self) -> str:
        return "cognitive_integrity_monitor"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        self.root_path = Path.cwd()
        self.file_hashes: Dict[str, str] = {}
        self.baseline_computed = False
    
    def setup(self, config: dict) -> None:
        """Initialize and compute baseline hashes."""
        self.compute_baseline()
        logger.info(f"Integrity monitor ready: monitoring {len(self.file_hashes)} files")
    
    async def execute(self, shared_context):
        """Verify file integrity periodically."""
        if not self.baseline_computed:
            return shared_context
        
        is_valid, modified_files = self.verify_integrity()
        
        if not is_valid:
            violation_info = {
                "timestamp": shared_context.current_time,
                "modified_files": modified_files,
                "severity": "CRITICAL"
            }
            shared_context.set("security.integrity_violation", violation_info)
            logger.critical(f"SECURITY: Files modified: {', '.join(modified_files)}")
        
        return shared_context
    
    def compute_baseline(self) -> None:
        """Compute SHA256 hashes of all critical files."""
        logger.info("Computing file integrity baseline...")
        
        for filepath in self.CRITICAL_FILES:
            full_path = self.root_path / filepath
            
            if not full_path.exists():
                logger.warning(f"Critical file not found: {filepath}")
                continue
            
            try:
                file_hash = self._compute_hash(full_path)
                self.file_hashes[filepath] = file_hash
            except Exception as e:
                logger.error(f"Failed to hash {filepath}: {e}")
        
        self.baseline_computed = True
    
    def verify_integrity(self) -> tuple[bool, list[str]]:
        """Verify integrity of all monitored files."""
        modified_files = []
        
        for filepath, expected_hash in self.file_hashes.items():
            full_path = self.root_path / filepath
            
            if not full_path.exists():
                modified_files.append(filepath)
                continue
            
            try:
                current_hash = self._compute_hash(full_path)
                if current_hash != expected_hash:
                    modified_files.append(filepath)
            except Exception as e:
                logger.error(f"Failed to verify {filepath}: {e}")
                modified_files.append(filepath)
        
        return len(modified_files) == 0, modified_files
    
    def _compute_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        
        return sha256.hexdigest()
