import pytest
import os
import sys
import shutil
import json
from unittest.mock import MagicMock, AsyncMock

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from mcp_servers import evolution_server

@pytest.fixture(scope="function", autouse=True)
def cleanup_evolution_server_state():
    """Tato fixtura se spustí před každým testem a zajistí čistý stav."""
    if evolution_server.ACTIVE_SANDBOX_PATH and os.path.exists(evolution_server.ACTIVE_SANDBOX_PATH):
        shutil.rmtree(evolution_server.ACTIVE_SANDBOX_PATH)
    evolution_server.ACTIVE_SANDBOX_PATH = None
    if os.path.exists(evolution_server.ARCHIVE_DIR):
        shutil.rmtree(evolution_server.ARCHIVE_DIR)
    os.makedirs(evolution_server.ARCHIVE_DIR, exist_ok=True)
    yield

def test_sandbox_workflow():
    """Testuje kompletní cyklus práce se sandboxem."""
    with open("test_file.txt", "w") as f:
        f.write("original content")
    result_create = evolution_server.create_code_sandbox(["test_file.txt"])
    assert "Sandbox byl úspěšně vytvořen" in result_create
    sandbox_path = evolution_server.ACTIVE_SANDBOX_PATH
    sandbox_file_path = os.path.join(sandbox_path, "test_file.txt")
    assert os.path.exists(sandbox_file_path)
    with open(sandbox_file_path, "w") as f:
        f.write("modified content")
    result_compare = evolution_server.compare_sandbox_changes("test_file.txt")
    assert "---" in result_compare
    assert "modified content" in result_compare
    result_run = evolution_server.run_in_sandbox("ls -l")
    assert "test_file.txt" in result_run
    result_destroy = evolution_server.destroy_sandbox()
    assert "byl úspěšně zničen" in result_destroy
    os.remove("test_file.txt")

@pytest.mark.asyncio
async def test_propose_refactoring(monkeypatch):
    """Testuje navrhování refaktoringu s mockovaným LLM."""
    mock_read_section = MagicMock(return_value="def old_func(): pass")
    monkeypatch.setattr("mcp_servers.evolution_server.read_file_section", mock_read_section)

    # Mock the LLMManager and its methods
    mock_model = AsyncMock()
    mock_model.generate_content_async.return_value = ("def new_func():\n    # New and improved\n    pass", {})
    mock_llm_manager_instance = MagicMock()
    mock_llm_manager_instance.get_llm.return_value = mock_model
    monkeypatch.setattr("mcp_servers.evolution_server.LLMManager", lambda *args, **kwargs: mock_llm_manager_instance)

    result = await evolution_server.propose_refactoring("dummy/path.py", "old_func")

    assert "Návrh na refaktoring" in result
    assert "def new_func()" in result
    mock_read_section.assert_called_once_with("dummy/path.py", "old_func")
    mock_llm_manager_instance.get_llm.assert_called_once_with("powerful")
    mock_model.generate_content_async.assert_called_once()

def test_task_archiving():
    """Testuje archivaci a prohledávání dokončených úkolů."""
    task_id = "task-123"
    summary = "Vyřešil jsem bug v přihlašování."
    history = [("krok1", "výsledek1")]
    result_archive = evolution_server.archive_completed_task(task_id, summary, history)
    assert "byl úspěšně archivován" in result_archive
    result_search = evolution_server.search_task_archive("přihlašování")
    assert "Nalezené relevantní úkoly" in result_search
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
    os.remove(evolution_server.KNOWLEDGE_FILE)