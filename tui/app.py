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
from textual.widgets import Header, Footer, TabbedContent, TabPane, RichLog, Static, TextArea
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.table import Table

from core.conversational_manager import ConversationalManager
from core.rich_printer import RichPrinter
from tui.widgets.status_widget import StatusWidget
from tui.widgets.memory_log_widget import MemoryLogWidget
from tui.widgets.prompt_lab_widget import PromptLabWidget
from tui.messages import LogMessage, ChatMessage

CRASH_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "crash.log")

class SophiaTUI(App):
    """Moderní TUI pro interakci s agentem Jules s podporou záložek."""

    TITLE = "Jules - AI Software Engineer"
    SUB_TITLE = "Powered by Sophia Protocol (Manager/Worker Architektura)"

    BINDINGS = [
        ("ctrl+d", "toggle_dark", "Přepnout tmavý režim"),
        ("ctrl+q", "request_quit", "Ukončit"),
        ("enter", "submit_prompt", "Odeslat prompt"),
    ]

    def __init__(self):
        super().__init__()
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.explanation_widget = Static(id="explanation", markup=True)
        self.current_explanation = ""
        self.tool_widget = RichLog(id="tool_output", highlight=True, markup=True)
        self.tool_widget.border_title = "Výstup nástrojů"

        self.system_log_widget = StatusWidget(id="system_log_view")
        self.system_log_widget.border_title = "Systémové Logy"

        self.communication_log_widget = RichLog(id="communication_log_view", highlight=True, markup=True)
        self.communication_log_widget.border_title = "Záznam Komunikace"

        self.error_log_widget = RichLog(id="error_log_view", highlight=True, markup=True)
        self.error_log_widget.border_title = "Záznam Chyb"

        self.memory_log_widget = MemoryLogWidget(id="memory_log_view")

        # Nahrazení Orchestratoru za ConversationalManager
        self.manager = ConversationalManager(project_root=self.project_root)
        self.input_widget = TextArea(theme="monokai")
        self.session_id = None # Session ID se nyní spravuje v manažerovi

    def compose(self) -> ComposeResult:
        """Sestaví layout TUI."""
        yield Header()
        with TabbedContent(initial="agent_tab"):
            with TabPane("Agent", id="agent_tab"):
                with VerticalScroll(id="explanation-container"):
                    yield self.explanation_widget
                yield self.tool_widget
            with TabPane("Komunikace", id="communication_tab"):
                yield self.communication_log_widget
            with TabPane("Systémové logy", id="system_log_tab"):
                yield self.system_log_widget
            with TabPane("Paměť", id="memory_tab"):
                yield self.memory_log_widget
            with TabPane("Prompt Lab", id="prompt_lab_tab"):
                yield PromptLabWidget(manager=self.manager)
            with TabPane("Chyby", id="error_log_tab"):
                yield self.error_log_widget
        yield self.input_widget
        yield Footer()

    async def on_mount(self) -> None:
        """Spustí se po připojení widgetů a zkontroluje pád aplikace."""
        RichPrinter.set_message_poster(self.post_message)
        self.initialize_manager() # Přejmenováno z initialize_orchestrator
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

            recovery_prompt = textwrap.dedent(f"""
                **KRITICKÉ UPOZORNĚNÍ: Během předchozího spuštění došlo k pádu aplikace.**
                Tvým hlavním a jediným úkolem je analyzovat následující chybový protokol, diagnostikovat hlavní příčinu a implementovat opravu.
                --- ZÁZNAM O SELHÁNÍ ---
                {crash_content}
                --- KONEC ZÁZNAMU O SELHÁNÍ ---
                **POSTUP OPRAVY:**
                1. Analyzuj chybu a navrhni plán opravy.
                2. Implementuj opravu.
                3. Ověř, že oprava funguje.
                **DŮLEŽITÝ KROK PO OVĚŘENÍ OPRAVY:**
                Jakmile je oprava ověřena, **musíš** trvale uložit nový funkční stav. Použij k tomu následující nástroje v tomto pořadí:
                1. `create_git_commit` - Vytvoř commit s popisem provedené opravy.
                2. `promote_commit_to_last_known_good` - Z výstupu předchozího kroku získej hash nového commitu a použij tento nástroj.
                Tento druhý krok je klíčový pro evoluci a stabilitu systému. Začni s analýzou.
            """).strip()

            recovery_panel = Panel(Markdown(recovery_prompt), title="Automatická Oprava", border_style="bold red")
            self.tool_widget.write(recovery_panel)
            self.run_manager_task(recovery_prompt) # Přejmenováno
        except Exception as e:
            RichPrinter.error(f"Nepodařilo se zpracovat crash log: {e}")

    @work(exclusive=True)
    async def initialize_manager(self): # Přejmenováno
        """Inicializuje manažer v samostatném workeru."""
        RichPrinter.info("Inicializace jádra agenta (Manažer)...")
        await self.manager.initialize()
        RichPrinter.info("Jádro agenta připraveno.")


    async def action_submit_prompt(self) -> None:
        """Zpracuje odeslání vstupu od uživatele."""
        prompt = self.input_widget.text
        if not prompt:
            return

        user_panel = Panel(f"{prompt}", title="Uživatel", border_style="green")
        self.tool_widget.write(user_panel)
        self.input_widget.clear()

        self.current_explanation = ""
        self.explanation_widget.update("")

        self.run_manager_task(prompt)

    @work(exclusive=True)
    async def run_manager_task(self, prompt: str): # Přejmenováno
        """Spustí `manager.handle_user_input` v samostatném workeru, aby neblokoval UI."""
        await self.manager.handle_user_input(prompt)

    def on_log_message(self, message: LogMessage) -> None:
        """Zpracuje logovací zprávu a zobrazí ji v záložce Systémové logy."""
        self.system_log_widget.add_log(message.text, message.level)

    def on_chat_message(self, message: ChatMessage) -> None:
        """Zpracuje zprávu pro agenta a zobrazí ji ve správném widgetu."""
        msg_type = message.msg_type
        content = message.content

        def write_to_tool_widget(panel_content, title, border_style):
            self.tool_widget.write(Panel(panel_content, title=title, border_style=border_style))

        if msg_type == "explanation_chunk":
            self.current_explanation += content
            md_panel = Panel(Markdown(self.current_explanation), border_style="blue", title="Myšlenkový pochod")
            self.explanation_widget.update(md_panel)
            self.query_one("#explanation-container", VerticalScroll).scroll_end(animate=False)
        elif msg_type == "explanation_end":
            self.query_one("#explanation-container", VerticalScroll).scroll_end(animate=True)
        elif msg_type == "tool_code":
            panel_content = Syntax(content, "json", theme="monokai", line_numbers=True)
            write_to_tool_widget(panel_content, "Volání nástroje", "yellow")
        elif msg_type == "tool_output":
            write_to_tool_widget(content, "Výstup nástroje", "bright_cyan")
        elif msg_type == "inform":
            write_to_tool_widget(content, "Informace pro uživatele", "bright_green")
        elif msg_type == "warn":
            write_to_tool_widget(content, "Varování pro uživatele", "bright_yellow")
        elif msg_type == "error":
            write_to_tool_widget(content, "Chyba pro uživatele", "bright_red")
        elif msg_type == "ask":
            write_to_tool_widget(content, "Otázka pro uživatele", "bright_magenta")
        elif msg_type == "code":
            code_content = content.get('code', '')
            lang = content.get('language', 'python')
            panel_content = Syntax(code_content, lang, theme="monokai", line_numbers=True)
            write_to_tool_widget(panel_content, f"Zobrazení kódu ({lang})", "blue")
        elif msg_type == "table":
            try:
                table = Table(title=content.get('title'), border_style="blue")
                headers = content.get('headers', [])
                rows = content.get('rows', [])
                for header in headers:
                    table.add_column(str(header), justify="left")
                for row in rows:
                    table.add_row(*[str(item) for item in row])
                self.tool_widget.write(table)
            except Exception as e:
                self.system_log_widget.add_log(f"Chyba při vykreslování tabulky: {e}", "ERROR")
        elif msg_type == "task_complete":
            write_to_tool_widget(content, "Úkol Dokončen", "bold green")
        elif msg_type == "user_input":
            self.system_log_widget.add_log(f"Přijat vstup od uživatele: {content}", "INFO")
        elif msg_type == "communication_log":
            self.communication_log_widget.write(content)
        elif msg_type == "error_log":
            self.error_log_widget.write(content)
        elif msg_type == "memory_log":
            op = content.get("operation")
            source = content.get("source")
            log_content = content.get("content")
            self.memory_log_widget.add_log(op, source, log_content)
        else:
            self.system_log_widget.add_log(f"Neznámý typ zprávy '{msg_type}': {content}", "WARNING")

    async def action_request_quit(self):
        """Bezpečně ukončí aplikaci."""
        RichPrinter.info("Zahajuji ukončování...")
        await self.manager.shutdown() # Přejmenováno
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