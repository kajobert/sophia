import unittest
import os
import shutil
import asyncio
from tools.file_system import (
    WriteFileTool,
    ReadFileTool,
    ListDirectoryTool,
    SANDBOX_DIR,
    PathOutsideSandboxError,
    FileSystemNotFoundError,
    IsDirectoryError,
    NotDirectoryError,
    FileSystemError,
)


class TestFileSystemTools(unittest.TestCase):
    def setUp(self):
        """Set up the test environment before each test."""
        self.write_tool = WriteFileTool()
        self.read_tool = ReadFileTool()
        self.list_tool = ListDirectoryTool()

        # Ensure the sandbox directory exists and is clean for the test
        if not os.path.exists(SANDBOX_DIR):
            os.makedirs(SANDBOX_DIR)

        self.test_dir_name = "test_fs_data"
        self.test_dir = os.path.join(SANDBOX_DIR, self.test_dir_name)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

    def tearDown(self):
        """Clean up the test environment after each test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    # --- WriteFileTool Tests ---

    def test_write_file_success(self):
        """Test successfully writing a file."""
        file_path = os.path.join(self.test_dir_name, "test_write.txt")
        content = "Hello, Sandbox!"
        result = self.write_tool._run(file_path=file_path, content=content)
        self.assertIn("successfully", result)

        full_path = os.path.join(self.test_dir, "test_write.txt")
        self.assertTrue(os.path.exists(full_path))
        with open(full_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_write_file_outside_sandbox(self):
        """Test that writing outside the sandbox raises FileSystemError."""
        with self.assertRaises(FileSystemError) as cm:
            self.write_tool._run(file_path="../outside_test.txt", content="breach")
        self.assertIsInstance(cm.exception.__cause__, PathOutsideSandboxError)

    # --- ReadFileTool Tests ---

    def test_read_file_success(self):
        """Test successfully reading a file."""
        file_path = os.path.join(self.test_dir_name, "test_read.txt")
        content = "Readable content."
        self.write_tool._run(file_path=file_path, content=content)

        result = self.read_tool._run(file_path=file_path)
        self.assertEqual(result, content)

    def test_read_file_not_found(self):
        """Test reading a non-existent file raises FileSystemError."""
        with self.assertRaises(FileSystemError) as cm:
            self.read_tool._run(
                file_path=os.path.join(self.test_dir_name, "non_existent.txt")
            )
        self.assertIsInstance(cm.exception.__cause__, FileSystemNotFoundError)

    def test_read_file_is_directory(self):
        """Test that reading a directory raises FileSystemError."""
        with self.assertRaises(FileSystemError) as cm:
            self.read_tool._run(file_path=self.test_dir_name)
        self.assertIsInstance(cm.exception.__cause__, IsDirectoryError)

    def test_read_file_outside_sandbox(self):
        """Test reading outside the sandbox raises FileSystemError."""
        with self.assertRaises(FileSystemError) as cm:
            self.read_tool._run(file_path="../../AGENTS.md")
        self.assertIsInstance(cm.exception.__cause__, PathOutsideSandboxError)

    # --- ListDirectoryTool Tests ---

    def test_list_directory_success(self):
        """Test successfully listing a directory."""
        self.write_tool._run(
            file_path=os.path.join(self.test_dir_name, "file1.txt"), content="1"
        )
        self.write_tool._run(
            file_path=os.path.join(self.test_dir_name, "subdir/file2.txt"), content="2"
        )

        result = self.list_tool._run(path=self.test_dir_name)
        self.assertIn("file1.txt", result)
        self.assertIn("subdir/", result)
        self.assertEqual(len(result), 2)

    def test_list_empty_directory(self):
        """Test listing an empty directory returns an empty list."""
        result = self.list_tool._run(path=self.test_dir_name)
        self.assertEqual(result, [])

    def test_list_directory_not_found(self):
        """Test listing a non-existent directory raises FileSystemError."""
        with self.assertRaises(FileSystemError) as cm:
            self.list_tool._run(
                path=os.path.join(self.test_dir_name, "non_existent_dir")
            )
        self.assertIsInstance(cm.exception.__cause__, FileSystemNotFoundError)

    def test_list_directory_is_file(self):
        """Test that listing a file raises FileSystemError."""
        file_path = os.path.join(self.test_dir_name, "test_file.txt")
        self.write_tool._run(file_path=file_path, content="not a dir")
        with self.assertRaises(FileSystemError) as cm:
            self.list_tool._run(path=file_path)
        self.assertIsInstance(cm.exception.__cause__, NotDirectoryError)

    def test_list_directory_outside_sandbox(self):
        """Test listing outside the sandbox raises FileSystemError."""
        with self.assertRaises(FileSystemError) as cm:
            self.list_tool._run(path="../")
        self.assertIsInstance(cm.exception.__cause__, PathOutsideSandboxError)

    # --- Async Tests ---

    def test_arun_read_file(self):
        """Test the async _arun method for ReadFileTool."""

        async def run_test():
            file_path = os.path.join(self.test_dir_name, "async_read.txt")
            content = "Async readable content."
            self.write_tool._run(file_path=file_path, content=content)

            result = await self.read_tool._arun(file_path=file_path)
            self.assertEqual(result, content)

            with self.assertRaises(FileSystemError) as cm:
                await self.read_tool._arun(file_path="non_existent_async.txt")
            self.assertIsInstance(cm.exception.__cause__, FileSystemNotFoundError)

        asyncio.run(run_test())

    def test_arun_list_directory(self):
        """Test the async _arun method for ListDirectoryTool."""

        async def run_test():
            self.write_tool._run(
                file_path=os.path.join(self.test_dir_name, "async_file.txt"),
                content="...",
            )

            result = await self.list_tool._arun(path=self.test_dir_name)
            self.assertIn("async_file.txt", result)

        asyncio.run(run_test())

    # --- Alias acceptance tests for public execute() methods ---

    def test_writefile_execute_aliases(self):
        """WriteFileTool.execute should accept both 'file_path' and 'path' aliases."""
        # using canonical name
        res1 = self.write_tool.execute(file_path=os.path.join(self.test_dir_name, "exec_a.txt"), content="A")
        self.assertIn("written successfully", res1)
        # using alias
        res2 = self.write_tool.execute(path=os.path.join(self.test_dir_name, "exec_b.txt"), content="B")
        self.assertIn("written successfully", res2)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "exec_a.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "exec_b.txt")))

    def test_readfile_execute_aliases(self):
        """ReadFileTool.execute should accept both 'file_path' and 'path' aliases."""
        target = os.path.join(self.test_dir_name, "exec_read.txt")
        self.write_tool._run(file_path=target, content="readme")
        out1 = self.read_tool.execute(file_path=target)
        self.assertIn("readme", out1)
        out2 = self.read_tool.execute(path=target)
        self.assertIn("readme", out2)

    def test_listdir_execute_aliases(self):
        """ListDirectoryTool.execute should accept 'path', 'directory', and 'dir' aliases."""
        # create files
        self.write_tool._run(file_path=os.path.join(self.test_dir_name, "l1.txt"), content="x")
        out1 = self.list_tool.execute(path=self.test_dir_name)
        self.assertIsInstance(out1, list)
        out2 = self.list_tool.execute(directory=self.test_dir_name)
        self.assertIsInstance(out2, list)
        out3 = self.list_tool.execute(dir=self.test_dir_name)
        self.assertIsInstance(out3, list)


if __name__ == "__main__":
    unittest.main()
