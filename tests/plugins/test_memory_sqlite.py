import pytest
from plugins.memory_sqlite import SQLiteMemory
from core.context import SharedContext
import logging
import os

@pytest.mark.asyncio
async def test_sqlite_memory_execute_and_get_history():
    db_file = "test_memory.db"
    memory_plugin = SQLiteMemory()
    memory_plugin.setup({"db_path": db_file})
    context = SharedContext(
        session_id="mem_test",
        current_state="MEMORIZING",
        user_input="My input",
        payload={"llm_response": "My response"},
        logger=logging.getLogger("test")
    )

    await memory_plugin.execute(context)
    history = memory_plugin.get_history("mem_test")

    assert len(history) >= 2
    assert history[-2]["role"] == "user"
    assert history[-2]["content"] == "My input"
    assert history[-1]["role"] == "assistant"
    assert history[-1]["content"] == "My response"

    # Cleanup
    os.remove(db_file)
