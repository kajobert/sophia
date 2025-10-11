import os
import asyncio
import uuid
import json
import re

from core.prompt_builder import PromptBuilder
from core.rich_printer import RichPrinter
from core.memory_manager import MemoryManager
from core.llm_manager import LLMManager
from core.orchestrator import WorkerOrchestrator
from tui.messages import ChatMessage
from mcp_servers.worker.planning_server import PlanningServer
from mcp_servers.worker.reflection_server import ReflectionServer

class ConversationalManager:
    """
    Řídí konverzaci s uživatelem, rozhoduje o dalším kroku (informovat o stavu, nebo delegovat)
    a zajišťuje, aby uživatel dostal srozumitelnou odpověď.
    """
    def __init__(self, project_root: str = ".", status_widget=None, mission_manager=None):
        self.project_root = os.path.abspath(project_root)
        self.status_widget = status_widget
        self.mission_manager = mission_manager
        self.llm_manager = LLMManager(project_root=self.project_root)
        self.memory_manager = MemoryManager()
        self.worker = WorkerOrchestrator(project_root=self.project_root, status_widget=status_widget)
        self.planning_server = PlanningServer(project_root=self.project_root)
        self.reflection_server = ReflectionServer(project_root=self.project_root)
        self.session_id = str(uuid.uuid4())
        self.history = []
        self.state = "IDLE"
        self.pending_tool_call = None
        self.original_task_for_worker = None
        self.current_budget = None

        self.prompt_builder = PromptBuilder(
            system_prompt_path=os.path.join(self.project_root, "prompts/manager_prompt.txt"),
            ltm=None, # Manažer nepoužívá dlouhodobou paměť
            short_term_limit=10,
            long_term_retrieval_limit=0
        )
        RichPrinter.info("ConversationalManager initialized.")

    async def initialize(self):
        """Inicializuje podřízeného Workera."""
        await self.worker.initialize()
        RichPrinter.info("ConversationalManager a Worker jsou připraveni.")

    async def shutdown(self):
        """Bezpečně ukončí podřízeného Workera."""
        await self.worker.shutdown()
        self.memory_manager.close()
        RichPrinter.info("Všechny služby manažera a workera byly bezpečně ukončeny.")

    # --- Interní nástroje Manažera ---

    async def _delegate_task_to_worker(self, task: str, budget: int) -> dict:
        """
        Deleguje úkol na WorkerOrchestrator a čeká na výsledek.
        """
        RichPrinter.info(f"Manažer deleguje úkol na Workera: '{task}' (Budget: {budget})")
        result = await self.worker.run(initial_task=task, session_id=self.session_id, budget=budget)
        return result

    async def _get_task_directives(self, task: str) -> dict:
        """
        Analyzuje úkol pomocí specializovaného promptu a vrací jeho typ a navržený budget.
        """
        RichPrinter.info("Získávám direktivy pro úkol (triage & budget)...")
        try:
            with open(os.path.join(self.project_root, "prompts/triage_and_budget_prompt.txt"), "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            RichPrinter.error("Prompt pro triage a budget nebyl nalezen. Používám výchozí hodnoty.")
            return {"type": "complex", "budget": 8} # Fallback

        prompt = prompt_template.format(task=task)
        model = self.llm_manager.get_llm("default") # Použijeme rychlý model pro tento úkol

        response_text, _ = await model.generate_content_async(prompt, response_format={"type": "json_object"})

        try:
            # Očištění a parsování JSONu
            match = re.search(r"```(json)?\s*\n(.*?)\n```", response_text, re.DOTALL)
            if match:
                json_str = match.group(2).strip()
            else:
                json_str = response_text.strip()

            directives = json.loads(json_str)

            # Validace
            if "type" in directives and "budget" in directives:
                RichPrinter.log_communication("Direktivy pro úkol", directives, style="bold blue")
                return directives
            else:
                RichPrinter.warning("Chybějící klíče v direktivách. Používám fallback.")
                return {"type": "complex", "budget": 8}

        except json.JSONDecodeError:
            RichPrinter.log_error_panel("Selhání parsování JSON z triage promptu", response_text)
            return {"type": "complex", "budget": 8} # Fallback

    # --- Pomocné metody ---

    def _get_tool_descriptions(self) -> str:
        """Generuje popisy interních nástrojů pro vložení do promptu."""
        descriptions = [
            f"- `delegate_task_to_worker(task: str)`: Deleguje jakýkoliv úkol na Workera. Toto je tvůj jediný nástroj."
        ]
        return "\n".join(descriptions)

    def _parse_llm_response(self, response_text: str) -> tuple[str, dict | None]:
        """Parsování odpovědi od LLM, shodné s Workerem."""
        cleaned_text = response_text.strip()
        match = re.search(r"```(json)?\s*\n(.*?)\n```", cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(2).strip()
        try:
            parsed_response = json.loads(cleaned_text)
            return parsed_response.get("explanation", "").strip(), parsed_response.get("tool_call")
        except json.JSONDecodeError as e:
            RichPrinter.log_error_panel("Selhání parsování JSON odpovědi (Manažer)", cleaned_text, exception=e)
            return f"[SYSTÉM]: CHYBA PARSOVÁNÍ JSON.", None

    def _reset_state(self):
        """Resets the manager's state after a delegation flow is complete."""
        self.state = "IDLE"
        self.pending_tool_call = None
        self.original_task_for_worker = None
        self.current_budget = None
        RichPrinter.info("Stav manažera byl resetován na IDLE.")

    async def _generate_final_response(self, context: str, touched_files: list[str] | None = None) -> str:
        """
        Po získání výsledku nástroje zavolá LLM podruhé, aby vygeneroval
        srozumitelnou a informativní odpověď pro uživatele.
        """
        RichPrinter.info("Manažer formuluje finální odpověď pro uživatele...")

        prompt_parts = [
            "Na základě následujícího kontextu napiš krátkou, přátelskou a informativní odpověď pro uživatele v češtině.",
            f"Kontext: {context}"
        ]

        if touched_files:
            files_str = "\n".join(f"- `{f}`" for f in touched_files)
            prompt_parts.append(
                "\nBěhem operace byly upraveny nebo vytvořeny následující soubory. "
                "Explicitně je zmiň v odpovědi jako seznam, aby uživatel věděl, co se změnilo:\n"
                f"{files_str}"
            )

        prompt = "\n\n".join(prompt_parts)
        model = self.llm_manager.get_llm("default")
        final_response, _ = await model.generate_content_async(prompt)
        return final_response

    # --- Hlavní smyčka ---

    async def handle_user_input(self, user_input: str):
        """
        Handles user input by adopting an agile project management workflow.
        It breaks down complex tasks, delegates them as sub-tasks to the worker,
        and manages the overall project plan.
        """
        self.history.append(("", f"UŽIVATELSKÝ VSTUP: {user_input}"))
        task_directives = await self._get_task_directives(user_input)
        task_type = task_directives.get("type", "complex")
        budget = task_directives.get("budget", 8)

        if task_type == "simple":
            RichPrinter._post(ChatMessage("Tento úkol se zdá být jednoduchý, řeším ho přímo...", owner='agent', msg_type='inform'))
            # Simple tasks are delegated directly as before
            worker_result = await self._delegate_task_to_worker(user_input, budget)
            final_response = await self._generate_final_response(
                f"Jednoduchý úkol byl dokončen se shrnutím: {worker_result.get('summary')}",
                worker_result.get("touched_files", [])
            )
            RichPrinter._post(ChatMessage(final_response, owner='agent', msg_type='inform'))
            return

        # --- Agile Project Management Loop for Complex Tasks ---
        RichPrinter._post(ChatMessage("Rozumím, tento úkol je komplexní. Vytvářím projektový plán...", owner='agent', msg_type='inform'))

        # 1. Create the main task
        self.planning_server.update_task_description(user_input)
        self.planning_server.add_subtask(description=f"Pochopit a naplánovat kroky pro: '{user_input}'", priority=1)

        total_touched_files = set()
        project_history = []

        # 2. Execution Loop
        while True:
            next_task = self.planning_server.get_next_executable_task()
            if not next_task:
                RichPrinter.info("Všechny dílčí úkoly byly dokončeny. Projekt je hotov.")
                break

            task_id = next_task['id']
            task_desc = next_task['description']
            project_history.append(f"ZAHÁJEN DÍLČÍ ÚKOL: {task_desc}")
            RichPrinter._post(ChatMessage(f"Pracuji na dalším kroku: {task_desc}", owner='agent', msg_type='inform'))

            # 3. Delegate sub-task to Worker
            worker_result = await self._delegate_task_to_worker(task_desc, budget)
            project_history.append(f"VÝSLEDEK WORKERA: {worker_result.get('summary', 'Bez shrnutí.')}")

            # 4. Process Worker's result
            if worker_result.get("status") == "completed":
                RichPrinter.info(f"Dílčí úkol '{task_desc}' dokončen úspěšně.")
                self.planning_server.mark_task_as_completed(task_id)
                touched_files = worker_result.get("touched_files", [])
                if touched_files:
                    total_touched_files.update(touched_files)
                    RichPrinter._post(ChatMessage(f"Soubory ovlivněné tímto krokem: {', '.join(touched_files)}", owner='agent', msg_type='info'))

            elif worker_result.get("status") == "error" or worker_result.get("status") == "budget_exceeded":
                error_summary = worker_result.get('summary', 'Neznámá chyba.')
                RichPrinter.error(f"Chyba při provádění dílčího úkolu '{task_desc}': {error_summary}")
                project_history.append(f"CHYBA: {error_summary}")

                # 5. Error Handling & Reflection
                RichPrinter._post(ChatMessage("Narazil jsem na problém. Provádím sebereflexi, abych našel řešení...", owner='agent', msg_type='inform'))

                # Use the worker's history for reflection
                worker_history_for_reflection = worker_result.get("history", [])
                reflection = await self.reflection_server.reflect_on_recent_steps(worker_history_for_reflection, task_desc)

                RichPrinter._post(ChatMessage(f"**Výsledek sebereflexe:**\n{reflection}", owner='agent', msg_type='warning'))
                project_history.append(f"REFLEXE: {reflection}")

                # For now, we stop and report to the user.
                final_response = await self._generate_final_response(
                    f"Při práci na úkolu '{task_desc}' došlo k chybě: {error_summary}. "
                    f"Po analýze jsem dospěl k tomuto závěru: {reflection}. "
                    "Prosím, poskytněte mi další instrukce, jak mám pokračovat.",
                    list(total_touched_files)
                )
                RichPrinter._post(ChatMessage(final_response, owner='agent', msg_type='ask'))
                return # Stop the loop and wait for user feedback

            # Optional: Add a small delay to make the process observable
            await asyncio.sleep(1)

        # 6. Final summary after loop completion
        final_summary = (
            "Všechny kroky projektu byly úspěšně dokončeny. "
            f"Celkový cíl '{self.planning_server.get_main_goal()}' byl splněn."
        )
        final_response = await self._generate_final_response(final_summary, list(total_touched_files))
        RichPrinter._post(ChatMessage(final_response, owner='agent', msg_type='inform'))

        # Run final reflection on the whole project
        await self._run_reflection(project_history)


    async def _run_reflection(self, project_history: list):
        """
        Spustí proces sebereflexe na základě historie projektu.
        Vygeneruje "poučení" a uloží ho do dlouhodobé paměti.
        """
        RichPrinter.info("Spouštím sebereflexi na základě dokončeného projektu...")

        # 1. Připrav prompt
        try:
            with open(os.path.join(self.project_root, "prompts/reflection_prompt.txt"), "r", encoding="utf-8") as f:
                reflection_prompt_template = f.read()
        except FileNotFoundError:
            RichPrinter.error("Prompt pro sebereflexi nebyl nalezen. Přeskakuji.")
            return

        history_str = "\n".join(project_history)
        prompt = reflection_prompt_template.format(task_history=history_str)

        # 2. Zavolej LLM
        model = self.llm_manager.get_llm("default")
        learning, _ = await model.generate_content_async(prompt)
        learning = learning.strip()

        if not learning or len(learning) < 10:
            RichPrinter.warning("Vytvořený poznatek je příliš krátký, ignoruji.")
            return

        # 3. Ulož poznatek do LTM
        self.worker.ltm.add(
            documents=[learning],
            metadatas=[{"type": "learning", "source": "project_reflection"}],
            ids=[str(uuid.uuid4())]
        )
        RichPrinter.log_communication("Nový poznatek z projektu uložen do LTM", learning, style="bold green")