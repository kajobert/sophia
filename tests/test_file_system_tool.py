import unittest
import os
import shutil
from tools.file_system import WriteFileTool, ReadFileTool, ListDirectoryTool, SANDBOX_DIR

class TestFileSystemTools(unittest.TestCase):

    def setUp(self):
        """Set up the test environment before each test."""
        self.write_tool = WriteFileTool()
        self.read_tool = ReadFileTool()
        self.list_tool = ListDirectoryTool()

        # Ensure the sandbox directory exists and is clean for the test
        if not os.path.exists(SANDBOX_DIR):
            os.makedirs(SANDBOX_DIR)

        # Define a test directory within the sandbox to isolate test artifacts
        self.test_dir = os.path.join(SANDBOX_DIR, "test_fs_data")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

    def tearDown(self):
        """Clean up the test environment after each test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_write_file_success(self):
        """Test successfully writing a file to the sandbox."""
        file_path = "test_fs_data/test_write.txt"
        content = "Hello, Sandbox!"
        result = self.write_tool._run(file_path=file_path, content=content)
        self.assertIn("successfully", result)

        # Verify the file was actually written
        full_path = os.path.join(SANDBOX_DIR, file_path)
        self.assertTrue(os.path.exists(full_path))
        with open(full_path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), content)

    def test_write_file_outside_sandbox(self):
        """Test that writing outside the sandbox is forbidden."""
        # Attempt to write to the parent directory using traversal
        file_path = "../outside_test.txt"
        result = self.write_tool._run(file_path=file_path, content="breach")
        self.assertIn("Error: Path", result)
        self.assertIn("outside the allowed /sandbox directory", result)

        # Verify the file was not created
        self.assertFalse(os.path.exists(os.path.join(SANDBOX_DIR, file_path)))

    def test_read_file_success(self):
        """Test successfully reading a file from the sandbox."""
        file_path = "test_fs_data/test_read.txt"
        content = "Readable content."
        # Create the file first before reading
        self.write_tool._run(file_path=file_path, content=content)

        result = self.read_tool._run(file_path=file_path)
        self.assertIn(content, result)

    def test_read_file_not_found(self):
        """Test reading a file that does not exist."""
        result = self.read_tool._run(file_path="test_fs_data/non_existent_file.txt")
        self.assertIn("Error: File", result)
        self.assertIn("not found", result)

    def test_read_file_outside_sandbox(self):
        """Test that reading from outside the sandbox is forbidden."""
        # Attempt to read a sensitive file from the project root
        file_path = "../../AGENTS.md"
        result = self.read_tool._run(file_path=file_path)
        self.assertIn("Error: Path", result)
        self.assertIn("outside the allowed /sandbox directory", result)

    def test_list_directory_success(self):
        """Test successfully listing a directory's contents."""
        # Create some files and a directory to list
        self.write_tool._run(file_path="test_fs_data/file1.txt", content="1")
        self.write_tool._run(file_path="test_fs_data/subdir/file2.txt", content="2")

        result = self.list_tool._run(path="test_fs_data")
        self.assertIn("file1.txt", result)
        self.assertIn("subdir/", result)

    def test_list_empty_directory(self):
        """Test listing a directory that is empty."""
        result = self.list_tool._run(path="test_fs_data")
        self.assertIn("is empty", result)

    def test_list_directory_outside_sandbox(self):
        """Test that listing a directory outside the sandbox is forbidden."""
        result = self.list_tool._run(path="../")
        self.assertIn("Error: Path", result)
        self.assertIn("outside the allowed /sandbox directory", result)

    def test_list_non_existent_directory(self):
        """Test listing a directory that does not exist."""
        result = self.list_tool._run(path="test_fs_data/non_existent_dir")
        self.assertIn("Error: Directory", result)
        self.assertIn("not found", result)

if __name__ == "__main__":
    unittest.main()
