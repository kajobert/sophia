import pytest
import os
import sys
import shutil

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mcp_servers import debugging_server

# Defiujeme cestu k testovacímu adresáři
TEST_DIR = os.path.join(project_root, "tests/temp_debug_files")

@pytest.fixture(scope="module")
def temp_test_file():
    """
    Fixtura, která vytvoří dočasný Python soubor pro testování
    debugovacích nástrojů a po skončení všech testů ho smaže.
    """
    os.makedirs(TEST_DIR, exist_ok=True)
    file_path = os.path.join(TEST_DIR, "sample_to_debug.py")

    # Vytvoření souboru s nějakým obsahem pro analýzu
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("""
def my_function(x):
    # This function is simple
    if x > 10:
        return True
    return False

class MyClass:
    def __init__(self):
        pass
""")

    yield file_path

    # Úklid po testu
    shutil.rmtree(TEST_DIR)

def test_profile_code_execution(temp_test_file):
    """
    Testuje, zda profile_code_execution vrací výstup z cProfile.
    """
    # Použijeme samotný testovací soubor jako skript ke spuštění
    command_to_run = f"{sys.executable} {temp_test_file}"
    result = debugging_server.profile_code_execution(command_to_run)

    assert "ncalls" in result
    assert "tottime" in result
    assert "percall" in result
    assert "cumtime" in result
    assert "filename:lineno(function)" in result

def test_run_static_code_analyzer(temp_test_file):
    """
    Testuje, zda run_static_code_analyzer vrací výstup z Pylint.
    """
    result = debugging_server.run_static_code_analyzer(temp_test_file)

    assert "Your code has been rated at" in result
    assert "-----------------------------------" in result

def test_get_code_complexity(temp_test_file):
    """
    Testuje, zda get_code_complexity vrací reporty z Radonu.
    """
    result = debugging_server.get_code_complexity(temp_test_file)

    assert "--- Cyclomatic Complexity Report ---" in result
    assert "--- Maintainability Index Report ---" in result
    # Zpřesnění testu: hledáme konkrétní části reportu
    assert "my_function - A" in result # Radon označuje rank 'A' jako nejlepší
    assert "sample_to_debug.py - A" in result