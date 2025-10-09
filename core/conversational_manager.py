import asyncio
import sys
import os

# Přidání cesty k projektu pro správné rozlišení modulů
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from enum import Enum
from tui.messages import ChatMessage
from core.worker_orchestrator import WorkerOrchestrator
from core.rich_printer import RichPrinter

class ManagerState(Enum):
    LISTENING = "Čeká na vstup od uživatele"
    WAITING_FOR_WORKER = "Čeká na dokončení úkolu"
    PROCESSING = "Zpracovává vstup"

class ConversationalManager:
    """
    Vrstva 1: Hlavní komunikační rozhraní pro uživatele.
    Vede konverzaci, přijímá úkoly a deleguje je na WorkerOrchestrator.
    """
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.worker = WorkerOrchestrator(project_root=self.project_root)
        self.session_id = None
        self.state = ManagerState.LISTENING
        self.welcome_prompt_template = self._load_welcome_prompt()
        self.final_response_prompt_template = self._load_final_response_prompt()
        RichPrinter.info("Conversational Manager initialized.")

    def _set_state(self, new_state: ManagerState):
        """Nastaví nový stav a odešle zprávu pro aktualizaci TUI."""
        self.state = new_state
        RichPrinter.info(f"Manager state changed to: {new_state.name}")
        RichPrinter._post(ChatMessage(
            content={"source": "manager", "status": new_state.name, "details": new_state.value},
            owner="system",
            msg_type="status_update"
        ))

    async def initialize(self):
        """Inicializuje podřízeného workera, vygeneruje uvítací zprávu a nastaví výchozí stav."""
        RichPrinter.info("Initializing worker...")
        await self.worker.initialize()
        await self._generate_and_display_welcome_message()
        self._set_state(ManagerState.LISTENING)
        RichPrinter.info("Conversational Manager ready.")

    def _load_welcome_prompt(self) -> str:
        """Načte uvítací prompt ze souboru."""
        try:
            path = os.path.join(self.project_root, "prompts/welcome_prompt.txt")
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            RichPrinter.error("Welcome prompt not found. Using a default fallback.")
            return "Say hello and that you are ready."

    async def _generate_and_display_welcome_message(self):
        """Zkontroluje stav systému a vygeneruje uvítací zprávu pro uživatele."""
        RichPrinter.info("Generating welcome message...")
        error_log_path = os.path.join(self.project_root, "logs", "errors.log")
        error_log_status = "Žádné chyby v logu."
        try:
            if os.path.exists(error_log_path) and os.path.getsize(error_log_path) > 0:
                with open(error_log_path, "r", encoding="utf-8") as f:
                    # Načteme jen posledních pár řádků, abychom nepřetížili prompt
                    lines = f.readlines()
                    last_lines = "".join(lines[-10:])
                    error_log_status = f"Při posledním běhu byly zaznamenány chyby:\n---\n{last_lines}"
        except Exception as e:
            error_log_status = f"Nepodařilo se přečíst chybový log: {e}"

        # TODO: V budoucnu přidat informace o poslední session z paměti
        last_session_status = "Poslední sezení bylo úspěšně ukončeno."

        prompt = self.welcome_prompt_template.format(
            error_log_status=error_log_status,
            last_session_status=last_session_status
        )

        model = self.worker.llm_manager.get_llm("fast")
        welcome_message, _ = await model.generate_content_async(prompt)

        RichPrinter._post(ChatMessage(content=welcome_message, owner='agent', msg_type='inform'))


    def _load_final_response_prompt(self) -> str:
        """Načte prompt pro finální odpověď ze souboru."""
        try:
            path = os.path.join(self.project_root, "prompts/final_response_prompt.txt")
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            RichPrinter.error("Final response prompt not found. Using a default fallback.")
            return "Summarize the result for the user."

    async def run(self, user_input: str):
        """
        Přijme vstup, deleguje práci na workera a po dokončení vygeneruje finální odpověď.
        """
        if self.session_id is None and hasattr(self.worker, 'session_id'):
            self.session_id = self.worker.session_id

        self._set_state(ManagerState.PROCESSING)
        RichPrinter.info(f"ConversationalManager received task: '{user_input}'")
        RichPrinter._post(ChatMessage(content="Rozumím. Předávám úkol ke zpracování...", owner='agent', msg_type='inform'))

        self._set_state(ManagerState.WAITING_FOR_WORKER)
        worker_result = await self.worker.run(user_input, session_id=self.session_id)

        self._set_state(ManagerState.PROCESSING)

        # Sestavení promptu pro finální odpověď
        final_prompt = self.final_response_prompt_template.format(
            user_input=user_input,
            worker_summary=json.dumps(worker_result, indent=2, ensure_ascii=False)
        )

        model = self.worker.llm_manager.get_llm("fast")
        final_response, _ = await model.generate_content_async(final_prompt)

        RichPrinter._post(ChatMessage(content=final_response, owner='agent', msg_type='inform'))

        self._set_state(ManagerState.LISTENING)

    async def shutdown(self):
        """Bezpečně ukončí podřízeného workera."""
        await self.worker.shutdown()