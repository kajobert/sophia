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

    async def run(self, initial_task: str, session_id: str | None = None, budget: int = 10, mission_prompt: str | None = None):
        """The main decision-making loop of the agent, with a dynamic budget and prompt selection."""
        self.status = "working"
        self.current_task = initial_task
        self.touched_files = set()  # Reset for each new run
        self.history = [] # Reset history for each sub-task run

        try:
            # The 'task_complete' tool is now only for the MissionManager. The worker's goal is to finish its sub-task.
            TERMINAL_TOOLS = ["inform_user", "warn_user", "error_user", "display_code", "display_table", "ask_user", "subtask_complete"]

            # Session history is managed by the ConversationalManager, but we can load it if needed.
            # For now, we start fresh for each sub-task to keep context clean.
            # if session_id:
            #     self.history = self.memory_manager.load_history(session_id) or []

            # Dynamic selection of the system prompt based on budget
            if budget <= 3:
                RichPrinter.info(f"Using simplified prompt for a simple task (budget: {budget}).")
                self.prompt_builder.system_prompt_path = os.path.join(self.project_root, "prompts/simple_system_prompt.txt")
            else:
                RichPrinter.info(f"Using standard prompt for a complex task (budget: {budget}).")
                self.prompt_builder.system_prompt_path = os.path.join(self.project_root, "prompts/system_prompt.txt")


            RichPrinter.info(f"Task for Worker: {initial_task}")
            RichPrinter.log_communication("User Input for Worker", initial_task, style="green")
            self.history.append(("", f"USER INPUT: {initial_task}"))

            # Use a for loop with a dynamic budget
            for i in range(budget):
                tool_descriptions = await self.mcp_client.get_tool_descriptions()
                # The overall mission goal is now passed in directly
                prompt = self.prompt_builder.build_prompt(tool_descriptions, self.history, main_goal=mission_prompt)

                model = self.llm_manager.get_llm(self.llm_manager.default_model_name)
                response_text, _ = await model.generate_content_async(prompt, response_format={"type": "json_object"})
                thought, tool_call_data = self._parse_llm_response(response_text)

                if thought: RichPrinter.log_communication("Worker's Thought Process", thought, style="dim blue")

                if not tool_call_data or "tool_name" not in tool_call_data:
                    self.history.append((thought, "No action."))
                    continue

                tool_name = tool_call_data["tool_name"]
                args = tool_call_data.get("args", [])
                kwargs = tool_call_data.get("kwargs", {})
                history_entry_request = f"Thought Process:\n{thought}\n\nTool Call:\n{json.dumps(tool_call_data, indent=2, ensure_ascii=False)}"
                RichPrinter.log_communication("Worker is calling tool", tool_call_data, style="yellow")

                # The worker should not decide the whole mission is complete.
                # It now uses 'subtask_complete'.
                if tool_name == "subtask_complete":
                    summary = kwargs.get("reason", "No summary provided.")
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


                result_str = await self.mcp_client.execute_tool(tool_name, args, kwargs, self.verbose)

                # Zpracování a logování případné chyby nástroje
                try:
                    result_data = json.loads(result_str)
                    if isinstance(result_data, dict) and "tool_error" in result_data:
                        error_message = result_data['tool_error']
                        error_context = (
                            f"Nástroj '{tool_name}' selhal s chybou: {error_message}\n"
                            f"Původní vstup: {json.dumps(tool_call_data, indent=2, ensure_ascii=False)}\n"
                            "--- \n"
                            "ANALYZUJ PŘÍČINU CHYBY. Zkontroluj, zda existují soubory, které chceš použít, "
                            "a zda jsou argumenty ve správném formátu. Poté zkus problém vyřešit jiným způsobem."
                        )
                        RichPrinter.error(f"Tool Error: {error_message}")
                        self.history.append((history_entry_request, error_context))
                    else:
                        self.history.append((history_entry_request, result_str))
                except json.JSONDecodeError:
                    self.history.append((history_entry_request, result_str))


                self.memory_manager.save_history(session_id, self.history)

                if tool_name in TERMINAL_TOOLS:
                    return {
                        "status": "completed",
                        "summary": f"Task finished by terminal tool: {tool_name}",
                        "history": self.history,
                        "touched_files": list(self.touched_files)
                    }

            # Pokud se cyklus dokončí (vyčerpá se budget)
            summary = "Agent vyčerpal přidělený rozpočet na kroky, aniž by úkol dokončil."
            RichPrinter.warning(summary)
            return {
                "status": "budget_exceeded",
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
            return parsed_response.get("thought", "").strip(), parsed_response.get("tool_call")
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