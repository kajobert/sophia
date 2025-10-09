import sys
import os
import asyncio
import textwrap
import traceback

# Přidání cesty k projektu, aby bylo možné importovat moduly z `core`
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, TabbedContent, TabPane, RichLog
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.table import Table

from core.orchestrator import JulesOrchestrator
from core.rich_printer import RichPrinter
from tui.widgets.status_widget import StatusWidget
from tui.widgets.memory_log_widget import MemoryLogWidget
from tui.messages import LogMessage, ChatMessage

CRASH_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "crash.log")

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

        # Sjednocený widget pro zobrazení veškeré aktivity agenta
        self.agent_display = RichLog(id="agent_display", highlight=True, markup=True)
        self.agent_display.border_title = "Konzole Agenta"
        self.current_explanation = ""

        # Ostatní logovací widgety pro záložky
        self.system_log_widget = StatusWidget(id="system_log_view")
        self.communication_log_widget = RichLog(id="communication_log_view", highlight=True, markup=True)
        self.error_log_widget = RichLog(id="error_log_view", highlight=True, markup=True)
        self.memory_log_widget = MemoryLogWidget(id="memory_log_view")

        self.orchestrator = JulesOrchestrator(project_root=self.project_root)
        self.input_widget = Input(placeholder="Zadejte svůj úkol nebo zprávu...")
        self.session_id = None

    def compose(self) -> ComposeResult:
        """Sestaví layout TUI."""
        yield Header()
        with TabbedContent(initial="agent_tab"):
            with TabPane("Agent", id="agent_tab"):
                yield self.agent_display
            with TabPane("Komunikace", id="communication_tab"):
                yield self.communication_log_widget
            with TabPane("Systémové logy", id="system_log_tab"):
                yield self.system_log_widget
            with TabPane("Paměť", id="memory_tab"):
                yield self.memory_log_widget
            with TabPane("Chyby", id="error_log_tab"):
                yield self.error_log_widget
        yield self.input_widget
        yield Footer()

    async def on_mount(self) -> None:
        """Spustí se po připojení widgetů."""
        RichPrinter.set_message_poster(self.post_message)
        self.initialize_orchestrator()
        self.input_widget.focus()
        await self.check_for_crash_and_start_recovery()

    async def check_for_crash_and_start_recovery(self):
        """Zkontroluje, zda existuje log o pádu, a pokud ano, spustí proces obnovy."""
        if not os.path.exists(CRASH_LOG_PATH):
            return
        try:
            with open(CRASH_LOG_PATH, "r", encoding="utf-8") as f:
                crash_content = f.read()
            os.remove(CRASH_LOG_PATH)
            RichPrinter.error("Detekován pád aplikace! Zahajuji proces autonomní opravy.")
            # ... (zbytek logiky pro obnovu zůstává stejný)
        except Exception as e:
            RichPrinter.error(f"Nepodařilo se zpracovat crash log: {e}")

    @work(exclusive=True)
    async def initialize_orchestrator(self):
        """Inicializuje orchestrátor v samostatném workeru."""
        RichPrinter.info("Inicializace jádra agenta...")
        await self.orchestrator.initialize()
        RichPrinter.info("Jádro agenta připraveno.")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """Zpracuje odeslání vstupu od uživatele."""
        prompt = message.value
        if not prompt:
            return

        # Zobrazíme vstup od uživatele v hlavní konzoli
        user_panel = Panel(f"{prompt}", title="Uživatel", border_style="green")
        self.agent_display.write(user_panel)

        self.input_widget.clear()
        self.current_explanation = "" # Vynulujeme pro nový myšlenkový pochod
        self.run_orchestrator_task(prompt)

    @work(exclusive=True)
    async def run_orchestrator_task(self, prompt: str):
        """Spustí `orchestrator.run` v samostatném workeru."""
        await self.orchestrator.run(prompt, session_id=self.session_id)
        if self.session_id is None and hasattr(self.orchestrator, 'session_id'):
             self.session_id = self.orchestrator.session_id

    def on_log_message(self, message: LogMessage) -> None:
        self.system_log_widget.add_log(message.text, message.level)

    def on_chat_message(self, message: ChatMessage) -> None:
        """Zpracuje zprávu od agenta a zobrazí ji ve sjednocené konzoli."""
        msg_type = message.msg_type
        content = message.content

        # Pomocná funkce pro zápis panelu
        def write_panel(panel_content, title, border_style):
            self.agent_display.write(Panel(panel_content, title=title, border_style=border_style))

        if msg_type == "explanation_chunk":
            # Sbíráme části myšlenkového pochodu
            self.current_explanation += content
        elif msg_type == "explanation_end":
            # Na konci streamu zobrazíme celý myšlenkový pochod
            if self.current_explanation:
                md = Markdown(self.current_explanation)
                write_panel(md, "Myšlenkový pochod", "blue")
            self.current_explanation = "" # Vynulujeme pro příští použití
        elif msg_type == "tool_code":
            panel_content = Syntax(content, "json", theme="monokai", line_numbers=True)
            write_panel(panel_content, "Volání nástroje", "yellow")
        elif msg_type == "tool_output":
            write_panel(content, "Výstup nástroje", "bright_cyan")
        elif msg_type in ("inform", "warn", "error", "ask", "task_complete"):
            style_map = {
                "inform": ("Informace", "bright_green"),
                "warn": ("Varování", "bright_yellow"),
                "error": ("Chyba", "bright_red"),
                "ask": ("Otázka", "bright_magenta"),
                "task_complete": ("Úkol Dokončen", "bold green"),
            }
            title, border_style = style_map[msg_type]
            write_panel(content, title, border_style)
        elif msg_type == "code":
            lang = content.get('language', 'python')
            panel_content = Syntax(content.get('code', ''), lang, theme="monokai", line_numbers=True)
            write_panel(panel_content, f"Zobrazení kódu ({lang})", "blue")
        elif msg_type == "table":
            try:
                table = Table(title=content.get('title'), border_style="blue")
                for header in content.get('headers', []): table.add_column(str(header))
                for row in content.get('rows', []): table.add_row(*[str(item) for item in row])
                self.agent_display.write(table)
            except Exception as e:
                self.system_log_widget.add_log(f"Chyba při vykreslování tabulky: {e}", "ERROR")
        elif msg_type in ("communication_log", "error_log", "memory_log"):
            # Tyto zprávy patří do svých vlastních záložek
            if msg_type == "communication_log": self.communication_log_widget.write(content)
            elif msg_type == "error_log": self.error_log_widget.write(content)
            elif msg_type == "memory_log": self.memory_log_widget.add_log(content.get("operation"), content.get("source"), content.get("content"))
        elif msg_type != "user_input": # user_input již zobrazujeme v on_input_submitted
            self.system_log_widget.add_log(f"Neznámý typ zprávy '{msg_type}'", "WARNING")

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
        os.makedirs(os.path.dirname(CRASH_LOG_PATH), exist_ok=True)
        with open(CRASH_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("--- APLIKACE TUI SPADLA S NEOČEKÁVANOU VÝJIMKOU ---\n\n")
            traceback.print_exc(file=f)
        print(f"\n[FATAL] TUI application crashed. See {CRASH_LOG_PATH} for details.", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)