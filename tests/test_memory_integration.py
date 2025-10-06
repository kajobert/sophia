import os
import sys
import pytest
import shutil
import uuid
import time

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from core.memory_manager import MemoryManager

@pytest.fixture(scope="function")
def integrated_memory_manager(request):
    """
    Pytest fixtura, která pro každý test vytvoří unikátní dočasný adresář
    a čistou instanci MemoryManager. Tím je zajištěna 100% izolace testů.
    """
    # Vytvoření unikátního adresáře pro každý test
    test_dir = os.path.join(project_root, "tests", f"test_run_{request.node.name}_{int(time.time() * 1000)}")
    os.makedirs(test_dir, exist_ok=True)

    test_sqlite_path = os.path.join(test_dir, "test_memory.db")
    test_chroma_path = os.path.join(test_dir, "test_chroma_db")

    # Vytvoříme instanci MemoryManager s cestami do unikátního adresáře
    manager = MemoryManager(
        db_path=test_sqlite_path,
        ltm_db_path=test_chroma_path,
        ltm_collection_name="test_integration_collection"
    )

    yield manager

    # Úklid po testu
    manager.close()
    # Malá pauza, aby se systémy stihly uvolnit
    time.sleep(0.1)
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

def test_save_session_stores_in_both_dbs(integrated_memory_manager):
    """
    Ověří, že save_session ukládá data jak do SQLite, tak do ChromaDB.
    """
    manager = integrated_memory_manager
    session_id = str(uuid.uuid4())
    task = "Testovací úkol"
    summary = "Toto je souhrn, který by měl být sémanticky prohledatelný."

    # Uložíme session
    manager.save_session(session_id, task, summary)

    # 1. Ověření v SQLite
    cursor = manager.conn.cursor()
    cursor.execute("SELECT task_prompt, summary FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == task
    assert row[1] == summary

    # 2. Ověření v ChromaDB
    search_results = manager.ltm.search_memory(summary, n_results=1)
    assert search_results is not None
    documents = search_results.get('documents', [[]])[0]
    assert len(documents) == 1
    assert documents[0] == summary


def test_get_relevant_memories_uses_semantic_search(integrated_memory_manager):
    """
    Ověří, že get_relevant_memories provádí sémantické vyhledávání.
    """
    manager = integrated_memory_manager

    # Přidáme několik odlišných vzpomínek
    manager.save_session(str(uuid.uuid4()), "Úkol 1", "Oprava chyby v přihlašovacím formuláři.")
    manager.save_session(str(uuid.uuid4()), "Úkol 2", "Optimalizace databázových dotazů pro zrychlení API.")
    manager.save_session(str(uuid.uuid4()), "Úkol 3", "Nasazení nové verze aplikace na produkční server.")

    # Dotaz, který je sémanticky podobný první vzpomínce, ale nepoužívá stejná slova
    query = "Problém s autentizací uživatele"

    memories = manager.get_relevant_memories(query, limit=1)

    assert len(memories) == 1
    assert "přihlašovacím formuláři" in memories[0]['summary']
    assert "databázových dotazů" not in memories[0]['summary']
    assert "produkční server" not in memories[0]['summary']