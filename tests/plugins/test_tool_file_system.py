# tests/plugins/test_tool_file_system.py
"""Tests for the FileSystemTool plugin."""

import pytest
import os
import shutil
from plugins.tool_file_system import FileSystemTool


@pytest.fixture
def fs_tool():
    """Pytest fixture to set up and tear down a test sandbox."""
    sandbox_dir = "test_sandbox"
    # Ensure the directory is clean before the test
    if os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir)
    tool = FileSystemTool()
    tool.setup({"sandbox_dir": sandbox_dir})
    yield tool
    # Teardown: clean up the sandbox directory after the test
    if os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir)


def test_fs_tool_write_and_read(fs_tool: FileSystemTool):
    """Tests writing to a file and then reading from it."""
    file_path = "test_dir/my_file.txt"
    content = "Hello, Sophia!"
    write_status = fs_tool.write_file(file_path, content)
    assert "Successfully wrote" in write_status
    read_content = fs_tool.read_file(file_path)
    assert read_content == content


def test_fs_tool_list_directory(fs_tool: FileSystemTool):
    """Tests listing the contents of a directory."""
    fs_tool.write_file("file1.txt", "a")
    fs_tool.write_file("subdir/file2.txt", "b")
    root_contents = fs_tool.list_directory(".")
    assert "file1.txt" in root_contents
    assert "subdir" in root_contents
    subdir_contents = fs_tool.list_directory("subdir")
    assert "file2.txt" in subdir_contents


def test_fs_tool_sandbox_security(fs_tool: FileSystemTool):
    """Tests that the tool prevents path traversal attacks."""
    # Attempt to write outside the sandbox
    with pytest.raises(PermissionError):
        fs_tool.write_file("../outside.txt", "malicious content")

    # Attempt to read outside the sandbox
    with pytest.raises(PermissionError):
        fs_tool.read_file("../../some_system_file")


def test_fs_tool_read_nonexistent_file(fs_tool: FileSystemTool):
    """Tests that reading a nonexistent file raises an error."""
    with pytest.raises(FileNotFoundError):
        fs_tool.read_file("nonexistent.txt")


def test_fs_tool_list_nondirectory(fs_tool: FileSystemTool):
    """Tests that listing a non-directory raises an error."""
    fs_tool.write_file("a_file.txt", "content")
    with pytest.raises(NotADirectoryError):
        fs_tool.list_directory("a_file.txt")
