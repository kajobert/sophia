from tools.code_executor import ExecutePythonScriptTool, RunUnitTestsTool


def test_execute_python_script_tool():
    tool = ExecutePythonScriptTool()
    assert hasattr(tool, "run_sync")
    assert hasattr(tool, "__call__")


def test_run_unit_tests_tool():
    tool = RunUnitTestsTool()
    assert hasattr(tool, "run_sync")
    assert hasattr(tool, "__call__")
