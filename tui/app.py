import sys
import os

# HACK: Přidání cesty k projektu
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Input

from tui.backend import SophiaController
from tui.widgets.log_viewer import LogViewer
from tui.widgets.task_manager import TaskManager


class SophiaTUI(App):
    """Interaktivní terminálová aplikace pro Sophii."""

    TITLE = "Sophia TUI"
    SUB_TITLE = "Interaktivní klient pro jádro umělé mysli"

    BINDINGS = [
        ("ctrl+s", "start_core", "Start jádro"),
        ("ctrl+x", "stop_core", "Stop jádro"),
        ("ctrl+d", "toggle_dark", "Přepnout tmavý režim"),
        ("ctrl+q", "quit", "Ukončit"),
    ]

    def __init__(self):
        super().__init__()
        self.controller = SophiaController(self)
        self.log_viewer = LogViewer()
        self.task_manager = TaskManager()

    def compose(self) -> ComposeResult:
        """Vytvoří a uspořádá widgety."""
        yield Header()
        with Container():
            yield self.task_manager
            yield self.log_viewer
        yield Footer()

    async def on_mount(self) -> None:
        """Spustí se po připojení widgetů."""
        # Automaticky spustíme jádro při startu TUI
        await self.run_action("start_core")
        # Nastavíme periodickou aktualizaci seznamu úkolů
        self.set_interval(5, self.update_task_table)

    async def update_task_table(self) -> None:
        """Aktualizuje tabulku s úkoly."""
        tasks = await self.controller.get_task_updates()
        self.task_manager.update_tasks(tasks)

    # --- Action Handlers ---

    async def action_start_core(self) -> None:
        """Spustí jádro Sophie."""
        self.on_log_message("[TUI]: Pokouším se spustit jádro Sophie...")
        await self.controller.start_sophia_core()

    async def action_stop_core(self) -> None:
        """Zastaví jádro Sophie."""
        self.on_log_message("[TUI]: Zastavuji jádro Sophie...")
        await self.controller.stop_sophia_core()

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """Zpracuje odeslání nového úkolu z inputu."""
        prompt = message.value
        input_widget = self.query_one(Input)
        input_widget.clear()

        await self.controller.submit_task(prompt)
        # Ihned aktualizujeme tabulku, aby se zobrazil nový úkol
        await self.update_task_table()

    # --- Message Handlers ---

    def on_log_message(self, message: str) -> None:
        """Zpracuje novou zprávu do logu."""
        self.log_viewer.add_log_message(message)


if __name__ == "__main__":
    import logging

    # Nastavení logování do souboru pro ladění
    logging.basicConfig(
        level=logging.DEBUG,
        filename="tui_debug.log",
        filemode="w",
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    app = SophiaTUI()
    app.run()
