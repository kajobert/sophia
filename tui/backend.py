import asyncio
import subprocess
import sys
import os
from typing import Optional, Callable
from textual.app import App

# HACK: Přidání cesty k projektu, aby bylo možné importovat moduly z `core`, `memory` atd.
# V produkčním nasazení by se to řešilo instalací balíčku.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from memory.advanced_memory import AdvancedMemory

class SophiaController:
    """
    Spravuje běh `main.py` a komunikaci s ním.
    Je navržen tak, aby byl integrován s Textual aplikací.
    """
    def __init__(self, app: App):
        self.app = app
        self.process: Optional[asyncio.subprocess.Process] = None
        self.memory = AdvancedMemory()

    async def start_sophia_core(self):
        """Spustí main.py jako subprocess a začne číst jeho výstup."""
        if self.process and self.process.returncode is None:
            self.app.bell()
            return

        # Ujistíme se, že používáme python z aktuálního venv
        python_executable = sys.executable
        main_script_path = os.path.join(os.path.dirname(__file__), "..", "main.py")

        self.process = await asyncio.create_subprocess_exec(
            python_executable, main_script_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Spuštění čtení streamů jako background tasky
        asyncio.create_task(self._read_stream(self.process.stdout, self.app.on_log_message))
        asyncio.create_task(self._read_stream(self.process.stderr, self.app.on_log_message))

    async def stop_sophia_core(self):
        """Zastaví proces `main.py`."""
        if self.process and self.process.returncode is None:
            self.process.terminate()
            await self.process.wait()
            self.process = None
            self.app.on_log_message("[TUI]: Jádro Sophie bylo zastaveno.")
        else:
            self.app.bell()

    async def submit_task(self, prompt: str):
        """Odešle nový úkol do `AdvancedMemory`."""
        if not prompt:
            self.app.bell()
            return

        try:
            task_id = await self.memory.add_task(prompt)
            self.app.on_log_message(f"[TUI]: Úkol odeslán (ID: {task_id}): {prompt}")
        except Exception as e:
            self.app.on_log_message(f"[TUI]: Chyba při odesílání úkolu: {e}")

    async def get_task_updates(self) -> list:
        """Získá aktualizace o stavech úkolů."""
        try:
            # Oprava: Voláme správnou metodu pro získání úkolů.
            tasks = await self.memory.read_last_n_memories(n=100, mem_type="TASK")
            return tasks
        except Exception as e:
            self.app.on_log_message(f"[TUI]: Chyba při načítání úkolů: {e}")
            # Log the full traceback to the debug file for better diagnostics
            import logging
            logging.exception("Error getting task updates")
            return []

    async def _read_stream(self, stream: asyncio.StreamReader, on_message: Callable):
        """Asynchronně čte řádky ze streamu a posílá je do TUI."""
        while True:
            try:
                line = await stream.readline()
                if line:
                    on_message(line.decode().strip())
                else:
                    # Stream byl uzavřen
                    break
            except Exception:
                # Proces byl pravděpodobně ukončen
                break
