
import os
import shutil
import tempfile
import pytest
from tests.conftest import robust_import, safe_remove

ExecutePythonScriptTool = robust_import('tools.code_executor', 'ExecutePythonScriptTool')
RunUnitTestsTool = robust_import('tools.code_executor', 'RunUnitTestsTool')
WriteFileTool = robust_import('tools.file_system', 'WriteFileTool')
SANDBOX_DIR = os.path.abspath('sandbox')


@pytest.fixture
def sandbox_snapshot():
    # Vytvoř snapshot sandboxu v repozitáři (sandbox/test_exec_data)
    test_dir = os.path.join('sandbox', 'test_exec_data')
    os.makedirs(test_dir, exist_ok=True)
    script_path = os.path.join('test_exec_data', 'sample_script.py')
    script_content = "import sys; print('Hello from script'); sys.exit(0)"
    write_tool = WriteFileTool()
    write_tool._run(file_path=script_path, content=script_content)
    test_script_path = os.path.join('test_exec_data', 'test_sample.py')
    test_content = (
        'import unittest\n\nclass SampleTest(unittest.TestCase):\n    def test_always_passes(self):\n        self.assertTrue(True, \'This should always pass\')\n\nif __name__ == "__main__":\n    unittest.main()\n'
    )
    write_tool._run(file_path=test_script_path, content=test_content)
    yield script_path, test_script_path
    # Cleanup přes safe_remove
    safe_remove(os.path.join('sandbox', script_path))
    safe_remove(os.path.join('sandbox', test_script_path))
    safe_remove(os.path.join('sandbox', 'test_exec_data'))


def test_execute_script_success(request, sandbox_snapshot, snapshot):
    script_path, test_script_path = sandbox_snapshot
    executor_tool = ExecutePythonScriptTool()
    result = executor_tool._run(file_path=script_path)
    assert "Hello from script" in result
    assert "STDERR" not in result
    snapshot(result)


def test_execute_script_outside_sandbox(request, sandbox_snapshot, snapshot):
    executor_tool = ExecutePythonScriptTool()
    result = executor_tool._run(file_path="../../main.py")
    assert "Error: Path" in result or "outside the allowed /sandbox directory" in result
    snapshot(result)



