
import os
import pytest
import tempfile
import shutil
from tests.conftest import robust_import, safe_remove

ExecutePythonScriptTool = robust_import('tools.code_executor', 'ExecutePythonScriptTool')
RunUnitTestsTool = robust_import('tools.code_executor', 'RunUnitTestsTool')
ListDirectoryTool = robust_import('tools.file_system', 'ListDirectoryTool')
ReadFileTool = robust_import('tools.file_system', 'ReadFileTool')
WriteFileTool = robust_import('tools.file_system', 'WriteFileTool')



# Robustní skip s logováním důvodu
import logging
logging.warning("Test dočasně přeskočen: metaclass conflict v langchain-google-genai a Pydantic v2. Sledujte upstream.")
pytest.skip(
    "Test dočasně přeskočen: metaclass conflict v langchain-google-genai a Pydantic v2. Sledujte upstream.",
    allow_module_level=True,
)




@pytest.fixture
def sandbox_snapshot(tmp_path):
    # Vytvoř snapshot sandbox adresáře v temp adresáři
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir()
    yield sandbox_dir
    # Cleanup přes safe_remove
    for fname in ["hello.py", "test_hello.py"]:
        fpath = sandbox_dir / fname
        safe_remove(str(fpath))


def test_engineer_and_tester_workflow(request, sandbox_snapshot, snapshot):
    # Engineer vytvoří jednoduchý Python skript v sandbox snapshotu
    code = """def hello():\n    return 'Hello, Sophia!'\n\nif __name__ == '__main__':\n    print(hello())\n"""
    write_tool = WriteFileTool()
    hello_path = sandbox_snapshot / "hello.py"
    result = write_tool.run_sync(str(hello_path), code)
    assert "Error" not in result

    # Engineer vytvoří testovací soubor v sandbox snapshotu
    test_code = """import unittest\nfrom hello import hello\n\nclass TestHello(unittest.TestCase):\n    def test_hello(self):\n        self.assertEqual(hello(), 'Hello, Sophia!')\n\nif __name__ == '__main__':\n    unittest.main()\n"""
    test_path = sandbox_snapshot / "test_hello.py"
    result = write_tool.run_sync(str(test_path), test_code)
    assert "Error" not in result

    # Engineer spustí skript v sandbox snapshotu
    exec_tool = ExecutePythonScriptTool()
    output = exec_tool.run_sync(str(hello_path))
    # Approval snapshot výstupu
    snapshot({
        "script_output": output
    })
    assert "Hello, Sophia!" in output

    # Tester spustí unit testy
    test_tool = RunUnitTestsTool()
    test_output = test_tool.run_sync("test_hello.py")
    snapshot({
        "unit_test_output": test_output
    })
    assert "OK" in test_output or "Ran 1 test" in test_output

    # Tester přečte obsah testovacího souboru
    read_tool = ReadFileTool()
    file_content = read_tool.run_sync("test_hello.py")
    snapshot({
        "file_content": file_content
    })
    assert "TestHello" in file_content

    # Tester vypíše obsah sandboxu
    list_tool = ListDirectoryTool()
    dir_list = list_tool.run_sync("")
    snapshot({
        "dir_list": dir_list
    })
    assert "hello.py" in dir_list and "test_hello.py" in dir_list
