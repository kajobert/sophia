import sys
import os
import asyncio

# Přidání cesty k projektu, aby bylo možné importovat moduly z `core`
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Header, Footer, Input, TabbedContent, TabPane, RichLog
from textual.worker import Worker
from rich.panel import Panel
from rich.syntax import Syntax

from core.orchestrator import JulesOrchestrator
from core.rich_printer import RichPrinter
from tui.widgets.status_widget import StatusWidget
from tui.messages import LogMessage, ChatMessage

class SophiaTUI(App):
    """Moderní TUI pro interakci s agentem Jules s podporou záložek."""

    TITLE = "Jules - AI Software Engineer"
    SUB_TITLE = "Powered by Sophia Protocol"

    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Přepnout tmavý režim"),
        ("ctrl+q", "request_quit", "Ukončit"),
    ]

    def __init__(self):
        super().__init__()
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        # Nové widgety pro rozdělené zobrazení
        self.explanation_widget = RichLog(id="explanation", highlight=True, markup=True)
        self.explanation_widget.border_title = "Myšlenkový pochod"

        self.tool_widget = RichLog(id="tool_output", highlight=True, markup=True)
        self.tool_widget.border_title = "Výstup nástrojů"

        self.log_widget = StatusWidget(id="log_view") # Přejmenovaný StatusWidget
        self.log_widget.border_title = "Systémové logy"

        self.orchestrator = JulesOrchestrator(project_root=self.project_root)
        self.input_widget = Input(placeholder="Zadejte svůj úkol nebo zprávu...")
        self.session_id = None

    def compose(self) -> ComposeResult:
        """Sestaví layout TUI pomocí záložek."""
        yield Header()
        with TabbedContent(initial="agent_tab"):
            with TabPane("Agent", id="agent_tab"):
                yield Container(
                    self.explanation_widget,
                    self.tool_widget,
                    id="agent-view-container"
                )
            with TabPane("Logy", id="log_tab"):
                yield self.log_widget
        yield self.input_widget
        yield Footer()

    async def on_mount(self) -> None:
        """Spustí se po připojení widgetů."""
        RichPrinter.set_message_poster(self.post_message)
        self.initialize_orchestrator()
        self.input_widget.focus()

    @work(exclusive=True)
    async def initialize_orchestrator(self):
        """Inicializuje orchestrátor v samostatném workeru."""
        RichPrinter.info("Inicializace jádra agenta...")
        await self.orchestrator.initialize()
        try:
            if self.orchestrator.llm_manager.get_llm():
                RichPrinter.info("Jádro agenta připraveno.")
            else:
                RichPrinter.error("LLM manažer nevrátil model, ale nevyvolal výjimku. Agent je v offline režimu.")
        except Exception as e:
            RichPrinter.error(f"Nepodařilo se inicializovat LLM: {e}. Agent je v offline režimu.")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """Zpracuje odeslání vstupu od uživatele."""
        prompt = message.value
        if not prompt:
            return

        # Zobrazíme zprávu uživatele v dolním panelu
        user_panel = Panel(f"{prompt}", title="Uživatel", border_style="green")
        self.tool_widget.write(user_panel)
        self.input_widget.clear()

        # Vyčistíme myšlenkový pochod pro nový úkol
        self.explanation_widget.clear()

        self.run_orchestrator_task(prompt)

    @work(exclusive=True)
    async def run_orchestrator_task(self, prompt: str):
        """Spustí `orchestrator.run` v samostatném workeru, aby neblokoval UI."""
        await self.orchestrator.run(prompt, session_id=self.session_id)
        if self.session_id is None and hasattr(self.orchestrator, 'session_id'):
             self.session_id = self.orchestrator.session_id

    def on_log_message(self, message: LogMessage) -> None:
        """Zpracuje logovací zprávu a zobrazí ji v záložce Logy."""
        self.log_widget.add_log(message.text, message.level)

    def on_chat_message(self, message: ChatMessage) -> None:
        """Zpracuje zprávu pro agenta a zobrazí ji ve správném widgetu."""
        msg_type = message.msg_type
        content = message.content

        if msg_type == "explanation_chunk":
            self.explanation_widget.write(content)
        elif msg_type == "explanation_end":
            # Můžeme přidat nějaký vizuální oddělovač, pokud bude třeba
            pass
        elif msg_type == "tool_code":
            panel_content = Syntax(content, "json", theme="monokai", line_numbers=True)
            title = "Volání nástroje"
            self.tool_widget.write(Panel(panel_content, title=title, border_style="yellow"))
        elif msg_type == "tool_output":
            panel_content = content
            title = "Výstup nástroje"
            self.tool_widget.write(Panel(panel_content, title=title, border_style="cyan"))
        elif msg_type == "task_complete":
            panel_content = content
            title = "Úkol Dokončen"
            self.tool_widget.write(Panel(panel_content, title=title, border_style="bold green"))
        else: # Zprávy, které nepasují, půjdou do logu
            self.log_widget.add_log(f"Neznámý typ zprávy '{msg_type}': {content}", "WARNING")

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