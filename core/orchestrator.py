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

class WorkerOrchestrator:
    """
    Asynchronní "worker", který provádí konkrétní úkoly. Komunikuje s LLM,
    používá nástroje a ukládá své zkušenosti do perzistentní paměti.
    Pracuje v rámci "rozpočtu na složitost".
    """

    def __init__(self, project_root: str = ".", status_widget=None):
        self.project_root = os.path.abspath(project_root)
        self.history = []
        self.verbose = False
        self.last_full_output = None
        self.total_tokens = 0
        self.touched_files = set()
        # Worker má svůj vlastní MCP klient s profilem "worker"
        self.mcp_client = MCPClient(project_root=self.project_root, profile="worker")
        self.memory_manager = MemoryManager()
        self.llm_manager = LLMManager(project_root=self.project_root)
        self.cost_manager = CostManager(project_root=self.project_root)
        self.ltm = LongTermMemory(project_root=self.project_root)
        self.status_widget = status_widget
        # Přidání stavových atributů
        self.status = "idle"
        self.current_task = "None"

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
        RichPrinter.info("WorkerOrchestrator initialized.")

    async def initialize(self):
        await self.mcp_client.start_servers()

    async def shutdown(self):
        await self.mcp_client.shutdown_servers()
        self.memory_manager.close()
        RichPrinter.info("WorkerOrchestrator services have been safely shut down.")

    async def run(self, initial_task: str, session_id: str | None = None, budget: int = 10):
        """Hlavní rozhodovací smyčka agenta s dynamickým rozpočtem a výběrem promptu."""
        self.status = "working"
        self.current_task = initial_task
        self.touched_files = set()  # Reset pro každý nový běh

        try:
            TERMINAL_TOOLS = ["inform_user", "warn_user", "error_user", "display_code", "display_table", "ask_user"]

            if session_id:
                self.history = self.memory_manager.load_history(session_id) or []

            # Dynamický výběr systémového promptu na základě budgetu
            if budget <= 3:
                RichPrinter.info(f"Používám zjednodušený prompt pro jednoduchý úkol (budget: {budget}).")
                self.prompt_builder.system_prompt_path = os.path.join(self.project_root, "prompts/simple_system_prompt.txt")
            else:
                RichPrinter.info(f"Používám standardní prompt pro komplexní úkol (budget: {budget}).")
                self.prompt_builder.system_prompt_path = os.path.join(self.project_root, "prompts/system_prompt.txt")


            RichPrinter.info(f"Úkol pro Workera: {initial_task}")
            RichPrinter.log_communication("Vstup od uživatele pro Workera", initial_task, style="green")
            if not self.history:
                self.history.append(("", f"UŽIVATELSKÝ VSTUP: {initial_task}"))

            # Použijeme for smyčku s dynamickým budgetem
            for i in range(budget):
                tool_descriptions = await self.mcp_client.get_tool_descriptions()

                # Pojistka proti "otrávení" kontextu
                safe_initial_task = initial_task
                if isinstance(initial_task, str) and initial_task.strip().startswith("Error:"):
                    safe_initial_task = "Hlavní cíl mise je neplatný nebo obsahuje chybu. Řiď se pokyny z historie a posledním vstupem od uživatele."

                prompt = self.prompt_builder.build_prompt(tool_descriptions, self.history, main_goal=safe_initial_task)

                model = self.llm_manager.get_llm(self.llm_manager.default_model_name)
                response_text, _ = await model.generate_content_async(prompt, response_format={"type": "json_object"})
                explanation, tool_call_data = self._parse_llm_response(response_text)

                if explanation: RichPrinter.log_communication("Myšlenkový pochod Workera", explanation, style="dim blue")

                if not tool_call_data or "tool_name" not in tool_call_data:
                    self.history.append((explanation, "Žádná akce."))
                    continue

                tool_name = tool_call_data["tool_name"]
                args = tool_call_data.get("args", [])
                kwargs = tool_call_data.get("kwargs", {})
                history_entry_request = f"Myšlenkový pochod:\n{explanation}\n\nVolání nástroje:\n{json.dumps(tool_call_data, indent=2, ensure_ascii=False)}"
                RichPrinter.log_communication("Worker volá nástroj", tool_call_data, style="yellow")

                if tool_name == "task_complete":
                    summary = kwargs.get("reason", "Nebylo poskytnuto žádné shrnutí.")
                    return {
                        "status": "completed",
                        "summary": summary,
                        "history": self.history,
                        "touched_files": list(self.touched_files)
                    }

                # >>> HUMAN-IN-THE-LOOP FOR DELEGATION <<<
                if tool_name == "delegate_task_to_jules":
                    RichPrinter.info("Worker is proposing to delegate a task to Jules. Pausing for user approval.")
                    # Save the current history so the manager can continue
                    self.memory_manager.save_history(session_id, self.history)
                    return {
                        "status": "needs_delegation_approval",
                        "summary": "Worker wants to delegate a task to an external agent.",
                        "tool_call": tool_call_data,  # Send tool call info to the manager
                        "history": self.history
                    }

                # Sledování upravených souborů
                FILE_MODIFYING_TOOLS = {
                    "create_file_with_block": 0,  # filepath je první argument
                    "overwrite_file_with_block": 0,
                    "replace_with_git_merge_diff": 0,
                    "delete_file": 0,
                    "rename_file": 1 # new_filepath je druhý argument
                }
                if tool_name in FILE_MODIFYING_TOOLS:
                    try:
                        arg_index = FILE_MODIFYING_TOOLS[tool_name]
                        filepath = args[arg_index] if args and len(args) > arg_index else kwargs.get('filepath') or kwargs.get('new_filepath')
                        if filepath:
                            self.touched_files.add(filepath)
                            RichPrinter.info(f"Soubor '{filepath}' byl označen jako upravený.")
                    except (IndexError, KeyError) as e:
                        RichPrinter.warning(f"Nepodařilo se extrahovat cestu k souboru pro nástroj '{tool_name}': {e}")


                result = await self.mcp_client.execute_tool(tool_name, args, kwargs, self.verbose)
                self.history.append((history_entry_request, result))
                self.memory_manager.save_history(session_id, self.history)

                if tool_name in TERMINAL_TOOLS:
                    return {
                        "status": "completed",
                        "summary": f"Task finished by terminal tool: {tool_name}",
                        "history": self.history,
                        "touched_files": list(self.touched_files)
                    }

            summary = "Úkol je složitější a vyžaduje formální plán. Vyčerpal jsem rozpočet."
            return {
                "status": "needs_planning",
                "summary": summary,
                "history": self.history,
                "touched_files": list(self.touched_files)
            }

        except Exception as e:
            RichPrinter.log_error_panel("Chyba v běhu Workera", str(e), exception=e)
            return {
                "status": "error",
                "message": str(e),
                "history": self.history,
                "touched_files": list(self.touched_files)
            }

        finally:
            # Resetování stavu na konci běhu
            self.status = "idle"
            self.current_task = "None"

    def _parse_llm_response(self, response_text: str) -> tuple[str, dict | None]:
        cleaned_text = response_text.strip()
        match = re.search(r"```(json)?\s*\n(.*?)\n```", cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(2).strip()
        try:
            parsed_response = json.loads(cleaned_text)
            return parsed_response.get("explanation", "").strip(), parsed_response.get("tool_call")
        except json.JSONDecodeError as e:
            RichPrinter.log_error_panel("Selhání parsování JSON odpovědi (Worker)", cleaned_text, exception=e)
            return f"[SYSTÉM]: CHYBA PARSOVÁNÍ JSON.", None

    def _handle_long_output(self, result: str) -> tuple[str, str]:
        # This function seems to be unused now, but keeping it for potential future use.
        line_limit = 20
        if isinstance(result, str) and len(result.splitlines()) > line_limit:
            self.last_full_output = result
            summary = f"Výstup je příliš dlouhý ({len(result.splitlines())} řádků). Zobrazeno prvních {line_limit-2} řádků.\n"
            summary += "\n".join(result.splitlines()[:line_limit-2]) + "\n[...]"
            return summary, summary
        return result, result