import sys
import os
import json
import asyncio
import re
import uuid
from enum import Enum

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

class TaskType(Enum):
    SIMPLE_QUERY = "Jednoduchý dotaz"
    DIRECT_COMMAND = "Přímý příkaz"
    COMPLEX_TASK = "Komplexní úkol"

class AgentState(Enum):
    IDLE = "Čekání na vstup"
    TRIAGE = "Klasifikace úkolu"
    PLANNING = "Plánování"
    EXECUTING = "Provádění"

class JulesOrchestrator:
    """
    Orchestrátor řídí agenta, klasifikuje úkoly, spravuje stav a komunikuje s LLM.
    """
    def __init__(self, project_root: str = ".", status_widget=None):
        self.project_root = os.path.abspath(project_root)
        self.history = []
        self.verbose = False
        self.last_full_output = None
        self.total_tokens = 0
        self.state = AgentState.IDLE
        self.session_id = None

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
        self.triage_prompt_template = self._load_triage_prompt()
        RichPrinter.info("Orchestrator V3 (Stateful) initialized.")

    def _load_triage_prompt(self) -> str:
        try:
            with open(os.path.join(self.project_root, "prompts/triage_prompt.txt"), "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            RichPrinter.error("Triage prompt not found. Using a default fallback.")
            return "Classify the user request. Respond with JSON: {\"task_type\": \"SIMPLE_QUERY|DIRECT_COMMAND|COMPLEX_TASK\"}"

    async def initialize(self):
        await self.mcp_client.start_servers()

    async def shutdown(self):
        await self.mcp_client.shutdown_servers()
        self.memory_manager.close()
        RichPrinter.info("Všechny služby byly bezpečně ukončeny.")

    async def _triage_user_request(self, user_input: str) -> dict:
        """Klasifikuje požadavek uživatele pomocí LLM."""
        self.state = AgentState.TRIAGE
        RichPrinter.info("Provádím klasifikaci úkolu...")

        conversation_history = "\n".join([f"Q: {q}\nA: {a}" for q, a in self.history[-3:]])
        prompt = self.triage_prompt_template.format(
            user_input=user_input,
            conversation_history=conversation_history
        )

        model = self.llm_manager.get_llm() # Use default model for triage
        response, _ = await model.generate_content_async(prompt, response_format={"type": "json_object"})

        parsed_response = self._parse_llm_response(response)
        task_type_str = parsed_response.get("task_type", "COMPLEX_TASK")

        try:
            task_type = TaskType[task_type_str]
        except KeyError:
            RichPrinter.warning(f"Neznámý typ úkolu '{task_type_str}', bude použit 'COMPLEX_TASK'.")
            task_type = TaskType.COMPLEX_TASK

        RichPrinter.info(f"Výsledek klasifikace: [bold cyan]{task_type.value}[/bold cyan]")
        return {"task_type": task_type, "details": parsed_response.get("details")}


    async def run(self, user_input: str, session_id: str | None = None):
        """Hlavní vstupní bod pro zpracování uživatelského vstupu."""
        if not self.session_id:
            self.session_id = session_id or str(uuid.uuid4())
            RichPrinter.info(f"### Zahájení nového sezení (ID: {self.session_id})")
            self.history = self.memory_manager.load_history(self.session_id) or []

        RichPrinter.info(f"Úkol: {user_input}")
        RichPrinter._post(ChatMessage(f"{user_input}", owner='user', msg_type='user_input'))
        RichPrinter.log_communication("Vstup od uživatele", user_input, style="green")

        triage_result = await self._triage_user_request(user_input)
        task_type = triage_result["task_type"]

        if task_type == TaskType.SIMPLE_QUERY:
            await self._handle_simple_query(user_input, triage_result.get("details"))
        elif task_type == TaskType.DIRECT_COMMAND:
            await self._handle_direct_command(user_input)
        elif task_type == TaskType.COMPLEX_TASK:
            await self._execute_complex_task(user_input)

        self.state = AgentState.IDLE

    async def _handle_simple_query(self, user_input: str, details: str | None):
        """Zpracuje jednoduchý dotaz a pošle odpověď."""
        RichPrinter.info("Zpracovávám jednoduchý dotaz...")
        # For a simple query, we might just need a direct answer from the LLM
        # without using tools.
        prompt = self.prompt_builder.build_prompt_for_simple_query(user_input, self.history)
        model = self.llm_manager.get_llm("fast") # Use a faster model for simple chat

        response, _ = await model.generate_content_async(prompt)

        RichPrinter._post(ChatMessage(response, owner='agent', msg_type='inform'))
        self.history.append((f"UŽIVATELSKÝ VSTUP: {user_input}", response))
        self.memory_manager.save_history(self.session_id, self.history)

    async def _handle_direct_command(self, user_input: str):
        """Provede jeden cyklus myšlenka -> nástroj -> výsledek."""
        RichPrinter.info("Zpracovávám přímý příkaz...")
        self.state = AgentState.EXECUTING
        self.history.append(("", f"UŽIVATELSKÝ VSTUP: {user_input}"))
        await self._execute_iteration(user_input, is_direct_command=True)
        self.memory_manager.save_history(self.session_id, self.history)


    async def _execute_complex_task(self, initial_task: str):
        """Spustí hlavní smyčku pro řešení komplexního úkolu."""
        RichPrinter.info("Zahajuji řešení komplexního úkolu...")
        self.state = AgentState.PLANNING # Or EXECUTING if plan exists
        self.history.append(("", f"UŽIVATELSKÝ VSTUP: {initial_task}"))

        for i in range(len(self.history), self.max_iterations):
            RichPrinter.info(f"### Iterace č. {i+1} | Stav: {self.state.name}")
            completed = await self._execute_iteration(initial_task)
            self.memory_manager.save_history(self.session_id, self.history)
            if completed:
                RichPrinter.info("Agent dokončil komplexní úkol.")
                break
        else:
            RichPrinter.warning(f"Agent dosáhl maximálního počtu iterací ({self.max_iterations}). Úkol byl ukončen.")
            self.memory_manager.save_session(self.session_id, initial_task, f"Přerušeno po {self.max_iterations} iteracích.")


    async def _execute_iteration(self, initial_task: str, is_direct_command: bool = False) -> bool:
        """Provede jednu úplnou iteraci cyklu myšlení-akce."""
        TERMINAL_TOOLS = ["inform_user", "warn_user", "error_user", "display_code", "display_table", "ask_user"]

        tool_descriptions = await self.mcp_client.get_tool_descriptions()
        main_goal_raw = await self.mcp_client.execute_tool("get_main_goal", [], {}, self.verbose)
        main_goal = None if "Není definován žádný hlavní cíl" in main_goal_raw else main_goal_raw

        prompt = self.prompt_builder.build_prompt(tool_descriptions, self.history, main_goal=main_goal)

        model = self.llm_manager.get_llm("powerful") # Complex tasks need the best model

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

        # TODO: Handle cost and token usage from usage_data

        parsed_response = self._parse_llm_response(response_text)
        explanation = parsed_response.get("explanation", "Není k dispozici žádné vysvětlení.")
        tool_call_data = parsed_response.get("tool_call")

        RichPrinter.log_communication("Myšlenkový pochod", explanation, style="dim blue")

        if not tool_call_data or "tool_name" not in tool_call_data:
            RichPrinter.warning("LLM se rozhodl nepoužít nástroj.")
            self.history.append((explanation, "Žádná akce."))
            return False

        tool_name = tool_call_data["tool_name"]
        args = tool_call_data.get("args", [])
        kwargs = tool_call_data.get("kwargs", {})

        RichPrinter.log_communication("Volání nástroje", tool_call_data, style="yellow")
        history_entry_request = f"Myšlenkový pochod:\n{explanation}\n\nVolání nástroje:\n{json.dumps(tool_call_data, indent=2, ensure_ascii=False)}"

        if tool_name == "task_complete":
            summary = kwargs.get("reason", "Nebylo poskytnuto žádné shrnutí.")
            RichPrinter._post(ChatMessage(summary, owner='agent', msg_type='task_complete'))
            self.memory_manager.save_session(self.session_id, initial_task, summary)
            return True

        result = await self.mcp_client.execute_tool(tool_name, args, kwargs, self.verbose)

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
        self.ltm.add_memory(f"Krok:\n{history_entry_request}\n\nVýsledek:\n{output_for_history}", metadata={"session_id": self.session_id})

        if is_direct_command or tool_name in TERMINAL_TOOLS:
            return True # End after one cycle for direct commands or terminal tools

        return False


    def _parse_llm_response(self, response_text: str) -> dict:
        """Parzuje JSON odpověď od LLM, ošetřuje chyby."""
        cleaned_text = response_text.strip()
        match = re.search(r"```(json)?\s*\n(.*?)\n```", cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(2).strip()
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            RichPrinter.log_error_panel("Selhání parsování JSON odpovědi", cleaned_text, exception=e)
            return {"error": "JSON_DECODE_ERROR", "explanation": "Chyba při parsování odpovědi serveru."}

    def _handle_long_output(self, result: str) -> tuple[str, str]:
        line_limit = 20
        if isinstance(result, str) and len(result.splitlines()) > line_limit:
            self.last_full_output = result
            summary = f"Výstup je příliš dlouhý ({len(result.splitlines())} řádků). Zobrazeno prvních {line_limit-2} řádků.\n"
            summary += "\n".join(result.splitlines()[:line_limit-2]) + "\n[...]"
            return summary, summary
        return result, result