"""
Test suite for Jules CLI plugin

Tests the integration between Sophie and Jules CLI tool.

Author: GitHub Copilot
Date: 2025-11-03
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from plugins.tool_jules_cli import JulesCLIPlugin, CreateSessionRequest, PullResultsRequest


class TestJulesCLIPlugin:
    """Test cases for Jules CLI plugin"""
    
    @pytest.fixture
    def plugin(self):
        """Create plugin instance with mocked bash tool"""
        plugin = JulesCLIPlugin()
        
        # Mock bash tool
        bash_tool = Mock()
        bash_tool.execute = Mock()
        
        # Setup plugin with mocked bash
        config = {
            "plugins": {
                "tool_bash": bash_tool
            }
        }
        plugin.setup(config)
        
        return plugin
    
    @pytest.fixture
    def context(self):
        """Create mock context"""
        context = Mock()
        context.logger = Mock()
        context.logger.info = Mock()
        context.logger.error = Mock()
        context.logger.warning = Mock()
        return context
    
    # ============================================
    # TEST: create_session
    # ============================================
    
    def test_create_session_single(self, plugin, context):
        """Test creating single Jules session"""
        # Mock bash output
        plugin.bash_tool.execute.return_value = {
            "output": "Session ID: 123456\nStatus: PLANNING",
            "exit_code": 0
        }
        
        # Create session
        result = plugin.create_session(
            context,
            repo="ShotyCZ/sophia",
            task="Fix bug in auth module"
        )
        
        # Verify result
        assert result["success"] is True
        assert len(result["session_ids"]) == 1
        assert result["session_ids"][0] == "123456"
        
        # Verify bash was called correctly
        plugin.bash_tool.execute.assert_called_once()
        call_args = plugin.bash_tool.execute.call_args
        command = call_args[1]["command"]
        assert "jules remote new" in command
        assert "--repo ShotyCZ/sophia" in command
        assert "--parallel 1" in command
    
    def test_create_session_parallel(self, plugin, context):
        """Test creating parallel Jules sessions"""
        # Mock bash output with multiple session IDs
        plugin.bash_tool.execute.return_value = {
            "output": "Created sessions: 123456, 123457, 123458",
            "exit_code": 0
        }
        
        # Create parallel sessions
        result = plugin.create_session(
            context,
            repo="ShotyCZ/sophia",
            task="Complex refactoring task",
            parallel=3
        )
        
        # Verify result
        assert result["success"] is True
        assert len(result["session_ids"]) == 3
        assert "123456" in result["session_ids"]
        assert "123457" in result["session_ids"]
        assert "123458" in result["session_ids"]
        
        # Verify command
        call_args = plugin.bash_tool.execute.call_args
        command = call_args[1]["command"]
        assert "--parallel 3" in command
    
    def test_create_session_validation_error(self, plugin, context):
        """Test validation error for invalid parallel value"""
        with pytest.raises(Exception):  # Pydantic validation error
            plugin.create_session(
                context,
                repo="ShotyCZ/sophia",
                task="Test task",
                parallel=10  # Invalid: max is 5
            )
    
    def test_create_session_bash_failure(self, plugin, context):
        """Test handling bash execution failure"""
        # Mock bash failure
        plugin.bash_tool.execute.return_value = {
            "output": "Error: Authentication required",
            "exit_code": 1
        }
        
        # Create session
        result = plugin.create_session(
            context,
            repo="ShotyCZ/sophia",
            task="Test task"
        )
        
        # Verify error handling
        assert result["success"] is False
        assert "error" in result
        assert len(result["session_ids"]) == 0
    
    # ============================================
    # TEST: pull_results
    # ============================================
    
    def test_pull_results_view_only(self, plugin, context):
        """Test pulling results without applying"""
        # Mock bash output (diff)
        diff_output = """
