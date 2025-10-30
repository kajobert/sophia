import pytest
import logging
from plugins.tool_git import GitTool
from unittest.mock import patch, MagicMock


@pytest.fixture
def git_tool():
    """Fixture to provide a GitTool instance with a mocked Repo object."""
    with patch("plugins.tool_git.Repo") as mock_repo_class:
        mock_repo_instance = MagicMock()
        mock_repo_class.return_value = mock_repo_instance
        tool = GitTool()
        tool.setup({})
        return tool


def test_git_tool_get_status(git_tool):
    """Tests the get_status method."""
    git_tool.repo.git.status.return_value = "On branch master"
    status = git_tool.get_status()
    assert "On branch master" in status
    git_tool.repo.git.status.assert_called_once()


def test_git_tool_get_diff(git_tool):
    """Tests the get_diff method."""
    git_tool.repo.git.diff.return_value = "diff --git a/file.txt b/file.txt"
    diff = git_tool.get_diff()
    assert "diff --git" in diff
    git_tool.repo.git.diff.assert_called_once()


def test_git_tool_get_current_branch(git_tool):
    """Tests the get_current_branch method."""
    git_tool.repo.active_branch.name = "feature/new-plugin"
    branch = git_tool.get_current_branch()
    assert branch == "feature/new-plugin"


import logging

def test_git_tool_initialization_failure():
    """Tests that the tool handles a failure during repository initialization."""
    with patch("plugins.tool_git.Repo", side_effect=Exception("Test error")), patch(
        "plugins.tool_git.logger"
    ) as mock_logger:
        mock_logger.level = logging.INFO
        tool = GitTool()
        tool.setup({})
        assert tool.repo is None
        status = tool.get_status()
        assert "Error: Git repository not initialized" in status
        mock_logger.error.assert_called_once()
