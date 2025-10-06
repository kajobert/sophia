import os
import sys
import shutil
import pytest

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from tools.project_tools import get_project_summary

# Defiujeme cestu k testovacímu adresáři
TEST_DIR = os.path.join(project_root, "tests/temp_project_structure")

@pytest.fixture(scope="function")
def temp_project():
    """
    Pytest fixtura, která vytvoří dočasnou adresářovou strukturu
    s testovacím souborem a po skončení testu ji smaže.
    """
    # Vytvoření adresáře
    os.makedirs(TEST_DIR, exist_ok=True)

    # Vytvoření testovacího Python souboru
    sample_code = """
class MyClass:
    \"\"\"This is a class docstring.\"\"\"
    def method_with_doc(self, arg1):
        \"\"\"This is a method docstring.\"\"\"
        pass

def top_level_func(arg1, arg2):
    \"\"\"This is a function docstring.\"\"\"
    return True

def func_without_doc(arg):
    # No docstring here
    return arg
"""
    with open(os.path.join(TEST_DIR, "sample_module.py"), "w", encoding="utf-8") as f:
        f.write(sample_code)

    # Vytvoření prázdného souboru pro kontrolu ignorování
    with open(os.path.join(TEST_DIR, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write("test")

    yield TEST_DIR

    # Úklid po testu
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_get_project_summary_with_docstrings(temp_project):
    """
    Testuje, zda get_project_summary správně extrahuje docstringy
    z tříd a funkcí.
    """
    summary = get_project_summary(start_path=temp_project)

    # Ověření, že docstringy jsou přítomny
    assert "class MyClass:" in summary
    assert '"""This is a class docstring."""' in summary

    assert "def method_with_doc(self, arg1):" in summary
    assert '"""This is a method docstring."""' in summary

    assert "def top_level_func(arg1, arg2):" in summary
    assert '"""This is a function docstring."""' in summary

    # Ověření, že funkce bez docstringu má správný formát
    assert "def func_without_doc(arg): ..." in summary

    # Ověření, že ignorovaný soubor není v přehledu
    assert "requirements.txt" not in summary

    # Ověření struktury
    assert "- sample_module.py" in summary
    assert "# class MyClass:" in summary # Ověření odsazení komentáře