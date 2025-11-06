"""
Test Suite for Phase 3.7: Autonomous Self-Upgrade System

Tests the complete autonomous upgrade workflow:
1. Deploy code change (from Phase 3.5)
2. Trigger restart with upgrade validation
3. Validate upgrade after restart
4. Rollback if validation fails
5. Collect upgrade logs for feedback

Author: Cognitive Self-Tuning Plugin (self-improved)
Date: 2025-01-06
Status: PHASE 3.7 - Autonomous Self-Upgrade
"""

import pytest
import tempfile
import shutil
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from datetime import datetime


@pytest.fixture
def mock_self_tuning():
    """Create mock cognitive_self_tuning plugin with all dependencies."""
    plugin = Mock()
    plugin.logger = Mock()
    plugin.db = Mock()
    plugin._config = {
        "all_plugins": {}
    }
    
    # Mock database methods
    plugin.db.update_hypothesis_status = Mock()
    plugin.db.get_hypothesis = Mock()
    
    return plugin


@pytest.fixture
def sample_upgrade_state():
    """Sample upgrade state for testing."""
    return {
        "hypothesis_id": "test-hyp-123",
        "target_file": "plugins/test_plugin.py",
        "backup_file": ".backup/test_plugin.py.backup",
        "deployed_at": "2025-01-06T10:00:00",
        "status": "pending_validation",
        "validation_attempts": 0,
        "max_attempts": 3
    }


@pytest.fixture
def sample_hypothesis():
    """Sample hypothesis for testing."""
    return {
        "id": "test-hyp-123",
        "category": "bug_fix",
        "description": "Fix import error in test_plugin",
        "proposed_solution": "Add missing import statement",
        "target_files": ["plugins/test_plugin.py"],
        "status": "approved",
        "approval_timestamp": "2025-01-06T09:00:00"
    }


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace with files."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    # Create .data directory
    data_dir = workspace / ".data"
    data_dir.mkdir()
    
    # Create plugins directory
    plugins_dir = workspace / "plugins"
    plugins_dir.mkdir()
    
    # Create sample plugin file
    plugin_file = plugins_dir / "test_plugin.py"
    plugin_file.write_text("""
# Test plugin
def test_function():
    return "original version"
""")
    
    # Create backup
    backup_file = plugin_file.with_suffix(".backup")
    shutil.copy2(plugin_file, backup_file)
    
    return workspace


