import pytest
import os
import sys
from unittest.mock import MagicMock

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Importujeme server, který budeme testovat
from mcp_servers import planning_server

@pytest.fixture(autouse=True)
def clean_task_database():
    """Tato fixtura se spustí před každým testem a zajistí čistou databázi úkolů."""
    planning_server.TASK_DATABASE.clear()
    yield

def test_create_task():
    """Testuje vytváření úkolů a podúkolů."""
    parent_id = planning_server.create_task("Rodičovský úkol").split(": ")[-1]
    child_id = planning_server.create_task("Podúkol", parent_id=parent_id).split(": ")[-1]

    assert parent_id in planning_server.TASK_DATABASE
    assert child_id in planning_server.TASK_DATABASE
    assert planning_server.TASK_DATABASE[parent_id]["subtasks"] == [child_id]
    assert planning_server.TASK_DATABASE[child_id]["parent_id"] == parent_id

def test_get_task_tree():
    """Testuje správné zobrazení stromu úkolů."""
    p_id = planning_server.create_task("Rodič").split(": ")[-1]
    c1_id = planning_server.create_task("Dítě 1", parent_id=p_id).split(": ")[-1]
    c2_id = planning_server.create_task("Dítě 2", parent_id=p_id).split(": ")[-1]
    gc_id = planning_server.create_task("Vnouče", parent_id=c1_id).split(": ")[-1]

    tree = planning_server.get_task_tree()

    assert "Rodič" in tree
    assert "    - [new] Dítě 1" in tree
    assert "        - [new] Vnouče" in tree
    assert "    - [new] Dítě 2" in tree

def test_update_task_status():
    """Testuje aktualizaci stavu úkolu."""
    task_id = planning_server.create_task("Testovací úkol").split(": ")[-1]

    # Validní změna
    result = planning_server.update_task_status(task_id, "in_progress")
    assert "byl aktualizován na 'in_progress'" in result
    assert planning_server.TASK_DATABASE[task_id]["status"] == "in_progress"

    # Nevalidní změna
    result_fail = planning_server.update_task_status(task_id, "neexistujici_stav")
    assert "Chyba: Neplatný stav" in result_fail
    assert planning_server.TASK_DATABASE[task_id]["status"] == "in_progress" # Stav se nezměnil

def test_get_task_details():
    """Testuje získání detailů úkolu."""
    task_id = planning_server.create_task("Detailní úkol").split(": ")[-1]
    details = planning_server.get_task_details(task_id)
    assert f"'description': 'Detailní úkol'" in details
    assert f"'status': 'new'" in details

def test_summarize_text(monkeypatch):
    """
    Testuje sumarizaci textu s mockovaným LLM, aby se neprovádělo skutečné volání.
    """
    # Vytvoříme falešný model a manažera
    mock_model = MagicMock()
    mock_model.generate_content.return_value = ("Toto je shrnutí.", {})

    mock_llm_manager_instance = MagicMock()
    mock_llm_manager_instance.get_llm.return_value = mock_model

    # Podstrčíme naší falešnou instanci, kdykoliv se bude volat LLMManager()
    monkeypatch.setattr("mcp_servers.planning_server.LLMManager", lambda *args, **kwargs: mock_llm_manager_instance)

    long_text = "Toto je velmi dlouhý text, který potřebuje shrnout, protože obsahuje mnoho slov."
    summary = planning_server.summarize_text(long_text)

    assert "Shrnutí textu:" in summary
    assert "Toto je shrnutí." in summary
    # Ověříme, že byl model volán se správným promptem
    mock_model.generate_content.assert_called_once()
    call_args, _ = mock_model.generate_content.call_args
    assert long_text in call_args[0]