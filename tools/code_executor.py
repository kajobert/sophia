import asyncio
import threading


import os
import subprocess
from typing import Type

from langchain_core.tools import BaseTool as LangchainBaseTool
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool


# Helper pro univerzální volání sync/async
def run_sync_or_async(coro):
    try:
        loop = asyncio.get_running_loop()
        if threading.current_thread() is threading.main_thread():
            raise RuntimeError(
                "Nelze volat synchronní nástroj v běžící async smyčce. Použijte async variantu nebo run_async()."
            )
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    except RuntimeError:
        return asyncio.run(coro)


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

    file_path: str = Field(
        ...,
        description="The path to the Python script to be executed, relative to the sandbox directory.",
    )


class RunUnitTestsInput(BaseModel):
    """Input for RunUnitTestsTool."""

    test_file_path: str = Field(
        ...,
        description="The path to the test file to be run with unittest, relative to the sandbox directory.",
    )


# --- Tool Implementations ---


class ExecutePythonScriptTool(LangchainBaseTool, BaseTool):
    name: str = "Execute Python Script"
    description: str = "Executes a specified Python script from the /sandbox directory and returns its output."
    args_schema: Type[BaseModel] = ExecutePythonScriptInput

    def execute(self, **kwargs) -> str:
        return self._run(**kwargs)

    def run_sync(self, file_path: str) -> str:
        # Construct the full path safely within the sandbox
        full_path = os.path.join(SANDBOX_DIR, file_path)

        if not _is_within_sandbox(full_path):
            return (
                f"Error: Path '{file_path}' is outside the allowed /sandbox directory."
            )
        if not os.path.exists(full_path):
            return f"Error: Script file '{file_path}' not found in the sandbox."
        if not file_path.endswith(".py"):
            return f"Error: File '{file_path}' is not a Python script."
        try:
            process = subprocess.run(
                ["python3", full_path],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
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

    async def run_async(self, file_path: str) -> str:
        return self.run_sync(file_path)

    def __call__(self, file_path: str) -> str:
        try:
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
            if loop and loop.is_running():
                raise RuntimeError(
                    "ExecutePythonScriptTool: Detekováno async prostředí, použijte await tool.run_async() nebo _arun()."
                )
            return self.run_sync(file_path)
        except Exception as e:
            return f"Error executing Python script: {e}"

    def _run(self, file_path: str) -> str:
        return self.__call__(file_path)

    async def _arun(self, file_path: str) -> str:
        return await self.run_async(file_path)


class RunUnitTestsTool(LangchainBaseTool, BaseTool):
    name: str = "Run Unit Tests"
    description: str = "Runs unit tests from a specified file within the /sandbox directory using 'python -m unittest'."
    args_schema: Type[BaseModel] = RunUnitTestsInput

    def execute(self, **kwargs) -> str:
        return self._run(**kwargs)

    def run_sync(self, test_file_path: str) -> str:
        # Construct the full path safely within the sandbox
        full_path = os.path.join(SANDBOX_DIR, test_file_path)

        if not _is_within_sandbox(full_path):
            return f"Error: Path '{test_file_path}' is outside the allowed /sandbox directory."
        if not os.path.exists(full_path):
            return f"Error: Test file '{test_file_path}' not found in the sandbox."
        if not test_file_path.endswith(".py"):
            return f"Error: File '{test_file_path}' is not a Python file."
        try:
            process = subprocess.run(
                ["python3", "-m", "unittest", full_path],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
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

    async def run_async(self, test_file_path: str) -> str:
        return self.run_sync(test_file_path)

    def __call__(self, test_file_path: str) -> str:
        try:
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
            if loop and loop.is_running():
                raise RuntimeError(
                    "RunUnitTestsTool: Detekováno async prostředí, použijte await tool.run_async() nebo _arun()."
                )
            return self.run_sync(test_file_path)
        except Exception as e:
            return f"Error running unit tests: {e}"

    def _run(self, test_file_path: str) -> str:
        return self.__call__(test_file_path)

    async def _arun(self, test_file_path: str) -> str:
        return await self.run_async(test_file_path)
