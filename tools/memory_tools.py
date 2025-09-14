# /tools/memory_tools.py
"""
Nástroje pro interakci s pamětí Sophie.
"""
from langchain_core.tools import BaseTool
from memory.advanced_memory import AdvancedMemory
from typing import Type
from pydantic import BaseModel, Field
import json
from core.utils import CustomJSONEncoder

class MemoryReaderToolInput(BaseModel):
    """Pydantic model for MemoryReaderTool input."""
    n: int = Field(10, description="The number of recent memories to read.")

class MemoryReaderTool(BaseTool):
    """
    Nástroj pro čtení posledních N záznamů z paměti.
    """
    name: str = "Memory Reader"
    description: str = "Reads the N most recent entries from the memory. Use it to understand what happened recently."
    args_schema: Type[BaseModel] = MemoryReaderToolInput

    def _run(self, n: int = 10) -> str:
        """
        Synchronní zástupce pro asynchronní metodu.
        """
        # This is a fallback for synchronous calls.
        # The main application should use the async version.
        import asyncio
        try:
            return asyncio.run(self._arun(n))
        except RuntimeError:
            return "Error: asyncio.run() cannot be called from a running event loop. Use _arun instead."

    async def _arun(self, n: int = 10) -> str:
        """
        Asynchronně spustí nástroj pro čtení paměti.
        """
        try:
            memory = AdvancedMemory()
            recent_memories = await memory.read_last_n_memories(n)
            memory.close()
            # Převedeme seznam slovníků na JSON string pro čistší výstup
            return json.dumps(recent_memories, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
        except Exception as e:
            return f"Error reading memory: {e}"
