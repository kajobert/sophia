# /tools/memory_tools.py
"""
Nástroje pro interakci s pamětí Sophie.
"""
from langchain_core.tools import BaseTool
from memory.episodic_memory import EpisodicMemory
from typing import Type
from pydantic import BaseModel, Field
import json
from core.utils import CustomJSONEncoder

class EpisodicMemoryReaderToolInput(BaseModel):
    """Pydantic model for EpisodicMemoryReaderTool input."""
    n: int = Field(10, description="The number of recent memories to read.")

class EpisodicMemoryReaderTool(BaseTool):
    """
    Nástroj pro čtení posledních N záznamů z epizodické paměti.
    """
    name: str = "Episodic Memory Reader"
    description: str = "Reads the N most recent entries from the episodic memory. Use it to understand what happened recently."
    args_schema: Type[BaseModel] = EpisodicMemoryReaderToolInput

    def _run(self, n: int = 10) -> str:
        """
        Spustí nástroj pro čtení paměti.
        """
        try:
            memory = EpisodicMemory()
            recent_memories = memory.read_last_n_memories(n)
            memory.close()
            # Převedeme seznam slovníků na JSON string pro čistší výstup
            return json.dumps(recent_memories, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
        except Exception as e:
            return f"Error reading episodic memory: {e}"
