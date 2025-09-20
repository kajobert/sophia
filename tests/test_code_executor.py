
from tests.conftest import robust_import



def test_execute_python_script_tool(request, snapshot):
    ExecutePythonScriptTool = robust_import('tools.code_executor', 'ExecutePythonScriptTool')
    tool = ExecutePythonScriptTool()
    result = [hasattr(tool, "run_sync"), hasattr(tool, "__call__")]
    snapshot(str(result))



def test_run_unit_tests_tool(request, snapshot):
    RunUnitTestsTool = robust_import('tools.code_executor', 'RunUnitTestsTool')
    tool = RunUnitTestsTool()
    result = [hasattr(tool, "run_sync"), hasattr(tool, "__call__")]
    snapshot(str(result))
