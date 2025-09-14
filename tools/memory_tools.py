import threading

# Helper pro univerzální volání sync/async
def run_sync_or_async(coro):
    """
    Spustí coroutine bezpečně v jakémkoliv prostředí:
    - Pokud není běžící event loop, použije asyncio.run().
    - Pokud je běžící event loop v hlavním vlákně, použije nest_asyncio nebo vyhodí jasnou chybu.
    - Pokud je běžící event loop v jiném vlákně, použije run_coroutine_threadsafe.
    """
    try:
        loop = asyncio.get_running_loop()
        # Pokud jsme v hlavním vlákně a už běží event loop, není bezpečné volat sync
        if threading.current_thread() is threading.main_thread():
            raise RuntimeError("Nelze volat synchronní nástroj v běžící async smyčce. Použijte async variantu nebo _arun().")
        # Jinak jsme v jiném vlákně, použijeme run_coroutine_threadsafe
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    except RuntimeError:
        # Žádný běžící event loop, použijeme asyncio.run
        return asyncio.run(coro)
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
import asyncio

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

    def run_sync(self, n: int = 10) -> str:
        """
        Bezpečně synchronní varianta (pro CrewAI, main loop atd.)
        """
        try:
            memory = AdvancedMemory()
            recent_memories = run_sync_or_async(memory.read_last_n_memories(n))
            memory.close()
            return json.dumps(recent_memories, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
        except Exception as e:
            return f"Error reading memory: {e}"

    async def run_async(self, n: int = 10) -> str:
        """
        Asynchronní varianta (pro AutoGen, async agenty atd.)
        """
        try:
            memory = AdvancedMemory()
            recent_memories = await memory.read_last_n_memories(n)
            memory.close()
            return json.dumps(recent_memories, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
        except Exception as e:
            return f"Error reading memory: {e}"

    def __call__(self, n: int = 10) -> str:
        """
        Univerzální vstupní bod – automaticky zvolí sync/async podle prostředí.
        """
        try:
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
            if loop and loop.is_running():
                raise RuntimeError("MemoryReaderTool: Detekováno async prostředí, použijte await tool.run_async() nebo _arun().")
            return self.run_sync(n=n)
        except Exception as e:
            return f"Error reading memory: {e}"

    # Zpětná kompatibilita pro CrewAI/AutoGen
    def _run(self, n: int = 10) -> str:
        return self.__call__(n=n)

    async def _arun(self, n: int = 10) -> str:
        return await self.run_async(n=n)

    async def _arun(self, n: int = 10) -> str:
        """
        Asynchronně spustí nástroj pro čtení paměti.
        """
        try:
            memory = AdvancedMemory()
            recent_memories = await memory.read_last_n_memories(n)
            memory.close()
            return json.dumps(recent_memories, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
        except Exception as e:
            return f"Error reading memory: {e}"
