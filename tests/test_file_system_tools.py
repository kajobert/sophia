import pytest
import os
import shutil
from tools import file_system

# Define a sandbox directory for these specific tests
TEST_SANDBOX_DIR = "test_sandbox"

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """Set up the test sandbox before tests run, and clean it up afterwards."""
    # Setup: Create a clean sandbox for tests
    if os.path.exists(TEST_SANDBOX_DIR):
        shutil.rmtree(TEST_SANDBOX_DIR)
    os.makedirs(TEST_SANDBOX_DIR)

    # Override the default sandbox directory in the file_system module
    original_sandbox_dir = file_system.SANDBOX_DIR
    file_system.SANDBOX_DIR = TEST_SANDBOX_DIR

    yield # This is where the tests will run

    # Teardown: Clean up the sandbox
    file_system.SANDBOX_DIR = original_sandbox_dir # Restore original
    shutil.rmtree(TEST_SANDBOX_DIR)

# --- Test for the original bug fix ---
def test_tool_call_with_kwargs():
    """
    Verifies that a tool can be called with keyword arguments without crashing.
    This directly tests the fix for the `run_in_executor` bug.
    """
    # Using create_file as an example tool
    result = file_system.create_file(filepath="test_kwargs.txt")
    assert "successfully" in result
    assert os.path.exists(os.path.join(TEST_SANDBOX_DIR, "test_kwargs.txt"))

# --- Tests for New JULES Tools ---
def test_create_and_overwrite_file_with_block():
    """Tests create_file_with_block and overwrite_file_with_block functionality."""
    filepath = "test_create.txt"
    content1 = "Hello, World!"
    content2 = "This is the new content."

    # Test creation
    result_create = file_system.create_file_with_block(filepath, content1)
    assert "successfully" in result_create
    with open(os.path.join(TEST_SANDBOX_DIR, filepath), 'r') as f:
        assert f.read() == content1

    # Test overwrite
    result_overwrite = file_system.overwrite_file_with_block(filepath, content2)
    assert "successfully" in result_overwrite
    with open(os.path.join(TEST_SANDBOX_DIR, filepath), 'r') as f:
        assert f.read() == content2

def test_delete_file():
    """Tests the delete_file function."""
    filepath = "test_delete.txt"
    file_to_delete = os.path.join(TEST_SANDBOX_DIR, filepath)

    # Create a file to delete
    with open(file_to_delete, 'w') as f:
        f.write("delete me")
    assert os.path.exists(file_to_delete)

    # Test deletion
    result = file_system.delete_file(filepath)
    assert "successfully" in result
    assert not os.path.exists(file_to_delete)

def test_rename_file():
    """Tests the rename_file function."""
    old_filepath = "test_rename_old.txt"
    new_filepath = "test_rename_new.txt"
    old_file = os.path.join(TEST_SANDBOX_DIR, old_filepath)
    new_file = os.path.join(TEST_SANDBOX_DIR, new_filepath)

    # Create a file to rename
    with open(old_file, 'w') as f:
        f.write("rename me")
    assert os.path.exists(old_file)
    assert not os.path.exists(new_file)

    # Test renaming
    result = file_system.rename_file(old_filepath, new_filepath)
    assert "successfully" in result
    assert not os.path.exists(old_file)
    assert os.path.exists(new_file)

def test_replace_with_git_merge_diff():
    """Tests the replace_with_git_merge_diff special tool."""
    filepath = "test_replace.txt"
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
    with open(os.path.join(TEST_SANDBOX_DIR, filepath), 'r') as f:
        final_content = f.read()
        assert final_content == expected_content

def test_replace_diff_with_nonexistent_search_block():
    """Tests that replace_with_git_merge_diff fails gracefully when the search block is not found."""
    filepath = "test_replace_fail.txt"
    original_content = "This is the original content."
    search_block = "This block does not exist."
    replace_block = "This should not be written."

    file_system.create_file_with_block(filepath, original_content)

    result = file_system.replace_with_git_merge_diff(filepath, search_block, replace_block)
    assert "Error: SEARCH block not found" in result

    # Ensure the file was not modified
    with open(os.path.join(TEST_SANDBOX_DIR, filepath), 'r') as f:
        assert f.read() == original_content

# --- Tests for read_file_section ---

@pytest.fixture(scope="module")
def sample_py_file_for_section_read():
    """Creates a sample Python file for testing read_file_section within the module-scoped sandbox."""
    filepath = "sample_for_section.py"
    file_content = """
# This is a comment at the top

class MyTestClass:
    \"\"\"A test class.\"\"\"
    def __init__(self):
        self.value = 1

    def my_method(self):
        return self.value

@my_decorator
def decorated_function(x, y):
    \"\"\"A decorated function.\"\"\"
    return x + y

def another_function():
    return "hello"
"""
    # We use the existing file_system tools which are aware of the TEST_SANDBOX_DIR
    file_system.create_file_with_block(filepath, file_content)
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
    filepath = "bad_syntax.py"
    file_system.create_file_with_block(filepath, "def bad_function(:\n    pass")
    result = file_system.read_file_section(filepath, "bad_function")
    assert "Error: Could not parse Python file" in result