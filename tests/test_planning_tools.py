import pytest
import os
import sys
import json
import time
from unittest.mock import MagicMock, AsyncMock

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Importujeme server, který budeme testovat
from mcp_servers.worker import planning_server

@pytest.fixture(autouse=True)
def clean_task_database():
    """Tato fixtura se spustí před každým testem a zajistí čistou databázi úkolů."""
    planning_server.TASK_DATABASE.clear()
    yield

def _get_id(result_string: str) -> str:
    """Helper funkce pro extrakci ID z návratové hodnoty create_task."""
    return result_string.split(": ")[-1]

def test_create_task_adds_timestamp():
    """Testuje, že při vytváření úkolu je přidána časová značka."""
    task_id = _get_id(planning_server.create_task("Úkol s časovou značkou"))
    assert task_id in planning_server.TASK_DATABASE
    assert "created_at" in planning_server.TASK_DATABASE[task_id]
    assert isinstance(planning_server.TASK_DATABASE[task_id]["created_at"], float)

def test_get_main_goal():
    """Testuje, že funkce správně vrací hlavní cíl."""
    main_goal_desc = "Toto je hlavní cíl"
    parent_id = _get_id(planning_server.create_task(main_goal_desc))
    time.sleep(0.01)
    _ = _get_id(planning_server.create_task("Podúkol", parent_id=parent_id))

    # I když existují podúkoly, funkce by měla vrátit popis kořenového úkolu
    assert planning_server.get_main_goal() == main_goal_desc

def test_get_main_goal_no_tasks():
    """Testuje chování, když neexistují žádné úkoly."""
    assert "Není definován žádný hlavní cíl" in planning_server.get_main_goal()

def test_get_next_task_is_fifo():
    """Testuje, že get_next_executable_task vrací úkoly v pořadí, v jakém byly vytvořeny (FIFO)."""
    task1_id = _get_id(planning_server.create_task("První úkol"))
    time.sleep(0.01)
    task2_id = _get_id(planning_server.create_task("Druhý úkol"))

    next_task1 = json.loads(planning_server.get_next_executable_task())
    assert next_task1["id"] == task1_id
    planning_server.update_task_status(task1_id, "completed")

    next_task2 = json.loads(planning_server.get_next_executable_task())
    assert next_task2["id"] == task2_id

def test_get_next_task_unblocked_by_completed_subtask():
    """Testuje, že se rodičovský úkol stane proveditelným až po dokončení podúkolů."""
    parent_id = _get_id(planning_server.create_task("Rodič"))
    time.sleep(0.01)
    child_id = _get_id(planning_server.create_task("Dítě", parent_id=parent_id))

    child_task = json.loads(planning_server.get_next_executable_task())
    assert child_task["id"] == child_id

    planning_server.update_task_status(child_id, "completed")

    parent_task = json.loads(planning_server.get_next_executable_task())
    assert parent_task["id"] == parent_id

def test_get_next_task_complex_tree_is_chronological():
    """
    Testuje složitější strom závislostí a ověřuje, že pořadí je deterministické.
    """
    a_id = _get_id(planning_server.create_task("A"))
    time.sleep(0.01)
    b_id = _get_id(planning_server.create_task("B", parent_id=a_id))
    time.sleep(0.01)
    c_id = _get_id(planning_server.create_task("C", parent_id=a_id))
    time.sleep(0.01)
    d_id = _get_id(planning_server.create_task("D", parent_id=c_id))

    task1 = json.loads(planning_server.get_next_executable_task())
    assert task1["id"] == b_id
    planning_server.update_task_status(b_id, "completed")

    task2 = json.loads(planning_server.get_next_executable_task())
    assert task2["id"] == d_id
    planning_server.update_task_status(d_id, "completed")

    task3 = json.loads(planning_server.get_next_executable_task())
    assert task3["id"] == c_id
    planning_server.update_task_status(c_id, "completed")

    task4 = json.loads(planning_server.get_next_executable_task())
    assert task4["id"] == a_id
    planning_server.update_task_status(a_id, "completed")

    result = planning_server.get_next_executable_task()
    assert "Žádné další proveditelné úkoly nebyly nalezeny" in result

@pytest.mark.asyncio
async def test_summarize_text(monkeypatch):
    """Testuje sumarizaci textu s mockovaným LLM."""
    mock_model = AsyncMock()
    mock_model.generate_content_async.return_value = ("Toto je shrnutí.", {})
    mock_llm_manager_instance = MagicMock()
    mock_llm_manager_instance.get_llm.return_value = mock_model
    monkeypatch.setattr("mcp_servers.worker.planning_server.LLMManager", lambda *args, **kwargs: mock_llm_manager_instance)
    summary = await planning_server.summarize_text("Dlouhý text.")
    assert "Toto je shrnutí." in summary