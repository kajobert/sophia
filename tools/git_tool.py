import git
from tools.base_tool import BaseTool
from typing import Any, List

class GitTool(BaseTool):
    """
    A tool for interacting with Git repositories.
    This tool uses the GitPython library to execute git commands.
    """

    def __init__(self, repo_path: str = "."):
        """
        Initializes the GitTool.

        Args:
            repo_path (str): The path to the git repository. Defaults to the current directory.
        """
        try:
            self.repo = git.Repo(repo_path, search_parent_directories=True)
        except (git.InvalidGitRepositoryError, git.exc.NoSuchPathError):
            # Handle cases where the path is not a git repository or does not exist.
            raise ValueError(f"The path '{repo_path}' is not a valid Git repository or does not exist.")

    def execute(self, action: str, **kwargs: Any) -> str:
        """
        Executes a git action.

        Args:
            action (str): The git action to perform. Supported actions are:
                          'create_branch', 'add', 'commit', 'status'.
            **kwargs: Arguments for the specific action.
                - create_branch: requires `branch_name`
                - add: requires `files` (a list of file paths)
                - commit: requires `message`
                - status: no arguments required

        Returns:
            str: The result of the git command.
        """
        if action == "create_branch":
            branch_name = kwargs.get("branch_name")
            if not branch_name:
                return "Error: 'branch_name' is required for create_branch action."
            return self._create_branch(branch_name)
        elif action == "add":
            files = kwargs.get("files")
            if not files:
                return "Error: 'files' is required for add action."
            return self._add(files)
        elif action == "commit":
            message = kwargs.get("message")
            if not message:
                return "Error: 'message' is required for commit action."
            return self._commit(message)
        elif action == "status":
            return self._status()
        else:
            return f"Error: Unknown action '{action}'. Supported actions are: create_branch, add, commit, status."

    def _create_branch(self, branch_name: str) -> str:
        """Creates and checks out a new branch."""
        try:
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            return f"Branch '{branch_name}' created and checked out successfully."
        except Exception as e:
            return f"Error creating branch: {e}"

    def _add(self, files: List[str]) -> str:
        """Adds specified files to the staging area."""
        try:
            self.repo.index.add(files)
            return f"Files {files} added to staging successfully."
        except Exception as e:
            return f"Error adding files: {e}"

    def _commit(self, message: str) -> str:
        """Creates a commit."""
        try:
            self.repo.index.commit(message)
            return f"Commit created successfully with message: '{message}'"
        except Exception as e:
            return f"Error committing: {e}"

    def _status(self) -> str:
        """Gets the git status."""
        try:
            return self.repo.git.status()
        except Exception as e:
            return f"Error getting status: {e}"
