import os
import pytest
from tools.code_executor import ExecutePythonScriptTool, RunUnitTestsTool
from tools.file_system import ListDirectoryTool, ReadFileTool, WriteFileTool

# Dočasně přeskočeno kvůli chybě metaclass conflict v langchain-google-genai a Pydantic v2
pytest.skip(
    "Test dočasně přeskočen: metaclass conflict v langchain-google-genai a Pydantic v2. Sledujte upstream.",
    allow_module_level=True,
)

SANDBOX_DIR = os.path.abspath("sandbox")


@pytest.fixture(scope="module")
def setup_sandbox():
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    yield
    # Cleanup: remove test files after tests
    for fname in ["hello.py", "test_hello.py"]:
        fpath = os.path.join(SANDBOX_DIR, fname)
        if os.path.exists(fpath):
            os.remove(fpath)


def test_engineer_and_tester_workflow(setup_sandbox):
    # Engineer vytvoří jednoduchý Python skript
    code = """def hello():\n    return 'Hello, Sophia!'\n\nif __name__ == '__main__':\n    print(hello())\n"""
    write_tool = WriteFileTool()
    result = write_tool.run_sync("hello.py", code)
    assert "Error" not in result

    # Engineer vytvoří testovací soubor
    test_code = """import unittest\nfrom hello import hello\n\nclass TestHello(unittest.TestCase):\n    def test_hello(self):\n        self.assertEqual(hello(), 'Hello, Sophia!')\n\nif __name__ == '__main__':\n    unittest.main()\n"""
    result = write_tool.run_sync("test_hello.py", test_code)
    assert "Error" not in result

    # Engineer spustí skript
    exec_tool = ExecutePythonScriptTool()
    output = exec_tool.run_sync("hello.py")
    assert "Hello, Sophia!" in output

    # Tester spustí unit testy
    test_tool = RunUnitTestsTool()
    test_output = test_tool.run_sync("test_hello.py")
    assert "OK" in test_output or "Ran 1 test" in test_output

    # Tester přečte obsah testovacího souboru
    read_tool = ReadFileTool()
    file_content = read_tool.run_sync("test_hello.py")
    assert "TestHello" in file_content

    # Tester vypíše obsah sandboxu
    list_tool = ListDirectoryTool()
    dir_list = list_tool.run_sync("")
    assert "hello.py" in dir_list and "test_hello.py" in dir_list
