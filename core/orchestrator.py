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
        self.status_widget = status_widget

        RichPrinter.info("V2 Orchestrator initialized with LLMManager.")

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

    def _parse_llm_response(self, response_text: str) -> tuple[str | None, dict | None]:
        """
        Zparsuje odpověď LLM, aby oddělil vysvětlující text od JSONu pro volání nástroje.
        Vrací n-tici: (vysvětlující_text, data_pro_volání_nástroje).
        """
        explanation = None
        tool_call_data = None

        tool_code_match = re.search(r"<TOOL_CODE_START>(.*?)</TOOL_CODE_END>", response_text, re.DOTALL)

        if tool_code_match:
            json_str = textwrap.dedent(tool_code_match.group(1)).strip()
            try:
                tool_call_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                RichPrinter.error(f"Nepodařilo se zparsovat JSON z odpovědi LLM: {e}")
                return response_text, None # Celá odpověď je v případě chyby považována za vysvětlení

            # Vysvětlení je vše před značkou <TOOL_CODE_START>
            explanation = response_text[:tool_code_match.start()].strip()
            if not explanation:
                explanation = None
        else:
            # Nebyl nalezen žádný kód nástroje, takže celá odpověď je považována za vysvětlení.
            explanation = response_text.strip()
            # V tomto případě nevarujeme, protože odpověď bez nástroje může být legitimní (např. jen text)

        return explanation, tool_call_data

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


        for i in range(len(self.history), 15):
            tool_descriptions = await self.mcp_client.get_tool_descriptions()
            prompt = self.prompt_builder.build_prompt(tool_descriptions, self.history)

            # Fáze 1: Výběr modelu
            selected_model_name = self._triage_task_and_select_llm(prompt) # Triage na základě aktuálního promptu

            try:
                model = self.llm_manager.get_llm(selected_model_name)
                RichPrinter.info(f"Vybrán model: [bold cyan]{selected_model_name}[/bold cyan]")
            except (ValueError, FileNotFoundError) as e:
                RichPrinter.error(f"Nepodařilo se načíst model '{selected_model_name}': {e}")
                break

            # Fáze 2: Volání LLM s vybraným modelem
            # Poznámka: token_count se liší mezi providery, prozatím ho necháme pro Gemini-based modely
            token_count = 0
            if hasattr(model, 'count_tokens'):
                 token_count = model.count_tokens(prompt).total_tokens
                 self.total_tokens += token_count

            RichPrinter.info(f"### Iterace č. {i+1} | Celkem tokenů: {self.total_tokens}")
            RichPrinter.info(f"Přemýšlím... (model: {selected_model_name})")
            if token_count > 0:
                RichPrinter.info(f"Počet tokenů v tomto promptu: {token_count}")

            # Logování do TUI widgetu, pokud je k dispozici
            if self.status_widget:
                self.status_widget.add_log(f"Přemýšlím... (model: {selected_model_name})")
            else:
                # Fallback pro běh bez TUI
                RichPrinter.info(f"Přemýšlím... (model: {selected_model_name})")

            if token_count > 0:
                RichPrinter.info(f"Počet tokenů v tomto promptu: {token_count}")


            if self.verbose:
                RichPrinter.agent_markdown(f"**Prompt odeslaný do LLM:**\n\n```\n{prompt}\n```")

            # Univerzální volání modelu - prozatím předpokládáme async metodu
            # V budoucnu bude potřeba adaptér pro sjednocení API
            if hasattr(model, 'generate_content_async'):
                 response = await model.generate_content_async(prompt)
            else:
                 # Fallback pro ne-asynchronní modely (hypoteticky)
                 response = await asyncio.to_thread(model.generate_content, prompt)

            explanation, tool_call_data = self._parse_llm_response(response.text)

            if explanation:
                RichPrinter.agent_markdown(f"**Myšlenkový pochod:**\n\n{explanation}")

            if not tool_call_data or "tool_name" not in tool_call_data:
                RichPrinter.warning("LLM se rozhodl nepoužít nástroj v tomto kroku. Pokračuji v přemýšlení.")
                if explanation:
                    self.history.append((explanation, "Žádná akce."))
                    self.memory_manager.save_history(session_id, self.history)
                continue

            tool_name = tool_call_data["tool_name"]
            args = tool_call_data.get("args", [])
            kwargs = tool_call_data.get("kwargs", {})

            RichPrinter.info(">>> AKCE")
            RichPrinter.agent_tool_code(json.dumps(tool_call_data, indent=2, ensure_ascii=False))

            history_entry_request = f"{explanation}\n\n{json.dumps(tool_call_data, indent=2)}" if explanation else json.dumps(tool_call_data, indent=2)

            if tool_name == "task_complete":
                RichPrinter.info("Agent signalizoval dokončení úkolu. Ukládám vzpomínku...")
                summary = kwargs.get("reason", "Nebylo poskytnuto žádné shrnutí.")
                self.memory_manager.save_session(session_id, initial_task, summary)
                RichPrinter.info(f"Vzpomínka pro session {session_id} byla úspěšně uložena.")
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

        RichPrinter.info(f"### Úkol dokončen (Celkem spotřebováno: {self.total_tokens} tokenů)")

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