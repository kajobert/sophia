import sys
import os
import json
import asyncio
import re
import time
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
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.system_prompt import SYSTEM_PROMPT

class JulesOrchestrator:
    """
    Finální, asynchronní orchestrátor, který řídí agenta a komunikuje s LLM.
    """

    def __init__(self):
        self.servers = {}
        self.tool_to_server = {}
        self.tool_descriptions = ""
        self.history = []
        self.model = None
        self.system_prompt = SYSTEM_PROMPT
        print(f"{Colors.GREEN}INFO: Asynchronous Orchestrator initialized.{Colors.ENDC}")

    async def initialize(self):
        """Provede kompletní inicializaci - konfigurace, API, spuštění serverů."""
        self._load_config()
        self._configure_api()
        await self.start_servers()

    def _load_config(self):
        """Načte konfiguraci z config.yaml."""
        try:
            with open("config.yaml", "r") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"{Colors.FAIL}CHYBA: Konfigurační soubor 'config.yaml' nebyl nalezen.{Colors.ENDC}")
            self.config = {} # Fallback na prázdnou konfiguraci

    def _configure_api(self):
        """Nakonfiguruje Gemini API klienta z .env souboru."""
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key and api_key != "VASE_GOOGLE_API_KLIC_ZDE":
            genai.configure(api_key=api_key)
            model_name = self.config.get("llm_models", {}).get("primary_llm", {}).get("model_name", "gemini-pro")
            self.model = genai.GenerativeModel(model_name)
            print(f"{Colors.GREEN}INFO: Klient Gemini API byl úspěšně nakonfigurován s modelem '{model_name}'.{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}VAROVÁNÍ: API klíč nebyl nalezen nebo je neplatný. Orchestrátor poběží v offline režimu.{Colors.ENDC}")

    async def start_servers(self):
        """Spustí a inicializuje všechny definované MCP servery."""
        print(f"{Colors.BLUE}INFO: Spouštím MCP servery...{Colors.ENDC}")
        server_scripts = [
            "mcp_servers/file_system_server.py",
            "mcp_servers/shell_server.py",
            "mcp_servers/control_server.py"
        ]
        all_descriptions = []

        for script_path in server_scripts:
            server_name = os.path.basename(script_path)
            process = await asyncio.create_subprocess_exec(
                sys.executable, script_path,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            self.servers[server_name] = process
            print(f"INFO: Server '{server_name}' spuštěn (PID: {process.pid}).")

            init_request = json.dumps({"jsonrpc": "2.0", "method": "initialize", "id": 1})
            process.stdin.write((init_request + '\n').encode())
            await process.stdin.drain()

            response_line = await process.stdout.readline()
            response = json.loads(response_line)

            tools = response.get('result', {}).get('capabilities', {}).get('tools', [])
            for tool in tools:
                self.tool_to_server[tool['name']] = server_name
                all_descriptions.append(f"- `{tool['name']}`: {tool['description'].strip()}")

        self.tool_descriptions = "\n".join(all_descriptions)
        print(f"{Colors.GREEN}INFO: Všechny MCP servery byly inicializovány a nástroje zaregistrovány.{Colors.ENDC}")

    async def shutdown_servers(self):
        """Bezpečně ukončí všechny spuštěné MCP servery."""
        print(f"{Colors.BLUE}INFO: Ukončuji MCP servery...{Colors.ENDC}")
        for server_name, process in self.servers.items():
            if process.returncode is None:
                process.terminate()
                await process.wait()
                print(f"INFO: Server '{server_name}' byl úspěšně ukončen.")

    def _build_prompt(self):
        """Sestaví kompletní prompt pro LLM."""
        prompt_parts = [
            self.system_prompt,
            "\n# **DOSTUPNÉ NÁSTROJE**\n",
            self.tool_descriptions,
            "\n# **HISTORIE AKTUÁLNÍHO ÚKOLU**\n"
        ]
        if not self.history:
            prompt_parts.append("Zatím nebyla provedena žádná akce. Toto je první krok.\n")
        else:
            for action, result in self.history:
                prompt_parts.append(f"## Akce:\n<TOOL_CODE_START>\n{action}\n</TOOL_CODE_END>\n")
                prompt_parts.append(f"## Výsledek:\n<TOOL_OUTPUT>\n{result}\n</TOOL_OUTPUT>\n")

        prompt_parts.append("\n# **FINÁLNÍ INSTRUKCE**\n")
        prompt_parts.append("Analyzuj historii a navrhni další krok jako JEDNO volání nástroje v požadovaném formátu.")
        return "".join(prompt_parts)

    def _parse_tool_call(self, response_text: str):
        """Zparsuje odpověď od LLM a extrahuje volání nástroje."""
        match = re.search(r"<TOOL_CODE_START>(.*?)</TOOL_CODE_END>", response_text, re.DOTALL)
        if match:
            code_block = match.group(1)
            return textwrap.dedent(code_block).strip()
        print(f"{Colors.WARNING}VAROVÁNÍ: V odpovědi nebyly nalezeny značky pro volání nástroje.{Colors.ENDC}")
        return None

    async def _execute_tool(self, tool_call_string: str):
        """Asynchronně vykoná volání nástroje přes MCP."""
        tool_name_match = re.match(r"(\w+)", tool_call_string)
        if not tool_name_match: return "Error: Could not parse tool name."

        tool_name = tool_name_match.group(1)
        server_name = self.tool_to_server.get(tool_name)
        if not server_name: return f"Error: Tool '{tool_name}' not registered."

        server_process = self.servers[server_name]

        args_match = re.search(r"\((.*)\)", tool_call_string, re.DOTALL)
        args = []
        if args_match:
            args_string = args_match.group(1).strip()
            if args_string: args = [arg.strip().strip("'\"") for arg in args_string.split(',')]
        else:
            args = [line.strip() for line in tool_call_string.split('\n')[1:]]

        request_id = int(time.time() * 1000)
        mcp_request = json.dumps({
            "jsonrpc": "2.0", "method": "mcp/tool/execute",
            "params": {"name": tool_name, "arguments": args}, "id": request_id
        })

        server_process.stdin.write((mcp_request + '\n').encode())
        await server_process.stdin.drain()

        response_line = await server_process.stdout.readline()
        response = json.loads(response_line)

        if "error" in response: return f"Error from {server_name}: {response['error']['message']}"
        return str(response.get("result", {}).get("result", "No result."))

    async def run(self, initial_task: str):
        """Hlavní rozhodovací smyčka agenta."""
        print(f"\n{Colors.HEADER}--- Zahájení nového úkolu: {initial_task} ---{Colors.ENDC}")
        self.history.append(("", f"UŽIVATELSKÝ VSTUP: {initial_task}"))

        for i in range(15):
            print(f"\n{Colors.BOLD}--- Iterace č. {i+1} ---{Colors.ENDC}")

            if not self.model:
                print(f"{Colors.FAIL}CHYBA: Model není k dispozici (offline režim). Ukončuji běh.{Colors.ENDC}")
                break

            prompt = self._build_prompt()

            print(f"{Colors.CYAN}INFO: Přemýšlím a odesílám prompt do Gemini API...{Colors.ENDC}")
            response = await self.model.generate_content_async(prompt)

            tool_call = self._parse_tool_call(response.text)
            if not tool_call:
                print(f"{Colors.FAIL}CHYBA: LLM nevrátil platné volání nástroje. Ukončuji.{Colors.ENDC}")
                break

            print(f"{Colors.HEADER}>>> AKCE:{Colors.ENDC}")
            print(f"{Colors.BLUE}{tool_call}{Colors.ENDC}")

            if tool_call.startswith("task_complete"):
                print(f"\n{Colors.GREEN}INFO: Agent signalizoval dokončení úkolu.{Colors.ENDC}")
                break

            result = await self._execute_tool(tool_call)

            print(f"{Colors.HEADER}<<< VÝSLEDEK:{Colors.ENDC}")
            print(f"{result}")
            self.history.append((tool_call, result))

        print(f"\n{Colors.GREEN}--- Úkol dokončen ---{Colors.ENDC}")