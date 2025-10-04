import pytest
import os
import sys
import shutil
import json
from unittest.mock import MagicMock

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mcp_servers import evolution_server

@pytest.fixture(scope="function", autouse=True)
def cleanup_evolution_server_state():
    """Tato fixtura se spustí před každým testem a zajistí čistý stav."""
    # Vyčištění sandboxu, pokud nějaký zbyl z předchozího neúspěšného běhu
    if evolution_server.ACTIVE_SANDBOX_PATH and os.path.exists(evolution_server.ACTIVE_SANDBOX_PATH):
        shutil.rmtree(evolution_server.ACTIVE_SANDBOX_PATH)
    evolution_server.ACTIVE_SANDBOX_PATH = None

    # Vyčištění archivu
    if os.path.exists(evolution_server.ARCHIVE_DIR):
        shutil.rmtree(evolution_server.ARCHIVE_DIR)
    os.makedirs(evolution_server.ARCHIVE_DIR, exist_ok=True)

    yield # Spuštění testu

def test_sandbox_workflow():
    """Testuje kompletní cyklus práce se sandboxem."""
    # Vytvoření testovacího souboru v projektu
    with open("test_file.txt", "w") as f:
        f.write("original content")

    # 1. Vytvoření sandboxu
    result_create = evolution_server.create_code_sandbox(["test_file.txt"])
    assert "Sandbox byl úspěšně vytvořen" in result_create
    assert evolution_server.ACTIVE_SANDBOX_PATH is not None

    sandbox_path = evolution_server.ACTIVE_SANDBOX_PATH
    sandbox_file_path = os.path.join(sandbox_path, "test_file.txt")
    assert os.path.exists(sandbox_file_path)

    # 2. Úprava souboru v sandboxu
    with open(sandbox_file_path, "w") as f:
        f.write("modified content")

    # 3. Porovnání změn
    result_compare = evolution_server.compare_sandbox_changes("test_file.txt")
    assert "---" in result_compare # '---' je typické pro diff výstup
    assert "modified content" in result_compare

    # 4. Spuštění příkazu v sandboxu
    result_run = evolution_server.run_in_sandbox("ls -l")
    assert "test_file.txt" in result_run

    # 5. Zničení sandboxu
    result_destroy = evolution_server.destroy_sandbox()
    assert "byl úspěšně zničen" in result_destroy
    assert not os.path.exists(sandbox_path)
    assert evolution_server.ACTIVE_SANDBOX_PATH is None

    # Úklid testovacího souboru v projektu
    os.remove("test_file.txt")

def test_propose_refactoring(monkeypatch):
    """Testuje navrhování refaktoringu s mockovaným LLM."""
    # Mockování file_system nástroje, který je použit interně
    mock_read_section = MagicMock(return_value="def old_func(): pass")
    monkeypatch.setattr("mcp_servers.evolution_server.read_file_section", mock_read_section)

    # Mockování LLM
    mock_model = MagicMock()
    mock_model.generate_content.return_value = ("def new_func():\n    # New and improved\n    pass", {})
    mock_llm_manager_instance = MagicMock()
    mock_llm_manager_instance.get_llm.return_value = mock_model
    monkeypatch.setattr("mcp_servers.evolution_server.LLMManager", lambda *args, **kwargs: mock_llm_manager_instance)

    result = evolution_server.propose_refactoring("dummy/path.py", "old_func")

    assert "Návrh na refaktoring" in result
    assert "def new_func()" in result
    mock_read_section.assert_called_once_with("PROJECT_ROOT/dummy/path.py", "old_func")
    mock_model.generate_content.assert_called_once()

def test_task_archiving():
    """Testuje archivaci a prohledávání dokončených úkolů."""
    task_id = "task-123"
    summary = "Vyřešil jsem bug v přihlašování."
    history = [("krok1", "výsledek1")]

    # Archivace
    result_archive = evolution_server.archive_completed_task(task_id, summary, history)
    assert "byl úspěšně archivován" in result_archive
    assert os.path.exists(os.path.join(evolution_server.ARCHIVE_DIR, f"{task_id}.json"))

    # Prohledávání
    result_search = evolution_server.search_task_archive("přihlašování")
    assert "Nalezené relevantní úkoly" in result_search
    assert summary in result_search

    result_no_match = evolution_server.search_task_archive("neexistující dotaz")
    assert "nebyly nalezeny žádné relevantní úkoly" in result_no_match

def test_update_self_knowledge():
    """Testuje přidávání nových znalostí."""
    if os.path.exists(evolution_server.KNOWLEDGE_FILE):
        os.remove(evolution_server.KNOWLEDGE_FILE)

    knowledge = "Toto je nový poznatek."
    result = evolution_server.update_self_knowledge(knowledge)
    assert "byla úspěšně aktualizována" in result

    with open(evolution_server.KNOWLEDGE_FILE, "r") as f:
        content = f.read()
        assert knowledge in content

    # Úklid
    os.remove(evolution_server.KNOWLEDGE_FILE)