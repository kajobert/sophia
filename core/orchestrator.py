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

from core.mcp_client import MCPClient
from core.prompt_builder import PromptBuilder
from core.rich_printer import RichPrinter
from core.memory_manager import MemoryManager
from core.llm_manager import LLMManager
from core.cost_manager import CostManager

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
        self.prompt_builder = PromptBuilder(system_prompt_path=os.path.join(self.project_root, "prompts/system_prompt.txt"))
        self.memory_manager = MemoryManager()
        self.llm_manager = LLMManager(project_root=self.project_root)
        self.cost_manager = CostManager(project_root=self.project_root)
        self.status_widget = status_widget

        # Načtení specifické konfigurace pro orchestrátor
        orchestrator_config = self.llm_manager.config.get("orchestrator", {})
        self.max_iterations = orchestrator_config.get("max_iterations", 15)

        RichPrinter.info("V2 Orchestrator initialized with LLMManager and CostManager.")

    async def initialize(self):
        """Provede kompletní inicializaci."""
        # _load_config se volá v LLMManager, není třeba ho volat zde znovu
        await self.mcp_client.start_servers()

    async def shutdown(self):
        """Bezpečně ukončí všechny spuštěné služby."""
        await self.mcp_client.shutdown_servers()
        self.memory_manager.close()
        RichPrinter.info("Všechny služby byly bezpečně ukončeny.")

    def _triage_task_and_select_llm(self, prompt: str) -> str:
        """
        Analyzuje prompt a vybere nejvhodnější LLM model.
        """
        prompt_lower = prompt.lower()
        powerful_keywords = ["analyzuj", "refaktoruj", "navrhni", "implementuj", "vytvoř kód"]
        economical_keywords = ["vypiš", "přečti", "zkontroluj", "potvrď"]

        if any(keyword in prompt_lower for keyword in powerful_keywords):
            return "powerful"
        elif any(keyword in prompt_lower for keyword in economical_keywords):
            return "economical"
        else:
            return self.llm_manager.default_llm_name

    async def run(self, initial_task: str, session_id: str | None = None):
        """Hlavní rozhodovací smyčka agenta."""
        if session_id:
            RichPrinter.info(f"### Obnovuji sezení: {session_id}")
            loaded_history = self.memory_manager.load_history(session_id)
            if loaded_history:
                self.history = loaded_history
                RichPrinter.info(f"Historie pro sezení '{session_id}' byla úspěšně načtena ({len(self.history)} kroků).")
            else:
                RichPrinter.warning(f"Pro sezení '{session_id}' nebyla nalezena žádná historie. Vytvářím nové sezení.")
                session_id = str(uuid.uuid4()) # Vytvoříme nové ID, pokud staré nebylo nalezeno
        else:
            session_id = str(uuid.uuid4())
            RichPrinter.info(f"### Zahájení nového sezení (ID: {session_id})")

        RichPrinter.info(f"Úkol: {initial_task}")
        self.history.append(("", f"UŽIVATELSKÝ VSTUP: {initial_task}"))
        self.memory_manager.save_history(session_id, self.history)


        task_was_completed_by_agent = False
        for i in range(len(self.history), self.max_iterations):
            tool_descriptions = await self.mcp_client.get_tool_descriptions()
            prompt = self.prompt_builder.build_prompt(tool_descriptions, self.history)

            # Fáze 1: Výběr modelu
            selected_model_name = self._triage_task_and_select_llm(prompt)

            try:
                model = self.llm_manager.get_llm(selected_model_name)
                RichPrinter.info(f"Vybrán model: [bold cyan]{model.model_name}[/bold cyan] (alias: {selected_model_name})")
            except (ValueError, FileNotFoundError) as e:
                RichPrinter.error(f"Nepodařilo se načíst model '{selected_model_name}': {e}")
                break

            # Fáze 2: Volání LLM s vynuceným JSON formátem
            RichPrinter.info(f"### Iterace č. {i+1} | Celkem tokenů: {self.total_tokens}")
            RichPrinter.info(f"Přemýšlím... (model: {model.model_name})")

            # Schéma pro vynucení JSON odpovědi
            tool_call_schema = {
                "type": "json_schema",
                "json_schema": {
                    "name": "tool_call_with_explanation",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "explanation": {
                                "type": "string",
                                "description": "Tvůj myšlenkový pochod krok za krokem, zdůvodnění a vysvětlení, proč volíš tento nástroj a tyto parametry. Musí být v češtině."
                            },
                            "tool_call": {
                                "type": "object",
                                "properties": {
                                    "tool_name": {"type": "string"},
                                    "args": {"type": "array", "items": {}},
                                    "kwargs": {"type": "object"}
                                },
                                "required": ["tool_name"]
                            }
                        },
                        "required": ["explanation", "tool_call"]
                    }
                }
            }

            if self.verbose:
                RichPrinter.agent_markdown(f"**Prompt odeslaný do LLM:**\n\n```\n{prompt}\n```")

            # --- Nová logika pro streamování a parsování ---
            full_response_text = ""
            explanation_streamed = ""
            tool_call_json_str = None
            tool_call_started = False

            # Callback pro zpracování streamovaných dat
            async def stream_callback(chunk: str):
                nonlocal full_response_text, explanation_streamed, tool_call_json_str, tool_call_started
                full_response_text += chunk

                # Jakmile najdeme separátor, vše ostatní je JSON pro volání nástroje
                if "|||TOOL_CALL|||" in full_response_text and not tool_call_started:
                    parts = full_response_text.split("|||TOOL_CALL|||", 1)
                    explanation_chunk = parts[0][len(explanation_streamed):] # Pošleme jen to, co je nové
                    if explanation_chunk:
                         RichPrinter.stream_explanation(explanation_chunk)
                    explanation_streamed = parts[0]
                    tool_call_started = True
                    # Zbytek je začátek JSONu, zatím ho neparsujeme

                # Pokud streamujeme myšlenkový pochod
                elif not tool_call_started:
                    RichPrinter.stream_explanation(chunk)
                    explanation_streamed += chunk

            # Zavoláme LLM se streamováním
            response_text, usage_data = await model.generate_content_async(
                prompt,
                stream_callback=stream_callback
            )

            # Zpracování nákladů a tokenů
            if usage_data:
                generation_id = usage_data.get("id")
                if generation_id:
                    cost = await self.cost_manager.get_generation_cost(generation_id)
                    self.cost_manager.add_cost(cost)
                    RichPrinter.info(f"Náklady na tento krok: ${cost:.6f} | Celkové náklady: {self.cost_manager.get_total_cost_str()}")

                if usage_data.get("usage"):
                    token_count = usage_data["usage"].get("total_tokens", 0)
                    self.total_tokens += token_count
                    RichPrinter.info(f"Počet spotřebovaných tokenů v tomto kroku: {token_count}")


            # Ukončení streamu v TUI
            RichPrinter.finish_explanation_stream()

            # Finální parsování kompletní odpovědi
            explanation = ""
            tool_call_data = None

            try:
                if "|||TOOL_CALL|||" in response_text:
                    explanation_part, tool_call_json_str = response_text.split("|||TOOL_CALL|||", 1)
                    explanation = explanation_part.strip()
                    tool_call_json_str = tool_call_json_str.strip()

                    # Robustnější parsování JSONu, který může být obalen v ```json ... ```
                    match = re.search(r'\{.*\}', tool_call_json_str, re.DOTALL)
                    if match:
                        tool_call_json_str = match.group(0)
                        tool_call_data = json.loads(tool_call_json_str)
                    else:
                        raise json.JSONDecodeError("Nebyl nalezen platný JSON objekt.", tool_call_json_str, 0)
                else:
                    explanation = response_text.strip()
                    RichPrinter.warning("Odpověď LLM neobsahovala separátor '|||TOOL_CALL|||'. Považuji celou odpověď za myšlenkový pochod.")

            except json.JSONDecodeError as e:
                RichPrinter.error(f"Nepodařilo se zparsovat JSON z odpovědi LLM: {e}")
                RichPrinter.error(f"Přijatý text pro parsování: {tool_call_json_str if 'tool_call_json_str' in locals() else response_text}")
                explanation = response_text
                tool_call_data = None

            if not tool_call_data or "tool_name" not in tool_call_data:
                RichPrinter.warning("LLM se rozhodl nepoužít nástroj v tomto kroku nebo se JSON nepodařilo zparsovat. Pokračuji v přemýšlení.")
                # I když se streamovalo, finální vysvětlení uložíme do historie
                if explanation:
                    self.history.append((explanation, "Žádná akce."))
                    self.memory_manager.save_history(session_id, self.history)
                continue

            tool_name = tool_call_data["tool_name"]
            args = tool_call_data.get("args", [])
            kwargs = tool_call_data.get("kwargs", {})

            RichPrinter.info(">>> AKCE")
            RichPrinter.agent_tool_code(json.dumps(tool_call_data, indent=2, ensure_ascii=False))

            # Sestavení záznamu do historie (myšlenkový pochod + volání nástroje)
            history_entry_request = f"{explanation}\n|||TOOL_CALL|||\n{json.dumps(tool_call_data, indent=2)}"

            if tool_name == "task_complete":
                RichPrinter.info("Agent signalizoval dokončení úkolu. Ukládám vzpomínku...")
                summary = kwargs.get("reason", "Nebylo poskytnuto žádné shrnutí.")

                # Zobrazíme finální shrnutí ve speciálním panelu v TUI
                RichPrinter.show_task_complete(summary)

                self.memory_manager.save_session(session_id, initial_task, summary)
                RichPrinter.info(f"Vzpomínka pro session {session_id} byla úspěšně uložena.")
                task_was_completed_by_agent = True # Nastavíme příznak
                break

            if tool_name == "show_last_output":
                RichPrinter.info("<<< VÝSLEDEK (Z paměti)")
                output = "V paměti není žádný předchozí dlouhý výstup."
                if self.last_full_output:
                    output = self.last_full_output
                    RichPrinter.agent_tool_output(output)
                else:
                    RichPrinter.warning(output)

                # Klíčová oprava: Přidáme plný výstup do historie, aby se přerušila smyčka
                self.history.append((history_entry_request, output))
                self.memory_manager.save_history(session_id, self.history)
                continue

            if tool_name == "reload_tools":
                RichPrinter.info("Přijat příkaz k restartování dynamického serveru nástrojů...")
                await self.mcp_client.restart_server('dynamic_tool_server.py')
                result = "Server s dynamickými nástroji byl restartován. Nové nástroje by nyní měly být k dispozici."
            else:
                result = await self.mcp_client.execute_tool(tool_name, args, kwargs, self.verbose)

            output_for_display, output_for_history = self._handle_long_output(result)

            RichPrinter.info("<<< VÝSLEDEK")
            RichPrinter.agent_tool_output(output_for_display)
            self.history.append((history_entry_request, output_for_history))
            self.memory_manager.save_history(session_id, self.history)

        if not task_was_completed_by_agent:
            final_message = f"Agent dosáhl maximálního počtu iterací ({self.max_iterations}). Úkol byl ukončen."
            RichPrinter.warning(final_message)
            # Uložíme session i v tomto případě, ale s jiným shrnutím
            summary = f"Úkol byl automaticky ukončen po dosažení limitu {self.max_iterations} iterací."
            self.memory_manager.save_session(session_id, initial_task, summary)
            RichPrinter.info(f"Vzpomínka pro session {session_id} byla uložena s poznámkou o přerušení.")
        else:
            final_message = "Agent dokončil úkol."

        RichPrinter.info(f"### {final_message} (Celkem spotřebováno: {self.total_tokens} tokenů)")


    def _handle_long_output(self, result: str) -> tuple[str, str]:
        """Zpracuje dlouhé výstupy, uloží je a vrátí shrnutí."""
        line_limit = 20
        if isinstance(result, str) and len(result.splitlines()) > line_limit:
            self.last_full_output = result
            summary = f"Výstup je příliš dlouhý ({len(result.splitlines())} řádků). Prvních {line_limit-2} řádků:\n"
            summary += "\n".join(result.splitlines()[:line_limit-2])
            summary += "\n[...]"
            summary += "\n\n(Pro zobrazení celého výstupu použijte nástroj 'show_last_output'.)"
            return summary, summary
        return result, result