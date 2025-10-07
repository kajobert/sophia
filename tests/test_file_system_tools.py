import pytest
import os
import shutil
import json
from tools import file_system

# Define a sandbox directory for these specific tests
TEST_SANDBOX_DIR = "test_sandbox_fs" # Renamed to avoid potential conflicts

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """Set up the test sandbox before tests run, and clean it up afterwards."""
    # Setup: Create a clean sandbox for tests
    if os.path.exists(TEST_SANDBOX_DIR):
        shutil.rmtree(TEST_SANDBOX_DIR)
    os.makedirs(TEST_SANDBOX_DIR)

    yield # This is where the tests will run

    # Teardown: Clean up the sandbox
    shutil.rmtree(TEST_SANDBOX_DIR)

# --- Test for path resolution and security ---
def test_path_traversal_prevention():
    """Tests that the _resolve_path function prevents path traversal."""
    with pytest.raises(ValueError, match="Path traversal detected"):
        file_system._resolve_path("../../../etc/passwd")
    with pytest.raises(ValueError, match="Path traversal detected"):
        file_system._resolve_path("/etc/passwd")

# --- Tests for File System Tools with Unified Pathing ---

def test_create_and_read_file():
    """Tests creating and reading a file with the new pathing."""
    filepath = os.path.join(TEST_SANDBOX_DIR, "test_create_read.txt")
    content = "Hello, unified world!"

    # Create file
    result_create = file_system.create_file_with_block(filepath, content)
    assert "successfully" in result_create
    assert os.path.exists(filepath)

    # Read file and parse JSON
    read_json = file_system.read_file(filepath)
    read_data = json.loads(read_json)

    assert read_data["content"] == content
    assert read_data["total_lines"] == 1
    assert not read_data["is_truncated"]

def test_overwrite_file():
    """Tests overwriting a file."""
    filepath = os.path.join(TEST_SANDBOX_DIR, "test_overwrite.txt")
    content1 = "Initial content."
    content2 = "Overwritten content."

    # Create initial file
    file_system.create_file_with_block(filepath, content1)

    # Overwrite
    result_overwrite = file_system.overwrite_file_with_block(filepath, content2)
    assert "successfully" in result_overwrite

    # Verify
    read_json = file_system.read_file(filepath)
    read_data = json.loads(read_json)
    assert read_data["content"] == content2

def test_delete_file():
    """Tests the delete_file function."""
    filepath = os.path.join(TEST_SANDBOX_DIR, "test_delete.txt")

    # Create a file to delete
    with open(filepath, 'w') as f:
        f.write("delete me")
    assert os.path.exists(filepath)

    # Test deletion
    result = file_system.delete_file(filepath)
    assert "successfully" in result
    assert not os.path.exists(filepath)

def test_rename_file():
    """Tests the rename_file function."""
    old_filepath = os.path.join(TEST_SANDBOX_DIR, "rename_old.txt")
    new_filepath = os.path.join(TEST_SANDBOX_DIR, "rename_new.txt")

    # Create a file to rename
    with open(old_filepath, 'w') as f:
        f.write("rename me")
    assert os.path.exists(old_filepath)
    assert not os.path.exists(new_filepath)

    # Test renaming
    result = file_system.rename_file(old_filepath, new_filepath)
    assert "successfully" in result
    assert not os.path.exists(old_filepath)
    assert os.path.exists(new_filepath)

def test_replace_with_git_merge_diff():
    """Tests the replace_with_git_merge_diff special tool."""
    filepath = os.path.join(TEST_SANDBOX_DIR, "test_replace.txt")
    original_content = "Line 1\nLine 2 to be replaced\nLine 3"
    search_block = "Line 2 to be replaced"
    replace_block = "Line 2 has been successfully replaced"
    expected_content = "Line 1\nLine 2 has been successfully replaced\nLine 3"

    # Create the file with original content
    file_system.create_file_with_block(filepath, original_content)

    # Perform the replacement
    result = file_system.replace_with_git_merge_diff(filepath, search_block, replace_block)
    assert "successfully" in result

    # Verify the content
    final_json = file_system.read_file(filepath)
    final_data = json.loads(final_json)
    assert final_data["content"] == expected_content

def test_list_files():
    """Tests listing files in a directory."""
    dir_to_list = os.path.join(TEST_SANDBOX_DIR, "list_test")
    os.makedirs(dir_to_list, exist_ok=True)
    with open(os.path.join(dir_to_list, "file1.txt"), 'w') as f:
        f.write("1")
    with open(os.path.join(dir_to_list, "file2.log"), 'w') as f:
        f.write("2")

    result = file_system.list_files(dir_to_list)
    assert "file1.txt" in result
    assert "file2.log" in result

# --- Tests for read_file_section ---

@pytest.fixture(scope="module")
def sample_py_file_for_section_read():
    """Creates a sample Python file for testing read_file_section."""
    filepath = os.path.join(TEST_SANDBOX_DIR, "sample_for_section.py")
    file_content = '''
# This is a comment at the top

class MyTestClass:
    """A test class."""
    def __init__(self):
        self.value = 1

    def my_method(self):
        return self.value

@my_decorator
def decorated_function(x, y):
    """A decorated function."""
    return x + y

def another_function():
    return "hello"
'''
    # We use the existing file_system tools which now work relative to project root
    file_system.create_file_with_block(filepath, file_content.strip())
    return filepath

def test_read_file_section_class(sample_py_file_for_section_read):
    """Tests extracting an entire class."""
    result = file_system.read_file_section(sample_py_file_for_section_read, "MyTestClass")
    assert "class MyTestClass:" in result
    assert "def my_method(self):" in result
    assert "def decorated_function" not in result

def test_read_file_section_decorated_function(sample_py_file_for_section_read):
    """Tests extracting a function with a decorator."""
    result = file_system.read_file_section(sample_py_file_for_section_read, "decorated_function")
    assert "@my_decorator" in result
    assert "def decorated_function(x, y):" in result
    assert "class MyTestClass:" not in result

def test_read_file_section_not_found(sample_py_file_for_section_read):
    """Tests the case where the identifier is not found in the file."""
    result = file_system.read_file_section(sample_py_file_for_section_read, "non_existent_function")
    assert "Error: Identifier 'non_existent_function' not found" in result

def test_read_file_section_syntax_error():
    """Tests reading from a file with a syntax error."""
    filepath = os.path.join(TEST_SANDBOX_DIR, "bad_syntax.py")
    file_system.create_file_with_block(filepath, "def bad_function(:\n    pass")
    result = file_system.read_file_section(filepath, "bad_function")
    assert "Error: Could not parse Python file" in result
