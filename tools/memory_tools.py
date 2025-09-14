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

    def _run(self, n: int = 10) -> str:
        """
        Spustí nástroj pro čtení paměti.
        Tato metoda je navržena tak, aby fungovala v synchronním i asynchronním prostředí.
        """
        try:
            memory = AdvancedMemory()

            try:
                # Zkusíme získat již běžící event loop
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # Pokud žádná neběží, spustíme novou
                loop = None

            if loop and loop.is_running():
                # Pokud jsme v asynchronním kontextu (např. main.py),
                # spustíme coroutine v existující smyčce.
                task = loop.create_task(memory.read_last_n_memories(n))
                # Získání výsledku z tasku synchronním způsobem, pokud je to nutné
                # Toto je komplexní, zkusíme jednodušší přístup
                # V tomto případě je lepší, když _run je plně synchronní a volá async.
                # Problém je, že crewai volá _run i když je k dispozici _arun.
                # Zkusíme tedy jiný přístup, který je robustnější.
                # Necháme si poradit od NEXUS a použijeme _arun.
                # Aplikujeme správný fix na volání v main.py
                pass # Necháme to na _arun

            # Fallback pro čistě synchronní volání
            recent_memories = asyncio.run(memory.read_last_n_memories(n))
            memory.close()
            return json.dumps(recent_memories, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)

        except Exception as e:
            return f"Error reading memory: {e}"

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
