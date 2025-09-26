import sys
import os
import json
import asyncio
import re
import textwrap
import google.generativeai as genai
from dotenv import load_dotenv
import yaml

# --- ANSI Color Codes for better output ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Přidání cesty k projektu pro importy
project_root_for_import = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root_for_import not in sys.path:
    sys.path.insert(0, project_root_for_import)

from core_v2.mcp_client import MCPClient
from core_v2.prompt_builder import PromptBuilder

class JulesOrchestrator:
    """
    Hlavní, refaktorovaný orchestrátor.
    Řídí hlavní smyčku a deleguje práci na specializované komponenty.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.history = []
        self.model = None
        self.verbose = False
        self.mcp_client = MCPClient(project_root=self.project_root)
        self.prompt_builder = PromptBuilder(system_prompt_path=os.path.join(self.project_root, "prompts/system_prompt.txt"))
        print(f"{Colors.GREEN}INFO: V2 Orchestrator initialized.{Colors.ENDC}")

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
            print(f"{Colors.FAIL}CHYBA: Konfigurační soubor '{config_path}' nebyl nalezen.{Colors.ENDC}")
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
            print(f"{Colors.GREEN}INFO: Klient Gemini API byl úspěšně nakonfigurován s modelem '{model_name}'.{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}VAROVÁNÍ: API klíč nebyl nalezen. Orchestrátor poběží v offline režimu.{Colors.ENDC}")

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
                print(f"{Colors.FAIL}CHYBA: Nepodařilo se zparsovat JSON z odpovědi LLM: {e}{Colors.ENDC}")
                return None
        print(f"{Colors.WARNING}VAROVÁNÍ: V odpovědi nebyly nalezeny značky pro volání nástroje.{Colors.ENDC}")
        return None

    async def run(self, initial_task: str):
        """Hlavní rozhodovací smyčka agenta."""
        print(f"\n{Colors.HEADER}--- Zahájení nového úkolu: {initial_task} ---{Colors.ENDC}")
        self.history.append(("", f"UŽIVATELSKÝ VSTUP: {initial_task}"))

        for i in range(15):
            print(f"\n{Colors.BOLD}--- Iterace č. {i+1} ---{Colors.ENDC}")

            if not self.model:
                print(f"{Colors.FAIL}CHYBA: Model není k dispozici (offline režim).{Colors.ENDC}")
                break

            tool_descriptions = await self.mcp_client.get_tool_descriptions()
            prompt = self.prompt_builder.build_prompt(tool_descriptions, self.history)

            print(f"{Colors.CYAN}INFO: Přemýšlím...{Colors.ENDC}")
            if self.verbose:
                print(f"{Colors.BLUE}--- PROMPT START ---\n{prompt}\n--- PROMPT END ---{Colors.ENDC}")

            response = await self.model.generate_content_async(prompt)

            tool_call_data = self._parse_tool_call(response.text)
            if not tool_call_data or "tool_name" not in tool_call_data:
                print(f"{Colors.FAIL}CHYBA: LLM nevrátil platné volání nástroje ve formátu JSON.{Colors.ENDC}")
                break

            tool_name = tool_call_data["tool_name"]
            args = tool_call_data.get("args", [])
            kwargs = tool_call_data.get("kwargs", {})

            tool_call_for_log = json.dumps(tool_call_data, indent=2, ensure_ascii=False)
            print(f"{Colors.HEADER}>>> AKCE:{Colors.ENDC}\n{Colors.BLUE}{tool_call_for_log}{Colors.ENDC}")

            if tool_name == "task_complete":
                print(f"\n{Colors.GREEN}INFO: Agent signalizoval dokončení úkolu.{Colors.ENDC}")
                break

            result = await self.mcp_client.execute_tool(tool_name, args, kwargs, self.verbose)

            print(f"{Colors.HEADER}<<< VÝSLEDEK:{Colors.ENDC}\n{result}")
            self.history.append((tool_call_for_log, result))

        print(f"\n{Colors.GREEN}--- Úkol dokončen ---{Colors.ENDC}")