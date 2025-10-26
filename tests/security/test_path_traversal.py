"""
Security tests for Path Traversal vulnerability (Attack #3).

These tests verify that the fixes in tool_file_system.py prevent
path traversal attacks that could allow accessing/modifying files
outside the sandbox.

CVSS Score: 8.8 (HIGH)
CWE-22: Improper Limitation of a Pathname to a Restricted Directory
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from plugins.tool_file_system import FileSystemTool


class TestPathTraversalPrevention:
    """Test suite for path traversal vulnerability fixes."""
    
    @pytest.fixture
    def fs_tool(self):
        """Create a FileSystemTool with a temporary sandbox."""
        tool = FileSystemTool()
        temp_dir = tempfile.mkdtemp()
        tool.setup({"sandbox_dir": temp_dir})
        yield tool
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_basic_path_traversal_blocked(self, fs_tool):
        """Test that basic ../ path traversal is blocked."""
        with pytest.raises(PermissionError, match="Path traversal"):
            fs_tool.read_file("../../etc/passwd")
    
    def test_encoded_path_traversal_blocked(self, fs_tool):
        """Test that encoded ../ attempts are blocked."""
        with pytest.raises(PermissionError, match="Path traversal"):
            fs_tool.read_file("..%2F..%2Fetc%2Fpasswd")
    
    def test_absolute_path_blocked(self, fs_tool):
        """Test that absolute paths are blocked."""
        with pytest.raises(PermissionError, match="Absolute paths"):
            fs_tool.read_file("/etc/passwd")
    
    def test_core_escape_blocked(self, fs_tool):
        """Test that attempting to access core/ is blocked."""
        with pytest.raises(PermissionError, match="Path traversal"):
            fs_tool.read_file("../../../core/kernel.py")
    
    def test_config_escape_blocked(self, fs_tool):
        """Test that attempting to access config/ is blocked."""
        with pytest.raises(PermissionError, match="Path traversal"):
            fs_tool.read_file("../../../config/settings.yaml")
    
    def test_git_escape_blocked(self, fs_tool):
        """Test that attempting to access .git/ is blocked."""
        with pytest.raises(PermissionError, match="Path traversal"):
            fs_tool.read_file("../../../.git/config")
    
    def test_legitimate_path_allowed(self, fs_tool):
        """Test that legitimate paths within sandbox work."""
        # Create a test file
        fs_tool.write_file("test.txt", "legitimate content")
        
        # Should be able to read it back
        content = fs_tool.read_file("test.txt")
        assert content == "legitimate content"
    
    def test_subdirectory_access_allowed(self, fs_tool):
        """Test that accessing subdirectories within sandbox works."""
        fs_tool.write_file("subdir/file.txt", "nested content")
        content = fs_tool.read_file("subdir/file.txt")
        assert content == "nested content"
    
    def test_mixed_traversal_blocked(self, fs_tool):
        """Test that mixed legitimate/traversal paths are blocked."""
        with pytest.raises(PermissionError, match="Path traversal"):
            fs_tool.read_file("legitimate/../../../etc/passwd")
    
    def test_symlink_escape_prevented(self, fs_tool):
        """Test that symlinks cannot escape sandbox."""
        # Create a file in sandbox
        fs_tool.write_file("normal.txt", "safe")
        
        # Try to create a symlink to outside sandbox (would fail on write)
        # The normpath + .. check should catch this
        with pytest.raises(PermissionError):
            fs_tool.write_file("../../../evil_link", "data")
    
    def test_case_insensitive_traversal_blocked(self, fs_tool):
        """Test that case variations of .. are blocked."""
        # Even though Linux is case-sensitive, normpath handles this
        with pytest.raises(PermissionError, match="Path traversal"):
            fs_tool.read_file("../PARENT/../../etc/passwd")


class TestProtectedPathsPrevention:
    """Test suite for protected paths (defense in depth)."""
    
    @pytest.fixture
    def fs_tool(self):
        """Create a FileSystemTool with project root as sandbox."""
        tool = FileSystemTool()
        # Use actual project root for protected paths testing
        tool.setup({"sandbox_dir": "/workspaces/sophia"})
        yield tool
    
    def test_core_write_blocked(self, fs_tool):
        """Test that writing to core/ is blocked."""
        with pytest.raises(PermissionError, match="protected path"):
            fs_tool.write_file("core/kernel.py", "malicious code")
    
    def test_config_write_blocked(self, fs_tool):
        """Test that writing to config/ is blocked."""
        with pytest.raises(PermissionError, match="protected path"):
            fs_tool.write_file("config/settings.yaml", "api_key: stolen")
    
    def test_git_write_blocked(self, fs_tool):
        """Test that writing to .git/ is blocked."""
        with pytest.raises(PermissionError, match="protected path"):
            fs_tool.write_file(".git/config", "malicious git config")
    
    def test_base_plugin_write_blocked(self, fs_tool):
        """Test that writing to base_plugin.py is blocked."""
        with pytest.raises(PermissionError, match="protected path"):
            fs_tool.write_file("plugins/base_plugin.py", "backdoor")
    
    def test_env_write_blocked(self, fs_tool):
        """Test that writing to .env is blocked."""
        with pytest.raises(PermissionError, match="protected path"):
            fs_tool.write_file(".env", "API_KEY=stolen")
    
    def test_sandbox_write_allowed(self, fs_tool):
        """Test that writing to sandbox/ is allowed."""
        # Should succeed without raising
        result = fs_tool.write_file("sandbox/test.txt", "allowed content")
        assert "Successfully wrote" in result
    
    def test_docs_write_allowed(self, fs_tool):
        """Test that writing to docs/ is allowed (not protected)."""
        result = fs_tool.write_file("docs/test.md", "documentation")
        assert "Successfully wrote" in result
    
    def test_plugins_custom_write_allowed(self, fs_tool):
        """Test that writing custom plugins is allowed (not base_plugin)."""
        result = fs_tool.write_file("plugins/my_plugin.py", "custom plugin")
        assert "Successfully wrote" in result
    
    def test_case_insensitive_protected_paths(self, fs_tool):
        """Test that case variations of protected paths are blocked."""
        # CRITICAL: Prevent bypass on case-insensitive filesystems
        with pytest.raises(PermissionError, match="protected path"):
            fs_tool.write_file("CORE/kernel.py", "malicious")
        
        with pytest.raises(PermissionError, match="protected path"):
            fs_tool.write_file("Core/Kernel.py", "malicious")
        
        with pytest.raises(PermissionError, match="protected path"):
            fs_tool.write_file("CONFIG/settings.yaml", "malicious")
        
        with pytest.raises(PermissionError, match="protected path"):
            fs_tool.write_file(".ENV", "API_KEY=stolen")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
