import sys
import os
import asyncio

# Přidání cesty k projektu, aby bylo možné importovat moduly z `core`
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer, Input
from textual.worker import Worker

from core.orchestrator import JulesOrchestrator
from core.rich_printer import RichPrinter
from tui.widgets.chat_widget import ChatWidget
from tui.widgets.status_widget import StatusWidget
from tui.messages import LogMessage, ChatMessage

class SophiaTUI(App):
    """Moderní TUI pro interakci s agentem Jules."""

    TITLE = "Jules - AI Software Engineer"
    SUB_TITLE = "Powered by Sophia Protocol"

    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Přepnout tmavý režim"),
        ("ctrl+q", "request_quit", "Ukončit"),
    ]

    def __init__(self):
        super().__init__()
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.orchestrator = JulesOrchestrator(project_root=self.project_root)
        self.chat_widget = ChatWidget(id="chat")
        self.status_widget = StatusWidget(id="status")
        self.input_widget = Input(placeholder="Zadejte svůj úkol nebo zprávu...")
        self.session_id = None # Bude nastaveno po inicializaci

    def compose(self) -> ComposeResult:
        """Sestaví layout TUI."""
        yield Header()
        yield VerticalScroll(self.chat_widget, id="chat-container")
        yield self.status_widget
        yield self.input_widget
        yield Footer()

    async def on_mount(self) -> None:
        """Spustí se po připojení widgetů."""
        # Propojení RichPrinteru s TUI
        RichPrinter.set_message_poster(self.post_message)

        # Spuštění inicializace orchestrátoru na pozadí
        self.initialize_orchestrator()
        self.input_widget.focus()

    @work(exclusive=True)
    async def initialize_orchestrator(self):
        """Inicializuje orchestrátor v samostatném workeru."""
        RichPrinter.info("Inicializace jádra agenta...")
        await self.orchestrator.initialize()
        if self.orchestrator.model:
            RichPrinter.info("Jádro agenta připraveno.")
        else:
            RichPrinter.error("API klíč pro Gemini nebyl nalezen nebo je neplatný. Agent je v offline režimu.")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """Zpracuje odeslání vstupu od uživatele."""
        prompt = message.value
        if not prompt:
            return

        self.chat_widget.add_user_message(prompt)
        self.input_widget.clear()

        # Pokud je to první zpráva, session_id je None, orchestrátor vytvoří nové.
        # Pro další zprávy se session_id předá, aby se navázalo na konverzaci.
        self.run_orchestrator_task(prompt)

    @work(exclusive=True)
    async def run_orchestrator_task(self, prompt: str):
        """Spustí `orchestrator.run` v samostatném workeru, aby neblokoval UI."""
        # Předáme existující session_id, pokud už bylo vytvořeno
        await self.orchestrator.run(prompt, session_id=self.session_id)
        # Uložíme si session_id pro další volání
        if self.session_id is None and hasattr(self.orchestrator, 'session_id'):
             self.session_id = self.orchestrator.session_id


    def on_log_message(self, message: LogMessage) -> None:
        """Zpracuje logovací zprávu z RichPrinteru."""
        self.status_widget.add_log(message.text, message.level)

    def on_chat_message(self, message: ChatMessage) -> None:
        """Zpracuje chatovací zprávu z RichPrinteru."""
        if message.owner == 'agent':
            self.chat_widget.add_agent_message(message.content, message.msg_type)
        # Zprávy od uživatele se přidávají přímo v on_input_submitted

    async def action_request_quit(self):
        """Bezpečně ukončí aplikaci."""
        RichPrinter.info("Zahajuji ukončování...")
        await self.orchestrator.shutdown()
        self.exit()


if __name__ == "__main__":
    # Konfigurace logování do souboru pro ladění
    RichPrinter.configure_logging()

    app = SophiaTUI()
    app.run()