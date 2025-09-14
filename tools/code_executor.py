import os
import subprocess
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

# Define the absolute path for the sandbox directory to ensure security
SANDBOX_DIR = os.path.abspath("sandbox")

def _is_within_sandbox(path: str) -> bool:
    """
    Checks if the given path is securely within the sandbox directory.
    Prevents directory traversal attacks.
    """
    # Resolve the real, absolute path of the given path.
    absolute_path = os.path.realpath(path)
    # Check if the resolved path starts with the sandbox directory's path
    return absolute_path.startswith(SANDBOX_DIR)

# --- Input Schemas for Tools ---

class ExecutePythonScriptInput(BaseModel):
    """Input for ExecutePythonScriptTool."""
    file_path: str = Field(..., description="The path to the Python script to be executed, relative to the sandbox directory.")

class RunUnitTestsInput(BaseModel):
    """Input for RunUnitTestsTool."""
    test_file_path: str = Field(..., description="The path to the test file to be run with unittest, relative to the sandbox directory.")

# --- Tool Implementations ---

class ExecutePythonScriptTool(BaseTool):
    name: str = "Execute Python Script"
    description: str = "Executes a specified Python script from the /sandbox directory and returns its output."
    args_schema: Type[BaseModel] = ExecutePythonScriptInput

    def _run(self, file_path: str) -> str:
        # Construct the full path safely within the sandbox
        full_path = os.path.join(SANDBOX_DIR, file_path)

        # Security check
        if not _is_within_sandbox(full_path):
            return f"Error: Path '{file_path}' is outside the allowed /sandbox directory."

        if not os.path.exists(full_path):
            return f"Error: Script file '{file_path}' not found in the sandbox."

        if not file_path.endswith('.py'):
            return f"Error: File '{file_path}' is not a Python script."

        try:
            # Run the script using subprocess
            process = subprocess.run(
                ['python3', full_path],
                capture_output=True,
                text=True,
                timeout=30,  # Add a timeout for safety
                check=False # Do not raise exception on non-zero exit codes
            )
            stdout = process.stdout
            stderr = process.stderr

            output = ""
            if stdout:
                output += f"--- STDOUT ---\n{stdout}\n"
            if stderr:
                output += f"--- STDERR ---\n{stderr}\n"

            if not output:
                return f"Script '{file_path}' executed with no output."

            return output.strip()

        except subprocess.TimeoutExpired:
            return f"Error: Script '{file_path}' timed out after 30 seconds."
        except Exception as e:
            return f"Error executing Python script: {e}"

class RunUnitTestsTool(BaseTool):
    name: str = "Run Unit Tests"
    description: str = "Runs unit tests from a specified file within the /sandbox directory using 'python -m unittest'."
    args_schema: Type[BaseModel] = RunUnitTestsInput

    def _run(self, test_file_path: str) -> str:
        # Construct the full path safely within the sandbox
        full_path = os.path.join(SANDBOX_DIR, test_file_path)

        # Security check
        if not _is_within_sandbox(full_path):
            return f"Error: Path '{test_file_path}' is outside the allowed /sandbox directory."

        if not os.path.exists(full_path):
            return f"Error: Test file '{test_file_path}' not found in the sandbox."

        if not test_file_path.endswith('.py'):
            return f"Error: File '{test_file_path}' is not a Python file."

        try:
            # Running `python -m unittest <path>` is a reliable way to run a specific test file.
            process = subprocess.run(
                ['python3', '-m', 'unittest', full_path],
                capture_output=True,
                text=True,
                timeout=60, # Longer timeout for tests
                check=False
            )
            # Unittest prints its output to stderr, even for successful runs.
            # We combine stdout and stderr for a complete report.
            output = f"--- Unittest Output for {test_file_path} ---\n"
            if process.stdout:
                output += f"--- STDOUT ---\n{process.stdout}\n"
            if process.stderr:
                output += f"--- STDERR ---\n{process.stderr}\n"

            return output.strip()

        except subprocess.TimeoutExpired:
            return f"Error: Unit test run for '{test_file_path}' timed out after 60 seconds."
        except Exception as e:
            return f"Error running unit tests: {e}"
