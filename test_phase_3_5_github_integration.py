#!/usr/bin/env python3
"""
Test Phase 3.5: GitHub Integration

Verifies that cognitive_self_tuning plugin creates Pull Requests
after successful deployment.

Expected behavior:
  1. Hypothesis deployed successfully
  2. Git commit created
  3. PR created via GitHub plugin
  4. Hypothesis updated with PR details
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from pathlib import Path
import logging

# Import plugins
from plugins.cognitive_self_tuning import CognitiveSelfTuning
from core.context import SharedContext

# Setup logging
logger = logging.getLogger(__name__)


class MockPRResponse:
    """Mock GitHub PR response."""
    def __init__(self, number=42, html_url="https://github.com/ShotyCZ/sophia/pull/42", title="Test PR"):
        self.number = number
        self.html_url = html_url
        self.title = title


class TestGitHubIntegration:
    """Test suite for GitHub integration in self-tuning plugin."""
    
    @pytest.fixture
    def mock_github_plugin(self):
        """Create mock GitHub plugin."""
        plugin = MagicMock()
        plugin.create_pull_request = MagicMock(return_value=MockPRResponse())
        return plugin
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.get_hypothesis_by_id = MagicMock(return_value={
            "id": 1,
            "description": "Test hypothesis for PR creation",
            "category": "performance",
            "priority": 5,
            "fix_type": "code",
            "proposed_fix": "Optimize query",
            "status": "approved"
        })
        db.update_hypothesis_status = MagicMock()
        return db
    
    @pytest.fixture
    def test_config(self, mock_github_plugin, mock_db):
        """Create test configuration with GitHub integration enabled."""
        return {
            "all_plugins": {
                "tool_github": mock_github_plugin,
                "memory_sqlite": mock_db
            },
            "event_bus": MagicMock(),
            "autonomy": {
                "self_improvement": {
                    "self_tuning": {
                        "improvement_threshold": 0.10,
                        "sandbox_path": "sandbox/test_github",
                        "auto_deploy": True
                    }
                },
                "github_integration": {
                    "enabled": True,
                    "repository_owner": "ShotyCZ",
                    "repository_name": "sophia",
                    "target_branch": "master",
                    "create_as_draft": True
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_pr_creation_after_deployment(self, test_config, mock_github_plugin):
        """Test that PR is created after successful deployment."""
        plugin = CognitiveSelfTuning()
        plugin.setup(test_config)
        
        hypothesis = {
            "id": 1,
            "description": "Optimize database query",
            "category": "performance",
            "priority": 8,
            "fix_type": "code",
            "proposed_fix": "Use index for faster lookup",
            "tested_at": "2025-01-01T12:00:00"
        }
        
        # Mock git branch command
        with patch('subprocess.run') as mock_run:
            # Git branch returns feature branch
            mock_run.return_value = MagicMock(
                stdout="feature/auto-improvement\n",
                returncode=0
            )
            
            # Call PR creation
            await plugin._create_pull_request_for_deployment(hypothesis, "plugins/test.py")
        
        # Verify GitHub plugin was called
        assert mock_github_plugin.create_pull_request.called
        
        # Verify PR parameters
        call_args = mock_github_plugin.create_pull_request.call_args
        assert call_args[1]["owner"] == "ShotyCZ"
        assert call_args[1]["repo"] == "sophia"
        assert call_args[1]["base"] == "master"
        assert call_args[1]["head"] == "feature/auto-improvement"
        assert call_args[1]["draft"] is True
        
        # Verify PR title contains hypothesis info
        assert "performance" in call_args[1]["title"]
        
        # Verify PR body contains details
        pr_body = call_args[1]["body"]
        assert "Hypothesis ID" in pr_body
        assert "1" in pr_body
        assert "performance" in pr_body
        assert "code" in pr_body
        
        print("✅ PR created with correct parameters")
    
    @pytest.mark.asyncio
    async def test_pr_skipped_when_disabled(self, test_config, mock_github_plugin):
        """Test that PR creation is skipped when disabled in config."""
        # Disable GitHub integration
        test_config["autonomy"]["github_integration"]["enabled"] = False
        
        plugin = CognitiveSelfTuning()
        plugin.setup(test_config)
        
        hypothesis = {
            "id": 2,
            "description": "Test hypothesis",
            "category": "bug_fix",
            "priority": 5,
            "fix_type": "code"
        }
        
        # Call PR creation
        await plugin._create_pull_request_for_deployment(hypothesis, "test.py")
        
        # Verify GitHub plugin was NOT called
        assert not mock_github_plugin.create_pull_request.called
        print("✅ PR creation skipped when disabled")
    
    @pytest.mark.asyncio
    async def test_pr_skipped_when_plugin_unavailable(self, test_config, mock_db):
        """Test graceful handling when GitHub plugin not available."""
        # Remove GitHub plugin
        test_config["all_plugins"].pop("tool_github")
        
        plugin = CognitiveSelfTuning()
        plugin.setup(test_config)
        
        hypothesis = {
            "id": 3,
            "description": "Test hypothesis",
            "category": "enhancement",
            "priority": 3,
            "fix_type": "config"
        }
        
        # Should not raise exception
        await plugin._create_pull_request_for_deployment(hypothesis, "config.yaml")
        
        print("✅ Gracefully handled missing GitHub plugin")
    
    @pytest.mark.asyncio
    async def test_pr_skipped_on_target_branch(self, test_config, mock_github_plugin):
        """Test that PR is not created when already on target branch."""
        plugin = CognitiveSelfTuning()
        plugin.setup(test_config)
        
        hypothesis = {
            "id": 4,
            "description": "Test hypothesis",
            "category": "refactor",
            "priority": 4,
            "fix_type": "code"
        }
        
        # Mock git branch command - return target branch
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="master\n",  # Already on target branch
                returncode=0
            )
            
            await plugin._create_pull_request_for_deployment(hypothesis, "test.py")
        
        # Verify GitHub plugin was NOT called
        assert not mock_github_plugin.create_pull_request.called
        print("✅ PR creation skipped when on target branch")
    
    @pytest.mark.asyncio
    async def test_hypothesis_updated_with_pr_info(self, test_config, mock_github_plugin, mock_db):
        """Test that hypothesis is updated with PR details."""
        plugin = CognitiveSelfTuning()
        plugin.setup(test_config)
        
        hypothesis = {
            "id": 5,
            "description": "Add caching layer",
            "category": "performance",
            "priority": 9,
            "fix_type": "code"
        }
        
        # Mock git branch command
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="feature/caching\n",
                returncode=0
            )
            
            await plugin._create_pull_request_for_deployment(hypothesis, "core/cache.py")
        
        # Verify hypothesis was updated with PR info
        assert mock_db.update_hypothesis_status.called
        
        call_args = mock_db.update_hypothesis_status.call_args
        assert call_args[0][0] == 5  # hypothesis_id
        assert call_args[0][1] == "deployed_with_pr"  # status
        
        # Result is in kwargs as test_results
        test_results = call_args[1]["test_results"]
        assert test_results["pr_number"] == 42
        assert test_results["pr_url"] == "https://github.com/ShotyCZ/sophia/pull/42"
        
        print("✅ Hypothesis updated with PR details")
    
    @pytest.mark.asyncio
    async def test_pr_error_handling(self, test_config, mock_github_plugin):
        """Test that PR creation errors don't fail deployment."""
        # Make GitHub plugin raise exception
        mock_github_plugin.create_pull_request.side_effect = Exception("GitHub API error")
        
        plugin = CognitiveSelfTuning()
        plugin.setup(test_config)
        
        hypothesis = {
            "id": 6,
            "description": "Test hypothesis",
            "category": "bug_fix",
            "priority": 7,
            "fix_type": "code"
        }
        
        # Mock git branch
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="feature/test\n", returncode=0)
            
            # Should not raise exception (best effort)
            await plugin._create_pull_request_for_deployment(hypothesis, "test.py")
        
        print("✅ PR errors handled gracefully")
    
    @pytest.mark.asyncio
    async def test_pr_body_contains_all_details(self, test_config, mock_github_plugin):
        """Test that PR body includes all required information."""
        plugin = CognitiveSelfTuning()
        plugin.setup(test_config)
        
        hypothesis = {
            "id": 7,
            "description": "Refactor authentication module",
            "category": "security",
            "priority": 10,
            "fix_type": "code",
            "proposed_fix": "Use bcrypt for password hashing",
            "tested_at": "2025-01-15T10:30:00"
        }
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="feature/auth\n", returncode=0)
            
            await plugin._create_pull_request_for_deployment(hypothesis, "core/auth.py")
        
        # Get PR body
        pr_body = mock_github_plugin.create_pull_request.call_args[1]["body"]
        
        # Verify required sections
        assert "Hypothesis ID" in pr_body
        assert "7" in pr_body
        assert "Category" in pr_body
        assert "security" in pr_body
        assert "Priority" in pr_body
        assert "10" in pr_body
        assert "Fix Type" in pr_body
        assert "code" in pr_body
        assert "Description" in pr_body
        assert "Refactor authentication module" in pr_body
        assert "Proposed Fix" in pr_body
        assert "bcrypt" in pr_body
        assert "Testing Results" in pr_body
        assert "APPROVED" in pr_body
        assert "Deployed At" in pr_body
        assert "Branch" in pr_body
        assert "feature/auth" in pr_body
        assert "Target" in pr_body
        assert "master" in pr_body
        
        print("✅ PR body contains all required details")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
