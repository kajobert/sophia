import sys
import os
import json
import asyncio
import re
import textwrap
import uuid
import google.generativeai as genai
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

class JulesOrchestrator:
    """
    Finální, asynchronní orchestrátor, který řídí agenta, komunikuje s LLM
    a ukládá své zkušenosti do perzistentní paměti.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.history = []
        self.model = None
        self.verbose = False
        self.last_full_output = None
        self.total_tokens = 0
        self.mcp_client = MCPClient(project_root=self.project_root)
        self.prompt_builder = PromptBuilder(system_prompt_path=os.path.join(self.project_root, "prompts/system_prompt.txt"))
        self.memory_manager = MemoryManager()
        RichPrinter.print_info("V2 Orchestrator initialized with MemoryManager.")

    async def initialize(self):
        """Provede kompletní inicializaci."""
        self._load_config()
        self._configure_api()
        await self.mcp_client.start_servers()

    def _load_config(self):
        config_path = os.path.join(self.project_root, "config.yaml")
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            RichPrinter.print_error(f"Konfigurační soubor '{config_path}' nebyl nalezen.")
            self.config = {}

    def _configure_api(self):
        dotenv_path = os.path.join(self.project_root, '.env')
        load_dotenv(dotenv_path=dotenv_path)
        api_key = os.getenv("GEMINI_API_KEY")

        llm_config = self.config.get("llm_models", {}).get("primary_llm", {})
        self.verbose = llm_config.get("verbose", False)
        model_name = llm_config.get("model_name", "models/gemini-pro-latest")

        if api_key and api_key != "VASE_GOOGLE_API_KLIC_ZDE":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            RichPrinter.print_info(f"Klient Gemini API byl úspěšně nakonfigurován s modelem '{model_name}'.")
        else:
            RichPrinter.print_warning("API klíč nebyl nalezen nebo je neplatný. Orchestrátor poběží v offline režimu.")

    async def shutdown(self):
        """Bezpečně ukončí všechny spuštěné služby."""
        await self.mcp_client.shutdown_servers()
        self.memory_manager.close()
        RichPrinter.print_info("Všechny služby byly bezpečně ukončeny.")

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
                RichPrinter.print_error(f"Nepodařilo se zparsovat JSON z odpovědi LLM: {e}")
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
            RichPrinter.print_header(f"Obnovuji sezení: {session_id}")
            loaded_history = self.memory_manager.load_history(session_id)
            if loaded_history:
                self.history = loaded_history
                RichPrinter.print_info(f"Historie pro sezení '{session_id}' byla úspěšně načtena ({len(self.history)} kroků).")
            else:
                RichPrinter.print_warning(f"Pro sezení '{session_id}' nebyla nalezena žádná historie. Vytvářím nové sezení.")
                session_id = str(uuid.uuid4()) # Vytvoříme nové ID, pokud staré nebylo nalezeno
        else:
            session_id = str(uuid.uuid4())
            RichPrinter.print_header(f"Zahájení nového sezení (ID: {session_id})")

        RichPrinter.print_info(f"Úkol: {initial_task}")
        self.history.append(("", f"UŽIVATELSKÝ VSTUP: {initial_task}"))
        self.memory_manager.save_history(session_id, self.history)


        for i in range(len(self.history), 15):
            if not self.model:
                RichPrinter.print_error("Model není k dispozici (offline režim). Ukončuji běh.")
                break

            tool_descriptions = await self.mcp_client.get_tool_descriptions()
            prompt = self.prompt_builder.build_prompt(tool_descriptions, self.history)

            token_count = self.model.count_tokens(prompt).total_tokens
            self.total_tokens += token_count

            RichPrinter.print_header(f"Iterace č. {i+1} | Celkem tokenů: {self.total_tokens}", style="bold blue")

            RichPrinter.print_info("Přemýšlím...")
            RichPrinter.print_info(f"Počet tokenů v tomto promptu: {token_count}")

            if self.verbose:
                RichPrinter.print_panel(prompt, title="Prompt odeslaný do LLM")

            response = await self.model.generate_content_async(prompt)

            explanation, tool_call_data = self._parse_llm_response(response.text)

            if explanation:
                RichPrinter.print_markdown(explanation, title="Myšlenkový pochod")

            if not tool_call_data or "tool_name" not in tool_call_data:
                RichPrinter.print_warning("LLM se rozhodl nepoužít nástroj v tomto kroku. Pokračuji v přemýšlení.")
                if explanation:
                    self.history.append((explanation, "Žádná akce."))
                    self.memory_manager.save_history(session_id, self.history)
                continue

            tool_name = tool_call_data["tool_name"]
            args = tool_call_data.get("args", [])
            kwargs = tool_call_data.get("kwargs", {})

            RichPrinter.print_subheader(">>> AKCE")
            RichPrinter.print_code(json.dumps(tool_call_data, indent=2, ensure_ascii=False), language="json")

            history_entry_request = f"{explanation}\n\n{json.dumps(tool_call_data, indent=2)}" if explanation else json.dumps(tool_call_data, indent=2)

            if tool_name == "task_complete":
                RichPrinter.print_info("Agent signalizoval dokončení úkolu. Ukládám vzpomínku...")
                summary = kwargs.get("reason", "Nebylo poskytnuto žádné shrnutí.")
                self.memory_manager.save_session(session_id, initial_task, summary)
                RichPrinter.print_info(f"Vzpomínka pro session {session_id} byla úspěšně uložena.")
                break

            if tool_name == "show_last_output":
                RichPrinter.print_subheader("<<< VÝSLEDEK (Z paměti)")
                if self.last_full_output:
                    RichPrinter.print_panel(self.last_full_output, title="Poslední úplný výstup")
                else:
                    RichPrinter.print_warning("V paměti není žádný předchozí dlouhý výstup.")
                continue

            if tool_name == "reload_tools":
                RichPrinter.print_info("Přijat příkaz k restartování dynamického serveru nástrojů...")
                await self.mcp_client.restart_server('dynamic_tool_server.py')
                result = "Server s dynamickými nástroji byl restartován. Nové nástroje by nyní měly být k dispozici."
            else:
                result = await self.mcp_client.execute_tool(tool_name, args, kwargs, self.verbose)

            output_for_display, output_for_history = self._handle_long_output(result)

            RichPrinter.print_subheader("<<< VÝSLEDEK")
            RichPrinter.print_panel(output_for_display, title="Výstup nástroje", border_style="green")
            self.history.append((history_entry_request, output_for_history))
            self.memory_manager.save_history(session_id, self.history)

        RichPrinter.print_header(f"Úkol dokončen (Celkem spotřebováno: {self.total_tokens} tokenů)", style="bold green")

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