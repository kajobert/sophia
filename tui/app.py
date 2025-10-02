import sys
import os
import asyncio
import textwrap
import traceback

# Přidání cesty k projektu, aby bylo možné importovat moduly z `core`
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Vertical, Container, VerticalScroll
from textual.widgets import Header, Footer, Input, TabbedContent, TabPane, RichLog, Static
from textual.worker import Worker
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

from core.orchestrator import JulesOrchestrator
from core.rich_printer import RichPrinter
from tui.widgets.status_widget import StatusWidget
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
        self.explanation_widget = Static(id="explanation", markup=True)
        self.current_explanation = ""
        self.tool_widget = RichLog(id="tool_output", highlight=True, markup=True)
        self.tool_widget.border_title = "Výstup nástrojů"
        self.log_widget = StatusWidget(id="log_view")
        self.log_widget.border_title = "Systémové logy"
        self.orchestrator = JulesOrchestrator(project_root=self.project_root)
        self.input_widget = Input(placeholder="Zadejte svůj úkol nebo zprávu...")
        self.session_id = None

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

    def on_exception(self, exception: Exception) -> None:
        """
        Zpracuje neočekávané chyby, zapíše je do crash.log a ukončí aplikaci
        s nenulovým kódem, aby to Guardian detekoval.
        """
        os.makedirs(os.path.dirname(CRASH_LOG_PATH), exist_ok=True)
        with open(CRASH_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("--- APLIKACE TUI SPADLA S NEOČEKÁVANOU VÝJIMKOU ---\n\n")
            traceback.print_exc(file=f)
        
        # Ukončíme aplikaci s chybovým kódem
        self.exit(1, f"FATAL: Unhandled exception occurred. See {CRASH_LOG_PATH} for details.")


    async def on_mount(self) -> None:
        """Spustí se po připojení widgetů a zkontroluje pád aplikace."""
        
        # ---> PONECH PRO TEST SEBEOPRAVY <---
        raise RuntimeError("Toto je simulovaný pád pro test sebeopravného mechanismu!")
        # ---> KONEC TESTOVACÍHO ŘÁDKU <---

        RichPrinter.set_message_poster(self.post_message)
        self.initialize_orchestrator()
        self.input_widget.focus()
        await self.check_for_crash_and_start_recovery()

    # ... (zbytek metod třídy zůstává stejný) ...
    # ... on_chat_message, action_request_quit, atd. ...
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
            self.run_orchestrator_task(recovery_prompt)
        except Exception as e:
            RichPrinter.error(f"Nepodařilo se zpracovat crash log: {e}")

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
        except Exception as e