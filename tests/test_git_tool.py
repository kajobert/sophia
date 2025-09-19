import pytest
from git import Repo
import os
import shutil
from tools.git_tool import GitTool

# Fixture to create a temporary git repository for testing
@pytest.fixture(scope="module")
def temp_git_repo(tmpdir_factory):
    repo_path = tmpdir_factory.mktemp("git_repo")
    repo = Repo.init(str(repo_path))

    # Create an initial commit so we have a master branch
    initial_file_path = repo_path.join("initial_file.txt")
    with open(initial_file_path, "w") as f:
        f.write("initial content")
    repo.index.add([str(initial_file_path)])
    repo.index.commit("Initial commit")

    yield str(repo_path)

    # Cleanup the temporary directory
    shutil.rmtree(str(repo_path))

def test_git_tool_init(temp_git_repo):
    """Test that GitTool initializes correctly with a valid repo."""
    tool = GitTool(repo_path=temp_git_repo)
    assert tool.repo is not None
    assert isinstance(tool.repo, Repo)

def test_git_tool_init_invalid_repo():
    """Test that GitTool raises an error for an invalid repo path."""
    with pytest.raises(ValueError):
        GitTool(repo_path="/tmp/non_existent_repo_for_sure")

def test_create_branch(temp_git_repo):
    """Test creating a new branch."""
    tool = GitTool(repo_path=temp_git_repo)
    branch_name = "test-branch"
    result = tool.execute(action="create_branch", branch_name=branch_name)
    assert "successfully" in result
    assert branch_name in tool.repo.branches

def test_add_files(temp_git_repo):
    """Test adding files to staging."""
    tool = GitTool(repo_path=temp_git_repo)

    # Create a new file to add
    file_to_add = os.path.join(temp_git_repo, "new_test_file.txt")
    with open(file_to_add, "w") as f:
        f.write("some test content")

    result = tool.execute(action="add", files=[file_to_add])
    assert "successfully" in result

    # Check the status to see if the file is staged
    status_result = tool.execute(action="status")
    assert "new file:   new_test_file.txt" in status_result

def test_commit(temp_git_repo):
    """Test committing changes."""
    tool = GitTool(repo_path=temp_git_repo)

    # Add a file and then commit it
    file_to_commit = os.path.join(temp_git_repo, "file_to_commit.txt")
    with open(file_to_commit, "w") as f:
        f.write("content to be committed")

    tool.execute(action="add", files=[file_to_commit])

    commit_message = "Test commit message"
    result = tool.execute(action="commit", message=commit_message)
    assert "successfully" in result

    # Check the log to see if the commit is there
    log = tool.repo.git.log()
    assert commit_message in log

def test_status(temp_git_repo):
    """Test getting the git status."""
    tool = GitTool(repo_path=temp_git_repo)

    # Create a new file to make the repo dirty
    dirty_file = os.path.join(temp_git_repo, "dirty_file.txt")
    with open(dirty_file, "w") as f:
        f.write("this is a new file")

    status_result = tool.execute(action="status")
    assert "untracked files" in status_result.lower()
    assert "dirty_file.txt" in status_result

def test_unknown_action(temp_git_repo):
    """Test that an unknown action returns an error."""
    tool = GitTool(repo_path=temp_git_repo)
    result = tool.execute(action="non_existent_action")
    assert "Error: Unknown action" in result
