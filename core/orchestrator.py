import sys
import os
import json
import asyncio
import re
import time

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class JulesOrchestrator:
    """
    Hlavní asynchronní třída pro orchestraci AI agenta Julese.
    Funguje jako MCP Host, spouští a spravuje MCP servery pro nástroje.
    """

    def __init__(self):
        self.servers = {}
        self.tool_to_server = {}
        self.tool_descriptions = ""
        print("INFO: Asynchronous Orchestrator initialized.")

    async def start_servers(self):
        """Spustí a inicializuje všechny definované MCP servery."""
        print("INFO: Spouštím MCP servery...")
        server_scripts = [
            "mcp_servers/file_system_server.py",
            "mcp_servers/shell_server.py"
        ]
        all_descriptions = []

        for script_path in server_scripts:
            server_name = os.path.basename(script_path)

            process = await asyncio.create_subprocess_exec(
                sys.executable, script_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
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
        print("INFO: Všechny MCP servery byly inicializovány a nástroje zaregistrovány.")

    async def shutdown_servers(self):
        """Bezpečně ukončí všechny spuštěné MCP servery."""
        print("INFO: Ukončuji MCP servery...")
        for server_name, process in self.servers.items():
            if process.returncode is None:
                process.terminate()
                await process.wait()
                print(f"INFO: Server '{server_name}' byl úspěšně ukončen.")

    async def execute_tool(self, tool_call_string: str) -> str:
        """Najde správný MCP server, pošle mu požadavek a vrátí výsledek."""
        tool_name_match = re.match(r"(\w+)", tool_call_string)
        if not tool_name_match:
            return "Error: Could not parse tool name."

        tool_name = tool_name_match.group(1)
        server_name = self.tool_to_server.get(tool_name)
        if not server_name:
            return f"Error: Tool '{tool_name}' not registered."

        server_process = self.servers[server_name]

        args_match = re.search(r"\((.*)\)", tool_call_string, re.DOTALL)
        args = []
        if args_match:
            args_string = args_match.group(1).strip()
            if args_string:
                args = [arg.strip().strip("'\"") for arg in args_string.split(',')]

        request_id = int(time.time() * 1000)
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "mcp/tool/execute",
            "params": {"name": tool_name, "arguments": args},
            "id": request_id
        }

        server_process.stdin.write((json.dumps(mcp_request) + '\n').encode())
        await server_process.stdin.drain()

        response_line = await server_process.stdout.readline()
        response = json.loads(response_line)

        if "error" in response:
            return f"Error from {server_name}: {response['error']['message']}"
        return str(response.get("result", {}).get("result", "No result."))

    async def run_task(self, task: str):
        """Simuluje běh jednoho úkolu."""
        print(f"\n--- Spouštím úkol: {task} ---")

        # Simulace LLM, který vygeneruje volání nástroje
        simulated_tool_call = ""
        if "list files" in task.lower():
            simulated_tool_call = "list_files('.')"
        else:
            return "INFO: Pro tento úkol nebyla nalezena žádná simulovaná akce."

        print(f"INFO: Simulované volání nástroje: {simulated_tool_call}")
        result = await self.execute_tool(simulated_tool_call)

        print("\n--- Výsledek akce ---")
        print(result)
        print("---------------------")
        return result