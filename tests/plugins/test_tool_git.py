import pytest
import logging
from unittest.mock import patch, MagicMock
from plugins.tool_git import GitTool
from core.context import SharedContext


@pytest.fixture
def mock_context():
    context = SharedContext(
        session_id="test_session", current_state="TESTING", logger=MagicMock(spec=logging.Logger)
    )
    return context


@pytest.fixture
def git_tool():
    """Fixture to provide a GitTool instance with a mocked Repo object."""
    with patch("plugins.tool_git.Repo") as mock_repo_class:
        mock_repo_instance = MagicMock()
        mock_repo_class.return_value = mock_repo_instance
        tool = GitTool()
        tool.setup({})
        return tool


def test_git_tool_get_status(git_tool, mock_context):
    """Tests the get_status method."""
    git_tool.repo.git.status.return_value = "On branch master"
    status = git_tool.get_status(mock_context)
    assert "On branch master" in status
    git_tool.repo.git.status.assert_called_once()


def test_git_tool_get_diff(git_tool, mock_context):
    """Tests the get_diff method."""
    git_tool.repo.git.diff.return_value = "diff --git a/file.txt b/file.txt"
    diff = git_tool.get_diff(mock_context)
    assert "diff --git" in diff
    git_tool.repo.git.diff.assert_called_once()


def test_git_tool_get_current_branch(git_tool, mock_context):
    """Tests the get_current_branch method."""
    git_tool.repo.active_branch.name = "feature/new-plugin"
    branch = git_tool.get_current_branch(mock_context)
    assert branch == "feature/new-plugin"


def test_git_tool_initialization_failure(mock_context):
    """Tests that the tool handles a failure during repository initialization."""
    with patch("plugins.tool_git.Repo", side_effect=Exception("Test error")):
        tool = GitTool()
        tool.setup({})
        assert tool.repo is None
        status = tool.get_status(mock_context)
        assert "Error: Git repository not initialized" in status
