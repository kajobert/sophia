"""
Tests for Cognitive Integrity Monitor Plugin (Phase 0.3)

Tests file integrity monitoring using simplified interface.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock
from plugins.cognitive_integrity_monitor import CognitiveIntegrityMonitor


class TestIntegrityMonitorBaseline:
    """Test baseline computation."""
    
    def test_baseline_computed_on_setup(self):
        """Baseline should be computed during setup."""
        monitor = CognitiveIntegrityMonitor()
        assert not monitor.baseline_computed
        
        monitor.setup({})
        
        assert monitor.baseline_computed
        assert len(monitor.file_hashes) > 0
    
    def test_critical_files_hashed(self):
        """All existing critical files should be hashed."""
        monitor = CognitiveIntegrityMonitor()
        
        monitor.setup({})
        
        # Check that existing critical files are in the baseline
        for filepath in monitor.CRITICAL_FILES:
            full_path = monitor.root_path / filepath
            if full_path.exists():
                assert filepath in monitor.file_hashes
                assert len(monitor.file_hashes[filepath]) == 64  # SHA256 hex length


class TestIntegrityVerification:
    """Test file integrity verification."""
    
    def test_unmodified_files_pass(self):
        """Unmodified files should pass integrity check."""
        monitor = CognitiveIntegrityMonitor()
        monitor.setup({})
        
        # Immediately verify - nothing should have changed
        is_valid, modified = monitor.verify_integrity()
        
        assert is_valid
        assert len(modified) == 0
    
    def test_modified_file_detected(self, tmp_path):
        """Modified files should be detected."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")
        
        monitor = CognitiveIntegrityMonitor()
        monitor.root_path = tmp_path
        monitor.CRITICAL_FILES = ["test.txt"]
        
        monitor.setup({})
        
        # Modify the file
        test_file.write_text("modified content")
        
        # Verify should detect the change
        is_valid, modified = monitor.verify_integrity()
        
        assert not is_valid
        assert "test.txt" in modified
    
    def test_deleted_file_detected(self, tmp_path):
        """Deleted files should be detected."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")
        
        monitor = CognitiveIntegrityMonitor()
        monitor.root_path = tmp_path
        monitor.CRITICAL_FILES = ["test.txt"]
        
        monitor.setup({})
        
        # Delete the file
        test_file.unlink()
        
        # Verify should detect deletion
        is_valid, modified = monitor.verify_integrity()
        
        assert not is_valid
        assert "test.txt" in modified


class TestHashComputation:
    """Test SHA256 hash computation."""
    
    def test_hash_deterministic(self, tmp_path):
        """Same file should produce same hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        monitor = CognitiveIntegrityMonitor()
        
        hash1 = monitor._compute_hash(test_file)
        hash2 = monitor._compute_hash(test_file)
        
        assert hash1 == hash2
    
    def test_different_content_different_hash(self, tmp_path):
        """Different content should produce different hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("content A")
        file2.write_text("content B")
        
        monitor = CognitiveIntegrityMonitor()
        
        hash1 = monitor._compute_hash(file1)
        hash2 = monitor._compute_hash(file2)
        
        assert hash1 != hash2
    
    def test_hash_is_sha256(self, tmp_path):
        """Hash should be valid SHA256 hex digest."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        monitor = CognitiveIntegrityMonitor()
        file_hash = monitor._compute_hash(test_file)
        
        # SHA256 hex digest is 64 characters
        assert len(file_hash) == 64
        # Should be valid hex
        assert all(c in '0123456789abcdef' for c in file_hash)


class TestPluginLifecycle:
    """Test plugin lifecycle integration."""
    
    def test_plugin_type_is_cognitive(self):
        """Plugin should be COGNITIVE type."""
        monitor = CognitiveIntegrityMonitor()
        from plugins.base_plugin import PluginType
        
        assert monitor.plugin_type == PluginType.COGNITIVE
    
    def test_plugin_name_correct(self):
        """Plugin name should be correct."""
        monitor = CognitiveIntegrityMonitor()
        
        assert monitor.name == "cognitive_integrity_monitor"
    
    def test_plugin_version(self):
        """Plugin should have version."""
        monitor = CognitiveIntegrityMonitor()
        
        assert monitor.version == "1.0.0"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_file_hashed(self, tmp_path):
        """Empty files should be hashed correctly."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        monitor = CognitiveIntegrityMonitor()
        
        file_hash = monitor._compute_hash(empty_file)
        
        # Empty file has known SHA256 hash
        import hashlib
        expected = hashlib.sha256(b"").hexdigest()
        assert file_hash == expected
    
    def test_large_file_handled(self, tmp_path):
        """Large files should be handled with chunked reading."""
        large_file = tmp_path / "large.txt"
        
        # Create a file larger than chunk size (8192 bytes)
        content = "A" * 10000
        large_file.write_text(content)
        
        monitor = CognitiveIntegrityMonitor()
        
        file_hash = monitor._compute_hash(large_file)
        
        import hashlib
        expected = hashlib.sha256(content.encode()).hexdigest()
        assert file_hash == expected
