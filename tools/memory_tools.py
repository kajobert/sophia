import threading
import asyncio
import json
from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool as LangchainBaseTool
from tools.base_tool import BaseTool
from memory.advanced_memory import AdvancedMemory
from core.utils import CustomJSONEncoder


def run_sync_or_async(coro):
    """
    Safely runs a coroutine from a sync context by creating a new event loop
    or using the existing one if in a different thread.
    """
    try:
        loop = asyncio.get_running_loop()
        if threading.current_thread() is threading.main_thread():
            raise RuntimeError(
                "Cannot call sync tool in a running async loop. Use the async version (`_arun`)."
            )
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    except RuntimeError:
        return asyncio.run(coro)


class MemoryReaderToolInput(BaseModel):
    """Pydantic model for MemoryReaderTool input."""

    n: int = Field(10, description="The number of recent memories to read.")
    mem_type: Optional[str] = Field(
        None,
        description="Optional memory type to filter by (e.g., 'TASK', 'CONVERSATION').",
    )


class MemoryReaderTool(LangchainBaseTool, BaseTool):
    name: str = "Memory Reader"
    description: str = (
        "Reads the N most recent entries from the memory. Can optionally filter by memory type "
        "to get specific types of memories, such as 'CONVERSATION' for past dialogues or 'TASK' for task outcomes."
    )
    args_schema: Type[BaseModel] = MemoryReaderToolInput

    def execute(self, **kwargs) -> str:
        return self._run(**kwargs)

    def _run(self, n: int = 10, mem_type: Optional[str] = None) -> str:
        """Synchronous execution of the tool."""
        try:
            memory = AdvancedMemory()
            # Use the helper to run the async method from a sync context
            recent_memories = run_sync_or_async(
                memory.read_last_n_memories(n=n, mem_type=mem_type)
            )
            memory.close()
            return json.dumps(
                recent_memories, indent=2, ensure_ascii=False, cls=CustomJSONEncoder
            )
        except Exception as e:
            return f"Error reading memory: {e}"

    async def _arun(self, n: int = 10, mem_type: Optional[str] = None) -> str:
        """Asynchronous execution of the tool."""
        try:
            memory = AdvancedMemory()
            recent_memories = await memory.read_last_n_memories(n=n, mem_type=mem_type)
            memory.close()
            return json.dumps(
                recent_memories, indent=2, ensure_ascii=False, cls=CustomJSONEncoder
            )
        except Exception as e:
            return f"Error reading memory: {e}"
