# /tools/memory_tools.py
"""
Nástroje pro interakci s pamětí Sophie.
"""
from crewai.tools import tool
from memory.advanced_memory import AdvancedMemory
import json
from core.utils import CustomJSONEncoder
import asyncio
from typing import Optional

def run_sync_in_new_loop(coro):
    """
    Spustí coroutine v nové událostní smyčce.
    Je to bezpečný způsob, jak volat async kód ze sync kontextu v CrewAI.
    """
    return asyncio.run(coro)

@tool("Memory Reader")
def read_memory(n: int = 10, mem_type: Optional[str] = None) -> str:
    """
    Reads the N most recent entries from the memory.
    You can optionally filter by `mem_type` to get specific types of memories,
    such as 'CONVERSATION' for past dialogues or 'ORCHESTRATION_RESULT' for task outcomes.
    """
    try:
        memory = AdvancedMemory()
        # Since CrewAI runs in a sync context, we need to run the async method in a new event loop.
        recent_memories = run_sync_in_new_loop(memory.read_last_n_memories(n=n, mem_type=mem_type))
        memory.close()
        return json.dumps(recent_memories, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
    except Exception as e:
        return f"Error reading memory: {e}"
