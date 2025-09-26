import sys
import os
import json
import asyncio
import re
import textwrap
import google.generativeai as genai
from dotenv import load_dotenv
import yaml

# Přidání cesty k projektu pro importy, pokud ještě není
project_root_for_import = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root_for_import not in sys.path:
    sys.path.insert(0, project_root_for_import)

from core.mcp_client import MCPClient
from core.prompt_builder import PromptBuilder
from core.rich_printer import RichPrinter

class JulesOrchestrator:
    """
    Finální, asynchronní orchestrátor, který řídí agenta a komunikuje s LLM.
    Využívá RichPrinter pro přehledný výstup a podporuje sbalitelné logy.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.history = []
        self.model = None
        self.verbose = False
        self.last_full_output = None
        self.mcp_client = MCPClient(project_root=self.project_root)
        self.prompt_builder = PromptBuilder(system_prompt_path=os.path.join(self.project_root, "prompts/system_prompt.txt"))
        RichPrinter.print_info("V2 Orchestrator initialized.")

    async def initialize(self):
        """Provede kompletní inicializaci."""
        self._load_config()
        self._configure_api()
        await self.mcp_client.start_servers()

    def _load_config(self):
        """Načte konfiguraci z config.yaml."""
        config_path = os.path.join(self.project_root, "config.yaml")
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            RichPrinter.print_error(f"Konfigurační soubor '{config_path}' nebyl nalezen.")
            self.config = {}

    def _configure_api(self):
        """Nakonfiguruje Gemini API klienta."""
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

    def _parse_tool_call(self, response_text: str) -> dict | None:
        """Zparsuje odpověď od LLM a extrahuje JSON objekt volání nástroje."""
        match = re.search(r"<TOOL_CODE_START>(.*?)</TOOL_CODE_END>", response_text, re.DOTALL)
        if match:
            json_str = textwrap.dedent(match.group(1)).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                RichPrinter.print_error(f"Nepodařilo se zparsovat JSON z odpovědi LLM: {e}")
                return None
        RichPrinter.print_warning("V odpovědi nebyly nalezeny značky pro volání nástroje.")
        return None

    async def run(self, initial_task: str):
        """Hlavní rozhodovací smyčka agenta."""
        RichPrinter.print_header(f"Zahájení nového úkolu: {initial_task}")
        self.history.append(("", f"UŽIVATELSKÝ VSTUP: {initial_task}"))

        for i in range(15):
            RichPrinter.print_header(f"Iterace č. {i+1}", style="bold blue")

            if not self.model:
                RichPrinter.print_error("Model není k dispozici (offline režim). Ukončuji běh.")
                break

            tool_descriptions = await self.mcp_client.get_tool_descriptions()
            prompt = self.prompt_builder.build_prompt(tool_descriptions, self.history)

            RichPrinter.print_info("Přemýšlím...")
            if self.verbose:
                RichPrinter.print_panel(prompt, title="Prompt odeslaný do LLM")

            response = await self.model.generate_content_async(prompt)

            tool_call_data = self._parse_tool_call(response.text)
            if not tool_call_data or "tool_name" not in tool_call_data:
                RichPrinter.print_error("LLM nevrátil platné volání nástroje ve formátu JSON.")
                break

            tool_name = tool_call_data["tool_name"]
            args = tool_call_data.get("args", [])
            kwargs = tool_call_data.get("kwargs", {})

            RichPrinter.print_subheader(">>> AKCE")
            RichPrinter.print_code(json.dumps(tool_call_data, indent=2, ensure_ascii=False), language="json")

            if tool_name == "task_complete":
                RichPrinter.print_info("Agent signalizoval dokončení úkolu.")
                break

            if tool_name == "show_last_output":
                RichPrinter.print_subheader("<<< VÝSLEDEK (Z paměti)")
                if self.last_full_output:
                    RichPrinter.print_panel(self.last_full_output, title="Poslední úplný výstup")
                else:
                    RichPrinter.print_warning("V paměti není žádný předchozí dlouhý výstup.")
                continue

            result = await self.mcp_client.execute_tool(tool_name, args, kwargs, self.verbose)

            output_for_display, output_for_history = self._handle_long_output(result)

            RichPrinter.print_subheader("<<< VÝSLEDEK")
            RichPrinter.print_panel(output_for_display, title="Výstup nástroje", border_style="green")
            self.history.append((json.dumps(tool_call_data, indent=2), output_for_history))

        RichPrinter.print_header("Úkol dokončen", style="bold green")

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