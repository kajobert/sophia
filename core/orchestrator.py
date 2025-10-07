import sys
import os
import json
import asyncio
import re
import textwrap
import uuid
from dotenv import load_dotenv
import yaml

# Přidání cesty k projektu pro importy
project_root_for_import = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root_for_import not in sys.path:
    sys.path.insert(0, project_root_for_import)

from tui.messages import ChatMessage
from core.mcp_client import MCPClient
from core.prompt_builder import PromptBuilder
from core.rich_printer import RichPrinter
from core.memory_manager import MemoryManager
from core.llm_manager import LLMManager
from core.cost_manager import CostManager
from core.long_term_memory import LongTermMemory

class JulesOrchestrator:
    """
    Finální, asynchronní orchestrátor, který řídí agenta, komunikuje s LLM
    a ukládá své zkušenosti do perzistentní paměti.
    """

    def __init__(self, project_root: str = ".", status_widget=None):
        self.project_root = os.path.abspath(project_root)
        self.history = []
        self.verbose = False
        self.last_full_output = None
        self.total_tokens = 0
        self.mcp_client = MCPClient(project_root=self.project_root)
        self.memory_manager = MemoryManager()
        self.llm_manager = LLMManager(project_root=self.project_root)
        self.cost_manager = CostManager(project_root=self.project_root)
        self.ltm = LongTermMemory(project_root=self.project_root)
        self.status_widget = status_widget

        orchestrator_config = self.llm_manager.config.get("orchestrator", {})
        self.max_iterations = orchestrator_config.get("max_iterations", 15)

        memory_config = self.llm_manager.config.get("memory", {})
        self.short_term_limit = memory_config.get("short_term_limit", 4)
        self.long_term_retrieval_limit = memory_config.get("long_term_retrieval_limit", 5)

        self.prompt_builder = PromptBuilder(
            system_prompt_path=os.path.join(self.project_root, "prompts/system_prompt.txt"),
            ltm=self.ltm,
            short_term_limit=self.short_term_limit,
            long_term_retrieval_limit=self.long_term_retrieval_limit
        )
        RichPrinter.info("V2 Orchestrator initialized with LLMManager and CostManager.")

    async def initialize(self):
        await self.mcp_client.start_servers()

    async def shutdown(self):
        await self.mcp_client.shutdown_servers()
        self.memory_manager.close()
        RichPrinter.info("Všechny služby byly bezpečně ukončeny.")

    async def _triage_user_request(self, user_input: str) -> str:
        """Klasifikuje požadavek uživatele na základě triage promptu."""
        try:
            with open(os.path.join(self.project_root, "prompts/triage_prompt.txt"), "r", encoding="utf-8") as f:
                triage_prompt_template = f.read()
        except FileNotFoundError:
            RichPrinter.log_error_panel("Triage prompt not found", "Soubor prompts/triage_prompt.txt chybí.")
            return "COMPLEX_TASK"

        prompt = triage_prompt_template.format(user_input=user_input)
        # Pro klasifikaci použijeme výchozí, rychlý model
        model = self.llm_manager.get_llm()

        RichPrinter.info("Klasifikuji požadavek...")
        response, _ = await model.generate_content_async(prompt, max_tokens=20) # Zvýšeno pro jistotu

        task_type = response.strip().upper()
        # Odstranění případných ```json a podobných artefaktů
        task_type = re.sub(r'[^A-Z_]', '', task_type)

        if task_type not in ["SIMPLE_QUERY", "DIRECT_COMMAND", "COMPLEX_TASK"]:
            RichPrinter.warning(f"Neznámý typ úkolu '{task_type}', bude použit fallback na COMPLEX_TASK.")
            return "COMPLEX_TASK"

        RichPrinter.info(f"Typ požadavku: [bold yellow]{task_type}[/bold yellow]")
        return task_type

    async def _handle_simple_query(self, user_input: str, session_id: str):
        """Zpracuje jednoduchý dotaz bez použití nástrojů."""
        RichPrinter.info("Zpracovávám jednoduchý dotaz...")

        # Vytvoříme jednoduchý prompt pro konverzační odpověď
        # Zjednodušená historie pro přímou odpověď
        history_summary = "\n".join([f"Uživatel: {h[1]}\nAgent: {h[0]}" for h in self.history[-self.short_term_limit:] if h[0]])

        prompt = textwrap.dedent(f"""
            Jsi konverzační AI asistent Jules. Odpověz na poslední dotaz uživatele stručně a přátelsky.

            Předchozí konverzace:
            {history_summary}

            Poslední dotaz: "{user_input}"

            Tvoje odpověď:
        """).strip()

        model = self.llm_manager.get_llm()

        full_response_text = ""
        async def stream_callback(chunk: str):
            nonlocal full_response_text
            full_response_text += chunk
            RichPrinter._post(ChatMessage(chunk, owner='agent', msg_type='explanation_chunk'))

        # Pro jednoduchou odpověď nepotřebujeme JSON formát
        await model.generate_content_async(prompt, stream_callback=stream_callback)
        RichPrinter._post(ChatMessage("", owner='agent', msg_type='explanation_end'))

        self.history.append((full_response_text, f"UŽIVATELSKÝ VSTUP: {user_input}"))
        self.memory_manager.save_history(session_id, self.history)
        self.ltm.add_memory(f"Uživatel: {user_input}\nAgent: {full_response_text}", metadata={"session_id": session_id, "is_query": True})

    async def run(self, initial_task: str, session_id: str | None = None):
        """Hlavní rozhodovací smyčka agenta."""
        TERMINAL_TOOLS = ["inform_user", "warn_user", "error_user", "display_code", "display_table", "ask_user"]

        if session_id:
            RichPrinter.info(f"### Obnovuji sezení: {session_id}")
            self.history = self.memory_manager.load_history(session_id) or []
        else:
            session_id = str(uuid.uuid4())
            RichPrinter.info(f"### Zahájení nového sezení (ID: {session_id})")

        RichPrinter.info(f"Úkol: {initial_task}")
        RichPrinter._post(ChatMessage(f"{initial_task}", owner='user', msg_type='user_input'))
        RichPrinter.log_communication("Vstup od uživatele", initial_task, style="green")

        # --- NOVÁ TRIAGE LOGIKA ---
        # Triage provádíme jen u prvního požadavku v sezení, kde ještě není historie.
        if not self.history:
            task_type = await self._triage_user_request(initial_task)
            if task_type == "SIMPLE_QUERY":
                await self._handle_simple_query(initial_task, session_id)
                return  # Ukončíme běh po přímé odpovědi
            # Pro DIRECT_COMMAND a COMPLEX_TASK pokračujeme do hlavní smyčky
        # --- KONEC TRIAGE LOGIKY ---

        if not self.history:
            self.history.append(("", f"UŽIVATELSKÝ VSTUP: {initial_task}"))
            self.memory_manager.save_history(session_id, self.history)

        task_was_completed_by_agent = False
        for i in range(len(self.history), self.max_iterations):
            tool_descriptions = await self.mcp_client.get_tool_descriptions()

            # Získání hlavního cíle mise
            main_goal_raw = await self.mcp_client.execute_tool("get_main_goal", [], {}, self.verbose)
            main_goal = None if "Není definován žádný hlavní cíl" in main_goal_raw else main_goal_raw

            prompt = self.prompt_builder.build_prompt(tool_descriptions, self.history, main_goal=main_goal)

            # Prozatím použijeme výchozí model. Výběr modelu lze v budoucnu vylepšit.
            try:
                model = self.llm_manager.get_llm()
                RichPrinter.info(f"Vybrán model: [bold cyan]{model.model_name}[/bold cyan]")
            except (ValueError, FileNotFoundError) as e:
                RichPrinter.log_error_panel("Selhání načtení LLM modelu", str(e), exception=e)
                break

            RichPrinter.info(f"### Iterace č. {i+1} | Celkem tokenů: {self.total_tokens}")
            RichPrinter.info(f"Přemýšlím... (model: {model.model_name})")

            full_response_text = ""
            async def stream_callback(chunk: str):
                nonlocal full_response_text
                full_response_text += chunk
                RichPrinter._post(ChatMessage(chunk, owner='agent', msg_type='explanation_chunk'))

            response_text, usage_data = await model.generate_content_async(
                prompt,
                stream_callback=stream_callback,
                response_format={"type": "json_object"}
            )
            RichPrinter._post(ChatMessage("", owner='agent', msg_type='explanation_end'))

            if usage_data:
                # Zpracování nákladů a tokenů...
                pass

            explanation, tool_call_data = self._parse_llm_response(response_text)
            if explanation:
                RichPrinter.log_communication("Myšlenkový pochod", explanation, style="dim blue")

            if not tool_call_data or "tool_name" not in tool_call_data:
                RichPrinter.warning("LLM se rozhodl nepoužít nástroj.")
                if explanation: self.history.append((explanation, "Žádná akce."))
                continue

            tool_name = tool_call_data["tool_name"]
            args = tool_call_data.get("args", [])
            kwargs = tool_call_data.get("kwargs", {})
            RichPrinter.log_communication("Volání nástroje", tool_call_data, style="yellow")
            history_entry_request = f"Myšlenkový pochod:\n{explanation}\n\nVolání nástroje:\n{json.dumps(tool_call_data, indent=2, ensure_ascii=False)}"

            # Zpracování `task_complete` je nyní součástí běžného toku, aby se využila
            # robustní logika v `control_server.py`.
            # Zde pouze detekujeme, že se má cyklus ukončit.
            if tool_name == "task_complete":
                task_was_completed_by_agent = True

            result = await self.mcp_client.execute_tool(tool_name, args, kwargs, self.verbose)

            # Po vykonání `task_complete` se cyklus přirozeně ukončí v další iteraci,
            # protože `task_was_completed_by_agent` je True.
            if task_was_completed_by_agent:
                # Uložíme finální stav se shrnutím, které vrátil nástroj
                summary = result if isinstance(result, str) else "Úkol dokončen."
                self.memory_manager.save_session(session_id, initial_task, summary)
                RichPrinter._post(ChatMessage(summary, owner='agent', msg_type='task_complete'))
                break

            try:
                data = json.loads(result)
                if isinstance(data, dict) and 'display' in data:
                    RichPrinter._post(ChatMessage(data.get('content'), owner='agent', msg_type=data['display']))
                    result = "OK. Zpráva zobrazena uživateli."
            except (json.JSONDecodeError, TypeError):
                pass

            output_for_display, output_for_history = self._handle_long_output(result)
            RichPrinter.log_communication("Výsledek nástroje", output_for_history, style="cyan")
            RichPrinter._post(ChatMessage(output_for_display, owner='agent', msg_type='tool_output'))

            self.history.append((history_entry_request, output_for_history))
            self.memory_manager.save_history(session_id, self.history)
            self.ltm.add_memory(f"Krok {i+1}:\n{history_entry_request}\n\nVýsledek:\n{output_for_history}", metadata={"session_id": session_id, "iteration": i + 1})

            if tool_name in TERMINAL_TOOLS:
                task_was_completed_by_agent = True
                break

        if not task_was_completed_by_agent:
            RichPrinter.warning(f"Agent dosáhl maximálního počtu iterací ({self.max_iterations}). Úkol byl ukončen.")
            self.memory_manager.save_session(session_id, initial_task, f"Přerušeno po {self.max_iterations} iteracích.")

    def _parse_llm_response(self, response_text: str) -> tuple[str, dict | None]:
        cleaned_text = response_text.strip()
        match = re.search(r"```(json)?\s*\n(.*?)\n```", cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(2).strip()
        try:
            parsed_response = json.loads(cleaned_text)
            return parsed_response.get("explanation", "").strip(), parsed_response.get("tool_call")
        except json.JSONDecodeError as e:
            RichPrinter.log_error_panel("Selhání parsování JSON odpovědi", cleaned_text, exception=e)
            return f"[SYSTÉM]: CHYBA PARSOVÁNÍ JSON.", None

    def _handle_long_output(self, result: str) -> tuple[str, str]:
        line_limit = 20
        if isinstance(result, str) and len(result.splitlines()) > line_limit:
            self.last_full_output = result
            summary = f"Výstup je příliš dlouhý ({len(result.splitlines())} řádků). Zobrazeno prvních {line_limit-2} řádků.\n"
            summary += "\n".join(result.splitlines()[:line_limit-2]) + "\n[...]"
            return summary, summary
        return result, result