diff --git a/auth.py b/auth.py
index abc123..def456 100644
--- a/auth.py
+++ b/auth.py
@@ -10,5 +10,5 @@ def authenticate():
-    return False
+    return True
"""
        plugin.bash_tool.execute.return_value = {
            "output": diff_output,
            "exit_code": 0
        }
        
        # Pull results
        result = plugin.pull_results(
            context,
            session_id="123456",
            apply=False
        )
        
        # Verify result
        assert result["success"] is True
        assert result["applied"] is False
        assert "diff" in result
        assert diff_output in result["diff"]
        
        # Verify command
        call_args = plugin.bash_tool.execute.call_args
        command = call_args[1]["command"]
        assert "jules remote pull" in command
        assert "--session 123456" in command
        assert "--apply" not in command
    
    def test_pull_results_with_apply(self, plugin, context):
        """Test pulling and applying results"""
        # Mock bash output
        plugin.bash_tool.execute.return_value = {
            "output": "Changes applied successfully",
            "exit_code": 0
        }
        
        # Pull and apply results
        result = plugin.pull_results(
            context,
            session_id="123456",
            apply=True
        )
        
        # Verify result
        assert result["success"] is True
        assert result["applied"] is True
        assert "applied" in result["message"].lower()
        
        # Verify command
        call_args = plugin.bash_tool.execute.call_args
        command = call_args[1]["command"]
        assert "--apply" in command
    
    def test_pull_results_session_id_cleanup(self, plugin, context):
        """Test that 'sessions/' prefix is removed from session ID"""
        plugin.bash_tool.execute.return_value = {
            "output": "diff output",
            "exit_code": 0
        }
        
        # Pull with full session ID format
        result = plugin.pull_results(
            context,
            session_id="sessions/123456",
            apply=False
        )
        
        # Verify command uses clean ID
        call_args = plugin.bash_tool.execute.call_args
        command = call_args[1]["command"]
        assert "--session 123456" in command
        assert "sessions/" not in command
    
    # ============================================
    # TEST: list_sessions
    # ============================================
    
    def test_list_sessions(self, plugin, context):
        """Test listing sessions"""
        # Mock bash output
        list_output = """
ID       Status      Repo              Task
123456   COMPLETED   ShotyCZ/sophia    Fix auth bug
123457   IN_PROGRESS torvalds/linux    Add tests
"""
        plugin.bash_tool.execute.return_value = {
            "output": list_output,
            "exit_code": 0
        }
        
        # List sessions
        result = plugin.list_sessions(context)
        
        # Verify result
        assert result["success"] is True
        assert len(result["sessions"]) == 2
        
        # Check first session
        session1 = result["sessions"][0]
        assert session1["session_id"] == "123456"
        assert session1["status"] == "COMPLETED"
        assert session1["repo"] == "ShotyCZ/sophia"
        
        # Check second session
        session2 = result["sessions"][1]
        assert session2["session_id"] == "123457"
        assert session2["status"] == "IN_PROGRESS"
    
    def test_list_sessions_empty(self, plugin, context):
        """Test listing when no sessions exist"""
        plugin.bash_tool.execute.return_value = {
            "output": "No sessions found",
            "exit_code": 0
        }
        
        result = plugin.list_sessions(context)
        
        assert result["success"] is True
        assert len(result["sessions"]) == 0
    
    # ============================================
    # TEST: _parse_session_ids
    # ============================================
    
    def test_parse_session_ids_single(self, plugin):
        """Test parsing single session ID"""
        output = "Session ID: 123456"
        ids = plugin._parse_session_ids(output)
        assert ids == ["123456"]
    
    def test_parse_session_ids_multiple(self, plugin):
        """Test parsing multiple session IDs"""
        output = "Created sessions: 123456, 123457, 123458"
        ids = plugin._parse_session_ids(output)
        assert len(ids) == 3
        assert "123456" in ids
    
    def test_parse_session_ids_full_format(self, plugin):
        """Test parsing full 'sessions/ID' format"""
        output = "Session created: sessions/123456"
        ids = plugin._parse_session_ids(output)
        assert "123456" in ids
    
    def test_parse_session_ids_no_duplicates(self, plugin):
        """Test that duplicates are removed"""
        output = "Session 123456, ID: 123456, sessions/123456"
        ids = plugin._parse_session_ids(output)
        assert len(ids) == 1
        assert ids[0] == "123456"
    
    # ============================================
    # TEST: Tool Definitions
    # ============================================
    
    def test_get_tool_definitions(self, plugin):
        """Test that tool definitions are properly formatted"""
        definitions = plugin.get_tool_definitions()
        
        # Should have 4 tools
        assert len(definitions) == 4
        
        # Check structure
        for tool_def in definitions:
            assert "type" in tool_def
            assert tool_def["type"] == "function"
            assert "function" in tool_def
            assert "name" in tool_def["function"]
            assert "description" in tool_def["function"]
            assert "parameters" in tool_def["function"]
        
        # Check specific tools exist
        tool_names = [t["function"]["name"] for t in definitions]
        assert "tool_jules_cli.create_session" in tool_names
        assert "tool_jules_cli.pull_results" in tool_names
        assert "tool_jules_cli.list_sessions" in tool_names
        assert "tool_jules_cli.list_repos" in tool_names


# ============================================
# INTEGRATION TESTS (require actual CLI)
# ============================================

@pytest.mark.integration
@pytest.mark.skip(reason="Requires jules login and actual CLI setup")
class TestJulesCLIIntegration:
    """Integration tests - require actual Jules CLI"""
    
    def test_real_session_creation(self):
        """Test creating real Jules session (requires auth)"""
        # This would test actual CLI interaction
        # Skip by default, run manually when needed
        pass
    
    def test_real_pull_results(self):
        """Test pulling real session results (requires completed session)"""
        # This would test actual pull/apply behavior
        # Skip by default, run manually when needed
        pass
