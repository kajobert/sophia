import unittest
import os
import shutil
from tools.code_executor import ExecutePythonScriptTool, RunUnitTestsTool
from tools.file_system import WriteFileTool, SANDBOX_DIR


class TestCodeExecutorTools(unittest.TestCase):
    def setUp(self):
        """Set up the test environment before each test."""
        self.executor_tool = ExecutePythonScriptTool()
        self.unittest_tool = RunUnitTestsTool()
        self.write_tool = WriteFileTool()

        self.test_dir = os.path.join(SANDBOX_DIR, "test_exec_data")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

        # Create a simple Python script in the sandbox for testing execution
        self.script_path = "test_exec_data/sample_script.py"
        script_content = "import sys; print('Hello from script'); sys.exit(0)"
        self.write_tool._run(file_path=self.script_path, content=script_content)

        # Create a simple unit test file in the sandbox for testing unittest runner
        self.test_script_path = "test_exec_data/test_sample.py"
        test_content = """
import unittest

class SampleTest(unittest.TestCase):
    def test_always_passes(self):
        self.assertTrue(True, "This should always pass")

if __name__ == '__main__':
    unittest.main()
"""
        self.write_tool._run(file_path=self.test_script_path, content=test_content)

    def tearDown(self):
        """Clean up the test environment after each test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_execute_script_success(self):
        """Test successfully executing a Python script from the sandbox."""
        result = self.executor_tool._run(file_path=self.script_path)
        self.assertIn("Hello from script", result)
        # Successful script execution should not produce stderr
        self.assertNotIn("STDERR", result)

    def test_execute_script_outside_sandbox(self):
        """Test that executing a script outside the sandbox is forbidden."""
        result = self.executor_tool._run(file_path="../../main.py")
        self.assertIn("Error: Path", result)
        self.assertIn("outside the allowed /sandbox directory", result)

    def test_run_unit_tests_success(self):
        """Test successfully running a unit test file from the sandbox."""
        result = self.unittest_tool._run(test_file_path=self.test_script_path)
        # unittest output goes to stderr by default
        self.assertIn("Ran 1 test", result)
        self.assertIn("OK", result)

    def test_run_unit_tests_outside_sandbox(self):
        """Test that running tests outside the sandbox is forbidden."""
        # This file doesn't have to be a valid test; the path check should fail first.
        result = self.unittest_tool._run(
            test_file_path="../../tests/test_file_system_tool.py"
        )
        self.assertIn("Error: Path", result)
        self.assertIn("outside the allowed /sandbox directory", result)

    def test_execute_non_existent_script(self):
        """Test executing a script that does not exist."""
        result = self.executor_tool._run(file_path="test_exec_data/non_existent.py")
        self.assertIn("Error: Script file", result)
        self.assertIn("not found", result)


if __name__ == "__main__":
    unittest.main()
