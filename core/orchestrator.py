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

    async def _should_delegate(self, task: str, tool_descriptions: str) -> bool:
        """
        Analyzes the task to decide if it should be delegated or handled locally.
        This is a "Tool Check" to enforce the "local tools first" rule.
        """
        RichPrinter.info("Performing 'Tool Check' to decide on delegation...")

        # Find the path to the delegation check prompt
        delegation_prompt_path = os.path.join(self.project_root, "prompts/delegation_check_prompt.txt")
        try:
            with open(delegation_prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            RichPrinter.error(f"Delegation check prompt not found at: {delegation_prompt_path}. Defaulting to no delegation.")
            return False

        prompt = prompt_template.format(task=task, tools=tool_descriptions)
        # Use a fast and cheap model for this simple classification task
        fast_model_name = self.llm_manager.config.get("llm_models", {}).get("fast_model", "default")
        model = self.llm_manager.get_llm(fast_model_name)

        response_text, _ = await model.generate_content_async(prompt, response_format={"type": "json_object"})

        try:
            RichPrinter.info(f"--- Delegation Check Diagnostics ---")
            RichPrinter.log_communication("Raw LLM Response", response_text, style="dim")

            # Clean the response: remove markdown and strip whitespace
            match = re.search(r"```(json)?\s*\n(.*?)\n```", response_text, re.DOTALL)
            json_str = match.group(2).strip() if match else response_text.strip()
            RichPrinter.log_communication("Cleaned JSON String", json_str, style="dim")

            # The LLM sometimes returns keys with extra whitespace. To make this robust,
            # we can load the JSON and then access the key flexibly.
            decision = json.loads(json_str)
            RichPrinter.log_communication("Parsed Decision Dict", str(decision), style="dim")

            # Find the key 'should_delegate' regardless of surrounding whitespace
            key = next((k for k in decision if k.strip() == "should_delegate"), None)
            RichPrinter.log_communication("Found Key", str(key), style="dim")

            if key is None:
                RichPrinter.warning("Delegation check response did not contain the 'should_delegate' key. Defaulting to False.")
                RichPrinter.info(f"--- End Diagnostics ---")
                return False

            should_delegate = decision.get(key, False)
            RichPrinter.log_communication("Final Decision", str(should_delegate), style="bold blue")
            RichPrinter.info(f"--- End Diagnostics ---")
            return should_delegate

        except Exception as e:
            RichPrinter.log_error_panel("An exception occurred during delegation check. Defaulting to False.", response_text, exception=e)
            RichPrinter.info(f"--- End Diagnostics ---")
            return False

    async def run(self, initial_task: str, session_id: str | None = None, mission_prompt: str | None = None):
        """The main decision-making loop of the agent. It now decides whether to delegate upfront."""
        self.status = "working"
        self.current_task = initial_task
        self.touched_files = set()
        self.history = []

        try:
            # Always use the standard system prompt, budget-based selection is removed.
            self.prompt_builder.system_prompt_path = os.path.join(self.project_root, "prompts/system_prompt.txt")
            tool_descriptions = await self.mcp_client.get_tool_descriptions()

            # Step 1: Perform the "Tool Check"
            if await self._should_delegate(initial_task, tool_descriptions):
                RichPrinter.info("Task requires delegation based on Tool Check.")
                # Construct the delegation tool call
                tool_call_data = {
                    "tool_name": "delegate_task_to_jules",
                    "kwargs": {
                        "prompt": initial_task,
                        "title": f"Handle complex task: {initial_task[:40]}...",
                        # 'source' and 'starting_branch' must be provided by a higher-level manager
                        # This worker does not have that context.
                    }
                }
                return {
                    "status": "needs_delegation_approval",
                    "summary": "Worker has determined the task requires capabilities beyond its local tools.",
                    "tool_call": tool_call_data,
                    "history": self.history
                }

            # Step 2: If not delegating, proceed with the local execution loop
            RichPrinter.info("Proceeding with local execution.")
            TERMINAL_TOOLS = ["inform_user", "warn_user", "error_user", "display_code", "display_table", "ask_user", "subtask_complete"]

            RichPrinter.log_communication("User Input for Worker", initial_task, style="green")
            self.history.append(("", f"USER INPUT: {initial_task}"))

            for i in range(self.max_iterations): # Use internal max_iterations as budget
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

                if tool_name == "subtask_complete":
                    summary = kwargs.get("reason", "No summary provided.")
                    return {
                        "status": "completed",
                        "summary": summary,
                        "history": self.history,
                        "touched_files": list(self.touched_files)
                    }

                # This logic should now be caught by the initial `_should_delegate` check.
                # If the LLM still tries to delegate, we treat it as a logic error and stop.
                if tool_name == "delegate_task_to_jules":
                    RichPrinter.warning("LLM attempted to delegate mid-task, which should not happen. Stopping execution.")
                    return {
                        "status": "error",
                        "summary": "Agent attempted to delegate after deciding to use local tools.",
                        "history": self.history,
                        "touched_files": list(self.touched_files)
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