class TestUpgradeTrigger:
    """Test triggering autonomous upgrade validation workflow."""
    
    @pytest.mark.asyncio
    async def test_trigger_creates_upgrade_state_file(self, mock_self_tuning, sample_hypothesis, temp_workspace):
        """Test that trigger creates upgrade_state.json."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        plugin.db = mock_self_tuning.db
        plugin._config = mock_self_tuning._config
        
        target_file = "plugins/test_plugin.py"
        backup_file = Path(temp_workspace) / "plugins" / "test_plugin.py.backup"
        
        # Change to temp workspace
        import os
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)
        
        try:
            # Execute
            await plugin._trigger_autonomous_upgrade_validation(
                sample_hypothesis,
                target_file,
                backup_file
            )
            
            # Verify upgrade_state.json created
            upgrade_state_file = temp_workspace / ".data" / "upgrade_state.json"
            assert upgrade_state_file.exists()
            
            # Verify content
            with open(upgrade_state_file, 'r') as f:
                upgrade_state = json.load(f)
            
            assert upgrade_state['hypothesis_id'] == sample_hypothesis['id']
            assert upgrade_state['target_file'] == target_file
            assert upgrade_state['status'] == "pending_validation"
            assert upgrade_state['validation_attempts'] == 0
            
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_trigger_creates_restart_request(self, mock_self_tuning, sample_hypothesis, temp_workspace):
        """Test that trigger creates restart_request.json for Guardian."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        plugin.db = mock_self_tuning.db
        plugin._config = mock_self_tuning._config
        
        target_file = "plugins/test_plugin.py"
        backup_file = Path(temp_workspace) / "plugins" / "test_plugin.py.backup"
        
        # Change to temp workspace
        import os
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)
        
        try:
            # Execute
            await plugin._trigger_autonomous_upgrade_validation(
                sample_hypothesis,
                target_file,
                backup_file
            )
            
            # Verify restart_request.json created
            restart_request_file = temp_workspace / ".data" / "restart_request.json"
            assert restart_request_file.exists()
            
            # Verify content
            with open(restart_request_file, 'r') as f:
                restart_request = json.load(f)
            
            assert restart_request['reason'] == "autonomous_upgrade"
            assert restart_request['hypothesis_id'] == sample_hypothesis['id']
            
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_trigger_updates_hypothesis_status(self, mock_self_tuning, sample_hypothesis, temp_workspace):
        """Test that trigger updates hypothesis status to 'deployed_awaiting_validation'."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        plugin.db = mock_self_tuning.db
        plugin._config = mock_self_tuning._config
        
        target_file = "plugins/test_plugin.py"
        backup_file = Path(temp_workspace) / "plugins" / "test_plugin.py.backup"
        
        # Change to temp workspace
        import os
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)
        
        try:
            # Execute
            await plugin._trigger_autonomous_upgrade_validation(
                sample_hypothesis,
                target_file,
                backup_file
            )
            
            # Verify hypothesis status updated
            mock_self_tuning.db.update_hypothesis_status.assert_called_once()
            call_args = mock_self_tuning.db.update_hypothesis_status.call_args
            
            assert call_args[0][0] == sample_hypothesis['id']
            assert call_args[0][1] == "deployed_awaiting_validation"
            
        finally:
            os.chdir(original_cwd)


class TestUpgradeValidation:
    """Test upgrade validation after restart."""
    
    @pytest.mark.asyncio
    async def test_validate_successful_upgrade(self, mock_self_tuning, sample_upgrade_state):
        """Test successful upgrade validation."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        plugin.db = mock_self_tuning.db
        plugin._config = mock_self_tuning._config
        
        # Mock validation methods to return success
        plugin._check_plugin_initialization = AsyncMock(return_value=True)
        plugin._run_validation_tests = AsyncMock(return_value=True)
        plugin._check_for_regressions = AsyncMock(return_value=True)
        
        # Execute
        result = await plugin._validate_upgrade(sample_upgrade_state)
        
        # Verify
        assert result is True
        mock_self_tuning.db.update_hypothesis_status.assert_called_once()
        call_args = mock_self_tuning.db.update_hypothesis_status.call_args
        assert call_args[0][1] == "deployed_validated"
    
    @pytest.mark.asyncio
    async def test_validate_failed_plugin_init(self, mock_self_tuning, sample_upgrade_state):
        """Test validation fails if plugin initialization fails."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        plugin.db = mock_self_tuning.db
        plugin._config = mock_self_tuning._config
        
        # Mock plugin init to fail
        plugin._check_plugin_initialization = AsyncMock(return_value=False)
        
        # Execute
        result = await plugin._validate_upgrade(sample_upgrade_state)
        
        # Verify
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_failed_tests(self, mock_self_tuning, sample_upgrade_state):
        """Test validation fails if tests fail."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        plugin.db = mock_self_tuning.db
        plugin._config = mock_self_tuning._config
        
        # Mock successful plugin init but failed tests
        plugin._check_plugin_initialization = AsyncMock(return_value=True)
        plugin._run_validation_tests = AsyncMock(return_value=False)
        
        # Execute
        result = await plugin._validate_upgrade(sample_upgrade_state)
        
        # Verify
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_regression_detected(self, mock_self_tuning, sample_upgrade_state):
        """Test validation fails if regression detected."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        plugin.db = mock_self_tuning.db
        plugin._config = mock_self_tuning._config
        
        # Mock successful init and tests but regression detected
        plugin._check_plugin_initialization = AsyncMock(return_value=True)
        plugin._run_validation_tests = AsyncMock(return_value=True)
        plugin._check_for_regressions = AsyncMock(return_value=False)
        
        # Execute
        result = await plugin._validate_upgrade(sample_upgrade_state)
        
        # Verify
        assert result is False


class TestRollback:
    """Test automatic rollback on validation failure."""
    
    @pytest.mark.asyncio
    async def test_rollback_restores_backup(self, mock_self_tuning, sample_upgrade_state, temp_workspace):
        """Test that rollback restores backup file."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        plugin.db = mock_self_tuning.db
        plugin._config = mock_self_tuning._config
        
        # Create modified file
        import os
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)
        
        try:
            plugin_file = temp_workspace / "plugins" / "test_plugin.py"
            backup_file = plugin_file.with_suffix(".backup")
            
            # Modify plugin file
            plugin_file.write_text("# MODIFIED VERSION")
            
            # Update upgrade state with temp paths
            sample_upgrade_state['backup_file'] = str(backup_file)
            sample_upgrade_state['target_file'] = "plugins/test_plugin.py"
            
            # Mock subprocess for git commands
            with patch('subprocess.run') as mock_subprocess:
                # Execute rollback
                result = await plugin._rollback_deployment(sample_upgrade_state)
            
            # Verify backup restored
            assert result is True
            restored_content = plugin_file.read_text()
            assert "original version" in restored_content
            assert "MODIFIED VERSION" not in restored_content
            
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_rollback_creates_revert_commit(self, mock_self_tuning, sample_upgrade_state, temp_workspace):
        """Test that rollback creates git revert commit."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        plugin.db = mock_self_tuning.db
        plugin._config = mock_self_tuning._config
        
        # Change to temp workspace
        import os
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)
        
        try:
            plugin_file = temp_workspace / "plugins" / "test_plugin.py"
            backup_file = plugin_file.with_suffix(".backup")
            
            sample_upgrade_state['backup_file'] = str(backup_file)
            sample_upgrade_state['target_file'] = "plugins/test_plugin.py"
            
            # Mock subprocess
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = Mock(returncode=0)
                
                # Execute
                result = await plugin._rollback_deployment(sample_upgrade_state)
            
            # Verify git commands called
            assert result is True
            assert mock_subprocess.call_count == 2  # git add + git commit
            
            # Check commit message (it's in the -m argument)
            commit_call = mock_subprocess.call_args_list[1]
            commit_args = commit_call[0][0]
            # Find the -m flag and get the message after it
            m_index = commit_args.index("-m")
            commit_message = commit_args[m_index + 1]
            assert "[AUTO-ROLLBACK]" in commit_message
            assert sample_upgrade_state['hypothesis_id'] in commit_message
            
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_rollback_updates_hypothesis(self, mock_self_tuning, sample_upgrade_state, temp_workspace):
        """Test that rollback updates hypothesis status."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        plugin.db = mock_self_tuning.db
        plugin._config = mock_self_tuning._config
        
        plugin._collect_upgrade_logs = AsyncMock(return_value={"logs": "test"})
        
        # Change to temp workspace
        import os
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)
        
        try:
            plugin_file = temp_workspace / "plugins" / "test_plugin.py"
            backup_file = plugin_file.with_suffix(".backup")
            
            sample_upgrade_state['backup_file'] = str(backup_file)
            sample_upgrade_state['target_file'] = "plugins/test_plugin.py"
            
            # Mock subprocess
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = Mock(returncode=0)
                
                # Execute
                await plugin._rollback_deployment(sample_upgrade_state)
            
            # Verify hypothesis updated
            mock_self_tuning.db.update_hypothesis_status.assert_called_once()
            call_args = mock_self_tuning.db.update_hypothesis_status.call_args
            
            assert call_args[0][0] == sample_upgrade_state['hypothesis_id']
            assert call_args[0][1] == "deployed_rollback"
            assert "rollback_reason" in call_args[1]["test_results"]
            
        finally:
            os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_rollback_requests_restart(self, mock_self_tuning, sample_upgrade_state, temp_workspace):
        """Test that rollback requests restart with original code."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        plugin.db = mock_self_tuning.db
        plugin._config = mock_self_tuning._config
        
        plugin._collect_upgrade_logs = AsyncMock(return_value={})
        
        # Change to temp workspace
        import os
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)
        
        try:
            plugin_file = temp_workspace / "plugins" / "test_plugin.py"
            backup_file = plugin_file.with_suffix(".backup")
            
            sample_upgrade_state['backup_file'] = str(backup_file)
            sample_upgrade_state['target_file'] = "plugins/test_plugin.py"
            
            # Mock subprocess
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = Mock(returncode=0)
                
                # Execute
                await plugin._rollback_deployment(sample_upgrade_state)
            
            # Verify restart request created
            restart_request_file = temp_workspace / ".data" / "restart_request.json"
            assert restart_request_file.exists()
            
            with open(restart_request_file, 'r') as f:
                restart_request = json.load(f)
            
            assert restart_request['reason'] == "rollback_complete"
            
        finally:
            os.chdir(original_cwd)


class TestLogCollection:
    """Test upgrade log collection."""
    
    @pytest.mark.asyncio
    async def test_collect_upgrade_logs(self, mock_self_tuning, sample_upgrade_state, temp_workspace):
        """Test that log collection gathers relevant logs."""
        from plugins.cognitive_self_tuning import CognitiveSelfTuning
        
        # Setup
        plugin = CognitiveSelfTuning()
        plugin.logger = mock_self_tuning.logger
        
        # Change to temp workspace
        import os
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)
        
        try:
            # Create log directory with sample logs
            log_dir = temp_workspace / "logs"
            log_dir.mkdir()
            
            log_file1 = log_dir / "sophia_1.log"
            log_file1.write_text("Log entry 1")
            
            log_file2 = log_dir / "sophia_2.log"
            log_file2.write_text("Log entry 2")
            
            # Execute
            logs = await plugin._collect_upgrade_logs(sample_upgrade_state)
            
            # Verify
            assert "upgrade_state" in logs
            assert "log_files" in logs
            assert len(logs["log_files"]) > 0
            
        finally:
            os.chdir(original_cwd)


class TestStartupCheck:
    """Test startup check for pending upgrades."""
    
    @pytest.mark.asyncio
    async def test_startup_check_validates_pending_upgrade(self, temp_workspace, sample_upgrade_state):
        """Test that startup check validates pending upgrade."""
        # This would test the _check_pending_upgrade() function in run.py
        # Requires integration testing with full kernel
        pass  # TODO: Integration test
    
    @pytest.mark.asyncio
    async def test_startup_check_cleans_up_on_success(self, temp_workspace, sample_upgrade_state):
        """Test that successful validation cleans up state files."""
        pass  # TODO: Integration test
    
    @pytest.mark.asyncio
    async def test_startup_check_rolls_back_on_failure(self, temp_workspace, sample_upgrade_state):
        """Test that failed validation triggers rollback."""
        pass  # TODO: Integration test


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
