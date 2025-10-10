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

class ConversationalManager:
    """
    Řídí konverzaci s uživatelem, rozhoduje o dalším kroku (informovat o stavu, nebo delegovat)
    a zajišťuje, aby uživatel dostal srozumitelnou odpověď.
    """
    def __init__(self, project_root: str = ".", status_widget=None):
        self.project_root = os.path.abspath(project_root)
        self.status_widget = status_widget
        self.llm_manager = LLMManager(project_root=self.project_root)
        self.memory_manager = MemoryManager()
        self.worker = WorkerOrchestrator(project_root=self.project_root, status_widget=status_widget)
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
        Kompletní smyčka pro zpracování vstupu od uživatele.
        Rozhoduje o dalším kroku na základě stavu manažera.
        """
        # >>> HUMAN-IN-THE-LOOP: HANDLE USER'S APPROVAL/DENIAL <<<
        if self.state == "AWAITING_DELEGATION_APPROVAL":
            self.history.append(("", f"UŽIVATELSKÝ VSTUP (rozhodnutí o delegování): {user_input}"))
            normalized_input = user_input.lower().strip()

            if normalized_input in ["ano", "yes", "souhlasím"]:
                RichPrinter.info("Uživatel schválil delegování. Pokračuji v exekuci...")

                tool_call = self.pending_tool_call
                tool_name = tool_call.get("tool_name")
                args = tool_call.get("args", [])
                kwargs = tool_call.get("kwargs", {})

                RichPrinter._post(ChatMessage("Dobře, provádím schválené delegování...", owner='agent', msg_type='inform'))

                result = await self.worker.mcp_client.execute_tool(tool_name, args, kwargs)

                try:
                    result_data = json.loads(result)
                    if "error" in result_data:
                        RichPrinter.error(f"Při delegování došlo k chybě: {result_data['error']}")
                        tool_result_context = f"Pokus o delegování selhal s chybou: {result_data['error']}"
                    else:
                        tool_result_context = f"Delegování na Jules bylo úspěšně provedeno. Výsledek: {result}"
                except json.JSONDecodeError:
                    tool_result_context = f"Delegování na Jules bylo provedeno, ale odpověď nebyla ve formátu JSON: {result}"
            else: # User denied
                RichPrinter.warning("Uživatel zamítl delegování.")
                # Instruct the worker to find another solution
                new_task_for_worker = (
                    f"Původní úkol byl: '{self.original_task_for_worker}'.\n"
                    f"Váš návrh na delegování byl uživatelem zamítnut. "
                    f"Najděte prosím alternativní způsob, jak úkol vyřešit bez delegování."
                )
                RichPrinter._post(ChatMessage("Rozumím, delegování bylo zrušeno. Zkusím najít jiné řešení.", owner='agent', msg_type='inform'))
                # Použijeme uložený budget
                worker_result = await self._delegate_task_to_worker(new_task_for_worker, self.current_budget or 8)
                tool_result_context = f"Worker hledá alternativní řešení. Jeho odpověď: {worker_result.get('summary')}"

            # Reset state and generate final response
            self._reset_state()
            final_response = await self._generate_final_response(tool_result_context)
            RichPrinter._post(ChatMessage(final_response, owner='agent', msg_type='inform'))
            return

        # Krok 1: Triage a Budgeting (standardní průběh)
        self.history.append(("", f"UŽIVATELSKÝ VSTUP: {user_input}"))
        task_directives = await self._get_task_directives(user_input)
        task_type = task_directives.get("type", "complex")
        budget = task_directives.get("budget", 8)
        self.current_budget = budget # Uložíme budget pro případné pozdější použití

        # Krok 2: Rozhodnutí o nástroji na základě triage
        tool_descriptions = self._get_tool_descriptions()
        prompt = self.prompt_builder.build_prompt(tool_descriptions, self.history)
        model = self.llm_manager.get_llm("default")

        RichPrinter.info(f"Manažer přemýšlí... (model: {model.model_name})")
        response_text, _ = await model.generate_content_async(prompt, response_format={"type": "json_object"})

        explanation, tool_call_data = self._parse_llm_response(response_text)
        if explanation:
            RichPrinter.log_communication("Myšlenkový pochod Manažera", explanation, style="bold magenta")

        if not tool_call_data or "tool_name" not in tool_call_data:
            RichPrinter.warning("Manažer se rozhodl nepoužít nástroj.")
            final_response = await self._generate_final_response("Řekni uživateli, že na jeho požadavek nemůžeš reagovat, protože se zdá, že nevyžaduje žádnou akci.")
            RichPrinter._post(ChatMessage(final_response, owner='agent', msg_type='inform'))
            return

        # Krok 2: Spuštění nástroje
        tool_name = tool_call_data["tool_name"]
        kwargs = tool_call_data.get("kwargs", {})
        RichPrinter.log_communication("Manažer volá interní metodu", tool_call_data, style="bold yellow")

        tool_result_context = ""
        if tool_name == "get_worker_status":
            status_json = self._get_worker_status()
            RichPrinter.log_communication("Výsledek `_get_worker_status`", status_json, style="bold cyan")
            tool_result_context = f"Výsledek zjištění stavu workera je: {status_json}. Na základě toho informuj uživatele."
            self.history.append((explanation, status_json))
            final_response = await self._generate_final_response(tool_result_context)

        elif tool_name == "delegate_task_to_worker":
            task = kwargs.get("task", user_input)
            self.original_task_for_worker = task # Save for potential continuation
            RichPrinter._post(ChatMessage("Rozumím, předávám úkol ke zpracování svému Workerovi. Bude vás informovat o průběhu.", owner='agent', msg_type='inform'))
            # Použijeme dynamicky získaný budget
            worker_result = await self._delegate_task_to_worker(task, budget)

            # >>> HUMAN-IN-THE-LOOP: HANDLE DELEGATION APPROVAL <<<
            if worker_result.get("status") == "needs_delegation_approval":
                self.state = "AWAITING_DELEGATION_APPROVAL"
                self.pending_tool_call = worker_result.get("tool_call")
                self.history.append((explanation, json.dumps(worker_result)))

                # Získáme popis úkolu z argumentů volání
                tool_args = self.pending_tool_call.get('args', [])
                tool_kwargs = self.pending_tool_call.get('kwargs', {})
                # 'prompt' je první argument funkce delegate_task_to_jules
                delegation_task_desc = tool_kwargs.get('prompt') or (tool_args[0] if tool_args else 'Nespecifikovaný úkol.')

                question = (
                    f"Můj Worker navrhuje delegovat následující úkol na externího specializovaného agenta Jules:\n\n"
                    f"> {delegation_task_desc}\n\n"
                    f"Souhlasíte s tímto postupem? (ano/ne)"
                )
                RichPrinter._post(ChatMessage(question, owner='agent', msg_type='ask'))
                return

            # --- Handle other worker outcomes (completed, needs_planning, etc.) ---
            touched_files = worker_result.get("touched_files", [])
            tool_result_context = f"Worker dokončil úkol. Jeho finální stav je: {worker_result.get('status')}. Jeho shrnutí je: {worker_result.get('summary')}."
            self.history.append((explanation, json.dumps(worker_result)))

            if worker_result.get("status") == "completed" and worker_result.get("history"):
                await self._run_reflection(worker_result.get("history"))

            # Krok 3: Generování finální odpovědi s informací o souborech
            final_response = await self._generate_final_response(tool_result_context, touched_files)

        else:
            RichPrinter.error(f"Manažer se pokusil zavolat neznámou interní metodu: {tool_name}")
            tool_result_context = f"Došlo k interní chybě, nepodařilo se najít nástroj '{tool_name}'."
            self.history.append((explanation, tool_result_context))
            final_response = await self._generate_final_response(tool_result_context)


        RichPrinter._post(ChatMessage(final_response, owner='agent', msg_type='inform'))
        RichPrinter.info("Manažer dokončil plný cyklus zpracování úkolu.")


    async def _run_reflection(self, task_history: list):
        """
        Spustí proces sebereflexe. Vezme historii úkolu, vygeneruje "poučení"
        a uloží ho do dlouhodobé paměti.
        """
        RichPrinter.info("Spouštím sebereflexi na základě dokončeného úkolu...")

        # 1. Připrav prompt
        try:
            with open(os.path.join(self.project_root, "prompts/reflection_prompt.txt"), "r", encoding="utf-8") as f:
                reflection_prompt_template = f.read()
        except FileNotFoundError:
            RichPrinter.error("Prompt pro sebereflexi nebyl nalezen. Přeskakuji.")
            return

        history_str = "\n".join([f"Krok {i+1}:\nMyšlenka: {thought}\nAkce/Výsledek: {action}" for i, (thought, action) in enumerate(task_history)])
        prompt = reflection_prompt_template.format(task_history=history_str)

        # 2. Zavolej LLM
        model = self.llm_manager.get_llm("default")
        learning, _ = await model.generate_content_async(prompt)
        learning = learning.strip()

        if not learning or len(learning) < 10:
            RichPrinter.warning("Vytvořený poznatek je příliš krátký, ignoruji.")
            return

        # 3. Ulož poznatek do LTM
        # Použijeme samotný poznatek jako obsah pro embedding
        self.worker.ltm.add(
            documents=[learning],
            metadatas=[{"type": "learning"}],
            ids=[str(uuid.uuid4())]
        )
        RichPrinter.log_communication("Nový poznatek uložen do LTM", learning, style="bold green")