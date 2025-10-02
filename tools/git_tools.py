import subprocess
import os
from typing import List, Union

# --- Configuration ---
LAST_GOOD_COMMIT_FILE = ".last_known_good_commit"

def _run_git_command(command: List[str]) -> str:
    """A helper function to run a Git command and return its output."""
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Return a formatted error message that the agent can understand.
        return f"Error executing command '{' '.join(command)}':\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}"
    except FileNotFoundError:
        return "Error: 'git' command not found. Is Git installed and in the system's PATH?"

def get_git_status() -> str:
    """
    Gets the status of the git repository.
    Equivalent to 'git status --porcelain' for a concise output.
    """
    return _run_git_command(["git", "status", "--porcelain"])

def add_to_git(files: Union[str, List[str]]) -> str:
    """
    Adds one or more files to the git staging area.

    :param files: A single file path or a list of file paths.
    """
    if isinstance(files, str):
        files = [files]

    if not files:
        return "Error: No files provided to add."

    command = ["git", "add"] + files
    return _run_git_command(command)

def create_git_commit(message: str) -> str:
    """
    Creates a new commit with the provided message.
    Returns the hash of the new commit.
    """
    # First, add all tracked, modified files to ensure they are included.
    # This is a safer default for the agent's workflow.
    status = get_git_status()
    if not status:
        return "No changes to commit."

    # Use 'git add -u' to stage all tracked, modified files.
    add_result = _run_git_command(["git", "add", "-u"])
    if "Error" in add_result:
        return f"Failed to stage changes before commit: {add_result}"

    commit_result = _run_git_command(["git", "commit", "-m", message])
    if "Error" in commit_result:
        return f"Failed to create commit: {commit_result}"

    return get_last_commit_hash()

def revert_git_changes(files: Union[str, List[str]]) -> str:
    """
    Reverts changes in the specified file(s) to the last committed state (HEAD).

    :param files: A single file path or a list of file paths to revert.
    """
    if isinstance(files, str):
        files = [files]

    if not files:
        return "Error: No files provided to revert."

    command = ["git", "checkout", "HEAD", "--"] + files
    return _run_git_command(command)

def get_last_commit_hash() -> str:
    """
    Gets the hash of the most recent commit (HEAD).
    """
    return _run_git_command(["git", "rev-parse", "HEAD"])

def promote_commit_to_last_known_good(commit_hash: str) -> str:
    """
    Updates the '.last_known_good_commit' file with a new commit hash.
    This "blesses" the commit as stable.

    :param commit_hash: The commit hash to set as the new last known good version.
    """
    if not commit_hash or len(commit_hash) < 7: # Basic validation
        return f"Error: Invalid commit hash provided: '{commit_hash}'"

    try:
        # Verify it's a real commit hash
        verify_result = _run_git_command(["git", "cat-file", "-t", commit_hash])
        if verify_result != "commit":
            return f"Error: Provided hash '{commit_hash}' is not a valid commit."

        with open(LAST_GOOD_COMMIT_FILE, "w") as f:
            f.write(commit_hash)
        return f"Successfully promoted {commit_hash} to the last known good version."
    except Exception as e:
        return f"An unexpected error occurred: {e}"