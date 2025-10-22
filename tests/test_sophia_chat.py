import pytest
import os
import time
import shutil
from unittest.mock import AsyncMock

from backend.database_manager import DatabaseManager

TEMP_DATA_DIR = "tests/temp_data"

@pytest.fixture
def temp_db_manager():
    """Vytvoří dočasnou instanci DatabaseManager pro testy v dočasném adresáři."""
    os.makedirs(TEMP_DATA_DIR, exist_ok=True)
    db_path = os.path.join(TEMP_DATA_DIR, f"test_chat_{int(time.time() * 1000)}.db")
    chroma_path = os.path.join(TEMP_DATA_DIR, f"test_chroma_{int(time.time() * 1000)}")

    manager = DatabaseManager(db_path=db_path, chroma_path=chroma_path)
    yield manager

    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)

def test_add_and_get_message(temp_db_manager):
    session_id = "test_session_1"
    temp_db_manager.add_message(session_id, "user", "Hello")
    messages = temp_db_manager.get_recent_messages(session_id, limit=5)
    assert len(messages) == 1
    assert messages[0][3] == "Hello"

def test_add_and_query_memory(temp_db_manager):
    session_id = "test_session_3"
    temp_db_manager.add_memory(session_id, "The sky is blue.")
    time.sleep(1)
    results = temp_db_manager.query_memory(session_id, "What color is the sky?")
    assert len(results) > 0
    assert "sky is blue" in results[0]

# =============== Testy pro SophiaChatCore ===============

# Updated MockLLMManager to reflect the new two-step logic
class MockLLMManager:
    def __init__(self):
        # Create a mock adapter
        self.mock_adapter = AsyncMock()
        # Set the return value for the method that will be awaited
        self.mock_adapter.generate_content_async.return_value = ("Your name is Jules.", None)

        # The get_llm method should return the mock adapter
        self.get_llm = lambda name: self.mock_adapter

@pytest.mark.asyncio
async def test_handle_message_logic():
    os.makedirs(TEMP_DATA_DIR, exist_ok=True)
    db_path = os.path.join(TEMP_DATA_DIR, f"test_chat_core_{int(time.time() * 1000)}.db")
    chroma_path = os.path.join(TEMP_DATA_DIR, f"test_chroma_core_{int(time.time() * 1000)}")
    db_manager = DatabaseManager(db_path=db_path, chroma_path=chroma_path)

    from backend.sophia_chat_core import SophiaChatCore

    # Temporarily patch the __init__ to prevent it from loading files
    original_init = SophiaChatCore.__init__
    SophiaChatCore.__init__ = lambda self: None

    chat_core = SophiaChatCore()
    chat_core.db_manager = db_manager
    chat_core.llm_manager = MockLLMManager()
    # Mock the loaded prompts
    chat_core.sophia_dna = "Mock DNA"
    chat_core.system_prompt = "Mock System Prompt"

    session_id = "core_test_session"
    user_message = "Hello, what is my name?"

    response = await chat_core.handle_message(session_id, user_message)

    assert response == "Your name is Jules."

    messages = db_manager.get_recent_messages(session_id)
    assert len(messages) == 2
    assert messages[1][3] == "Your name is Jules."

    # Restore original init
    SophiaChatCore.__init__ = original_init

    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)
