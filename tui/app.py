import sys
import os
import asyncio
import textwrap
import traceback

# Přidání cesty k projektu, aby bylo možné importovat moduly z `core`
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer, Input, TabbedContent, TabPane, RichLog, Static
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

from core.nomad_orchestrator_v2 import NomadOrchestratorV2
from core.state_manager import State
from core.rich_printer import RichPrinter
from tui.widgets.status_widget import StatusWidget
from tui.messages import LogMessage, ChatMessage

CRASH_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "crash.log")

class SophiaTUI(App):
    """Moderní TUI pro interakci s NomadOrchestratorV2."""

    TITLE = "Nomad - AI Software Engineer"
    SUB_TITLE = "Powered by Sophia/Nomad V2 Protocol"

    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Přepnout tmavý režim"),
        ("ctrl+q", "request_quit", "Ukončit"),
    ]

    def __init__(self):
        super().__init__()
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.explanation_widget = Static(id="explanation", markup=True)
        self.current_explanation = ""
        self.tool_widget = RichLog(id="tool_output", highlight=True, markup=True)
        self.tool_widget.border_title = "Výstup nástrojů"
        self.log_widget = StatusWidget(id="log_view")
        self.log_widget.border_title = "Systémové logy"
        self.orchestrator = NomadOrchestratorV2(project_root=self.project_root)
        self.input_widget = Input(placeholder="Zadejte svůj úkol nebo zprávu...")
        self.mission_running = False

    def compose(self) -> ComposeResult:
        """Sestaví layout TUI."""
        yield Header()
        with TabbedContent(initial="agent_tab"):
            with TabPane("Agent", id="agent_tab"):
                with VerticalScroll(id="explanation-container"):
                    yield self.explanation_widget
                yield self.tool_widget
            with TabPane("Logy", id="log_tab"):
                yield self.log_widget
        yield self.input_widget
        yield Footer()

    async def on_mount(self) -> None:
        """Spustí se po připojení widgetů a zkontroluje pád aplikace."""
        RichPrinter.set_message_poster(self.post_message)
        await self.initialize_orchestrator()
        self.input_widget.focus()
        # Note: Crash recovery je nyní handled v NomadOrchestratorV2 RecoveryManager

    async def initialize_orchestrator(self):
        """Inicializuje orchestrátor asynchronně."""
        RichPrinter.info("Inicializace NomadOrchestratorV2...")
        try:
            await self.orchestrator.initialize()
            RichPrinter.info("✅ Nomad připraven k použití!")
            RichPrinter.info(f"📊 Model: {self.orchestrator.llm_manager._gemini_adapter.model_name if self.orchestrator.llm_manager._gemini_adapter else 'OpenRouter'}")
        except Exception as e:
            RichPrinter.error(f"❌ Chyba při inicializaci: {e}")
            traceback.print_exc()
    
    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """Zpracuje odeslání vstupu od uživatele."""
        prompt = message.value
        if not prompt:
            return
    
        user_panel = Panel(f"{prompt}", title="Uživatel", border_style="green")
        self.tool_widget.write(user_panel)
        self.input_widget.clear()
    
        self.current_explanation = ""
        self.explanation_widget.update("")
    
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
            self.current_explanation += content
            md_panel = Panel(Markdown(self.current_explanation), border_style="blue", title="Myšlenkový pochod")
            self.explanation_widget.update(md_panel)
            self.query_one("#explanation-container", VerticalScroll).scroll_end(animate=False)
        elif msg_type == "explanation_end":
            self.query_one("#explanation-container", VerticalScroll).scroll_end(animate=True)
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
        else: 
            self.log_widget.add_log(f"Neznámý typ zprávy '{msg_type}': {content}", "WARNING")
    
    async def action_request_quit(self):
        """Bezpečně ukončí aplikaci."""
        RichPrinter.info("Zahajuji ukončování...")
        await self.orchestrator.shutdown()
        self.exit()


if __name__ == "__main__":
    RichPrinter.configure_logging()
    
    try:
        app = SophiaTUI()
        app.run()
    except Exception as e:
        # Zajistíme, že adresář pro logy existuje
        os.makedirs(os.path.dirname(CRASH_LOG_PATH), exist_ok=True)
        # Zapíšeme kompletní traceback do crash logu
        with open(CRASH_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("--- APLIKACE TUI SPADLA S NEOČEKÁVANOU VÝJIMKOU ---\n\n")
            traceback.print_exc(file=f)
        
        # Vytiskneme chybu i na standardní chybový výstup
        print(f"\n[FATAL] TUI application crashed. See {CRASH_LOG_PATH} for details.", file=sys.stderr)
        traceback.print_exc()
        
        # Ukončíme s nenulovým kódem, aby to Guardian detekoval
        sys.exit(1)