import pytest
import os
from backend.database_manager import DatabaseManager
import time

TEMP_DATA_DIR = "tests/temp_data"

@pytest.fixture
def temp_db_manager():
    """Vytvoří dočasnou instanci DatabaseManager pro testy v dočasném adresáři."""
    os.makedirs(TEMP_DATA_DIR, exist_ok=True)
    db_path = os.path.join(TEMP_DATA_DIR, f"test_chat_{int(time.time() * 1000)}.db")
    chroma_path = os.path.join(TEMP_DATA_DIR, f"test_chroma_{int(time.time() * 1000)}")

    manager = DatabaseManager(db_path=db_path, chroma_path=chroma_path)
    yield manager

    # Úklid po testu
    # os.remove se může nepovést, pokud soubor neexistuje, použijeme try-except
    try:
        os.remove(db_path)
    except OSError:
        pass

    # Adresář ChromaDB smažeme rekurzivně
    import shutil
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)

def test_add_and_get_message(temp_db_manager):
    """Otestuje přidání a načtení zprávy ze SQLite."""
    session_id = "test_session_1"
    temp_db_manager.add_message(session_id, "user", "Hello")
    temp_db_manager.add_message(session_id, "assistant", "Hi there")

    messages = temp_db_manager.get_recent_messages(session_id, limit=5)

    assert len(messages) == 2
    assert messages[0][2] == "user" # role
    assert messages[0][3] == "Hello" # content
    assert messages[1][2] == "assistant"
    assert messages[1][3] == "Hi there"

def test_get_messages_limit(temp_db_manager):
    """Otestuje limitaci počtu načtených zpráv."""
    session_id = "test_session_2"
    for i in range(15):
        temp_db_manager.add_message(session_id, "user", f"Message {i}")

    messages = temp_db_manager.get_recent_messages(session_id, limit=10)
    assert len(messages) == 10
    assert "Message 5" in messages[0][3] # Zprávy se řadí od nejstarší

def test_add_and_query_memory(temp_db_manager):
    """Otestuje přidání a sémantické vyhledávání v ChromaDB."""
    session_id = "test_session_3"
    temp_db_manager.add_memory(session_id, "The sky is blue.")
    temp_db_manager.add_memory(session_id, "The grass is green.")

    # Dejme Chromě chvilku na indexaci
    time.sleep(1)

    results = temp_db_manager.query_memory(session_id, "What color is the sky?")

    assert len(results) > 0
    # Očekáváme, že nejrelevantnější bude věta o obloze
    assert "sky is blue" in results[0]

def test_memory_is_session_specific(temp_db_manager):
    """Otestuje, že paměť je specifická pro danou session."""
    session_id_A = "session_A"
    session_id_B = "session_B"

    temp_db_manager.add_memory(session_id_A, "My name is John.")
    temp_db_manager.add_memory(session_id_B, "My name is Jane.")

    time.sleep(1)

    # Dotaz v session A by neměl najít nic z B
    results_A = temp_db_manager.query_memory(session_id_A, "What is my name?")
    assert len(results_A) > 0
    assert "John" in results_A[0]

    # Dotaz v session B by neměl najít nic z A
    results_B = temp_db_manager.query_memory(session_id_B, "What is my name?")
    assert len(results_B) > 0
    assert "Jane" in results_B[0]

# =============== Testy pro SophiaChatCore ===============

# Mock LLMManager, abychom nevolali skutečné API
class MockLLMManager:
    async def get_response(self, prompt, model_alias):
        # Jednoduchá odpověď, která obsahuje část promptu pro ověření
        if "what is my name" in prompt.lower():
            return "Your name is Jules."
        return "This is a mocked response."

@pytest.mark.asyncio
async def test_handle_message_logic():
    """
    Otestuje kompletní logiku metody handle_message v SophiaChatCore.
    Používá skutečný DatabaseManager a mockovaný LLMManager.
    """
    # Vytvoření dočasné databáze v temp adresáři
    os.makedirs(TEMP_DATA_DIR, exist_ok=True)
    db_path = os.path.join(TEMP_DATA_DIR, f"test_chat_core_{int(time.time() * 1000)}.db")
    chroma_path = os.path.join(TEMP_DATA_DIR, f"test_chroma_core_{int(time.time() * 1000)}")
    db_manager = DatabaseManager(db_path=db_path, chroma_path=chroma_path)

    # Vytvoření SophiaChatCore s mockovanými závislostmi
    from backend.sophia_chat_core import SophiaChatCore
    chat_core = SophiaChatCore()
    chat_core.db_manager = db_manager
    chat_core.llm_manager = MockLLMManager()

    session_id = "core_test_session"
    user_message = "Hello, what is my name?"

    # Zpracování zprávy
    response = await chat_core.handle_message(session_id, user_message)

    # 1. Ověření odpovědi
    assert response == "Your name is Jules."

    # 2. Ověření uložení do SQLite
    messages = db_manager.get_recent_messages(session_id)
    assert len(messages) == 2
    assert messages[0][3] == user_message # User message
    assert messages[1][3] == "Your name is Jules." # Assistant response

    # 3. Ověření uložení do ChromaDB
    time.sleep(1) # Počkat na indexaci
    memories = db_manager.query_memory(session_id, "name")
    assert len(memories) == 2
    assert any(user_message in mem for mem in memories)
    assert any("Your name is Jules." in mem for mem in memories)

    # Úklid
    os.remove(db_path)
    import shutil
    shutil.rmtree(chroma_path)
