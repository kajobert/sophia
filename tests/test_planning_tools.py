import pytest
import os
import sys
import json
from unittest.mock import MagicMock, AsyncMock, patch

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

def _get_id(result_string: str) -> str:
    """Helper funkce pro extrakci ID z návratové hodnoty create_task."""
    return result_string.split(": ")[-1]

def test_create_task():
    """Testuje vytváření úkolů a podúkolů."""
    parent_id = _get_id(planning_server.create_task("Rodičovský úkol"))
    child_id = _get_id(planning_server.create_task("Podúkol", parent_id=parent_id))

    assert parent_id in planning_server.TASK_DATABASE
    assert child_id in planning_server.TASK_DATABASE
    assert planning_server.TASK_DATABASE[parent_id]["subtasks"] == [child_id]
    assert planning_server.TASK_DATABASE[child_id]["parent_id"] == parent_id

def test_get_task_tree():
    """Testuje správné zobrazení stromu úkolů."""
    p_id = _get_id(planning_server.create_task("Rodič"))
    c1_id = _get_id(planning_server.create_task("Dítě 1", parent_id=p_id))
    _ = _get_id(planning_server.create_task("Dítě 2", parent_id=p_id))
    _ = _get_id(planning_server.create_task("Vnouče", parent_id=c1_id))

    tree = planning_server.get_task_tree()

    assert "Rodič" in tree
    assert "    - [new] Dítě 1" in tree
    assert "        - [new] Vnouče" in tree
    assert "    - [new] Dítě 2" in tree

def test_update_task_status():
    """Testuje aktualizaci stavu úkolu."""
    task_id = _get_id(planning_server.create_task("Testovací úkol"))
    result = planning_server.update_task_status(task_id, "in_progress")
    assert "byl aktualizován na 'in_progress'" in result
    assert planning_server.TASK_DATABASE[task_id]["status"] == "in_progress"

def test_get_task_details():
    """Testuje získání detailů úkolu."""
    task_id = _get_id(planning_server.create_task("Detailní úkol"))
    details_str = planning_server.get_task_details(task_id)
    details = json.loads(details_str)
    assert details["description"] == "Detailní úkol"

# --- Nové testy pro get_next_executable_task ---

def test_get_next_task_simple_case():
    """Testuje základní případ: jeden proveditelný úkol."""
    task_id = _get_id(planning_server.create_task("Jednoduchý úkol"))
    result_str = planning_server.get_next_executable_task()
    result = json.loads(result_str)
    assert result["id"] == task_id
    assert planning_server.TASK_DATABASE[task_id]["status"] == "in_progress"

def test_get_next_task_unblocked_by_completed_subtask():
    """Testuje, že se rodičovský úkol stane proveditelným po dokončení podúkolů."""
    parent_id = _get_id(planning_server.create_task("Rodič"))
    child_id = _get_id(planning_server.create_task("Dítě", parent_id=parent_id))

    child_task = json.loads(planning_server.get_next_executable_task())
    assert child_task["id"] == child_id
    planning_server.update_task_status(child_id, "completed")

    parent_task = json.loads(planning_server.get_next_executable_task())
    assert parent_task["id"] == parent_id

def test_get_next_task_no_executable_tasks():
    """Testuje, že se nevrátí žádný úkol, pokud žádný není proveditelný."""
    task_id = _get_id(planning_server.create_task("Probíhající úkol"))
    planning_server.update_task_status(task_id, "in_progress")
    result = planning_server.get_next_executable_task()
    assert "Žádné další proveditelné úkoly nebyly nalezeny" in result

@patch('mcp_servers.planning_server.uuid.uuid4')
def test_get_next_task_complex_tree_deterministic(mock_uuid4):
    """
    Testuje složitější strom závislostí s kontrolovanými UUID,
    aby byl test plně deterministický.
    """
    # Kontrolujeme UUID, abychom zaručili pořadí při třídění
    mock_uuid4.side_effect = [
        'a0000000-0000-0000-0000-000000000000',  # A
        'b0000000-0000-0000-0000-000000000000',  # B
        'c0000000-0000-0000-0000-000000000000',  # C
        'd0000000-0000-0000-0000-000000000000',  # D
    ]
    # Struktura: A -> (B, C), C -> D
    a_id = _get_id(planning_server.create_task("A"))
    b_id = _get_id(planning_server.create_task("B", parent_id=a_id))
    c_id = _get_id(planning_server.create_task("C", parent_id=a_id))
    d_id = _get_id(planning_server.create_task("D", parent_id=c_id))

    # Očekávané pořadí exekuce díky řízeným UUIDs: B -> D -> C -> A

    # 1. Měl by se vrátit B (je proveditelný a má nejnižší ID z proveditelných)
    task1 = json.loads(planning_server.get_next_executable_task())
    assert task1["id"] == b_id
    planning_server.update_task_status(b_id, "completed")

    # 2. Měl by se vrátit D (je proveditelný a má nejnižší ID z proveditelných)
    task2 = json.loads(planning_server.get_next_executable_task())
    assert task2["id"] == d_id
    planning_server.update_task_status(d_id, "completed")

    # 3. Teď je C proveditelný (D je hotové)
    task3 = json.loads(planning_server.get_next_executable_task())
    assert task3["id"] == c_id
    planning_server.update_task_status(c_id, "completed")

    # 4. Teď je A proveditelný (B a C jsou hotové)
    task4 = json.loads(planning_server.get_next_executable_task())
    assert task4["id"] == a_id
    planning_server.update_task_status(a_id, "completed")

    # 5. Žádné další úkoly
    result = planning_server.get_next_executable_task()
    assert "Žádné další proveditelné úkoly nebyly nalezeny" in result

@pytest.mark.asyncio
async def test_summarize_text(monkeypatch):
    """Testuje sumarizaci textu s mockovaným LLM."""
    mock_model = AsyncMock()
    mock_model.generate_content_async.return_value = ("Toto je shrnutí.", {})
    mock_llm_manager_instance = MagicMock()
    mock_llm_manager_instance.get_llm.return_value = mock_model
    monkeypatch.setattr("mcp_servers.planning_server.LLMManager", lambda *args, **kwargs: mock_llm_manager_instance)
    summary = await planning_server.summarize_text("Dlouhý text.")
    assert "Toto je shrnutí." in summary