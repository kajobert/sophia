import sys
import os
import json
import asyncio
import time
import inspect

class MCPClient:
    """
    Klient pro správu a komunikaci s MCP servery.
    Zapouzdřuje logiku pro spouštění, ukončování a komunikaci
    se subprocesy MCP serverů.
    """
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.servers = {}
        self.tool_to_server = {}
        self.tool_definitions = []
        self.server_scripts = {} # Uloží cesty ke skriptům pro možnost restartu

    async def start_servers(self):
        """Spustí a inicializuje všechny MCP servery nalezené v adresáři mcp_servers."""
        servers_dir = os.path.join(self.project_root, "mcp_servers")
        if not os.path.isdir(servers_dir):
            from .rich_printer import RichPrinter
            RichPrinter.warning(f"Adresář MCP serverů '{servers_dir}' nebyl nalezen.")
            return

        for filename in os.listdir(servers_dir):
            if filename.endswith("_server.py"):
                script_path = os.path.join(servers_dir, filename)
                server_name = os.path.basename(script_path)
                self.server_scripts[server_name] = script_path
                await self._start_and_init_server(server_name, script_path)

    async def _start_and_init_server(self, server_name: str, script_path: str):
        """Pomocná metoda pro spuštění a inicializaci jednoho serveru."""
        from .rich_printer import RichPrinter
        # Nastavíme vyšší limit pro buffer, aby prošly i velké odpovědi nástrojů
        limit = 2 * 1024 * 1024  # 2MB
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_path,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            cwd=self.project_root,
            limit=limit
        )
        self.servers[server_name] = process
        RichPrinter.info(f"MCPClient spustil server '{server_name}' (PID: {process.pid}).")

        init_request = json.dumps({"jsonrpc": "2.0", "method": "initialize", "id": 1})
        if process.stdin:
            process.stdin.write((init_request + '\n').encode())
            await process.stdin.drain()

        # Try to read the response, with a timeout.
        try:
            response_line = await asyncio.wait_for(process.stdout.readline(), timeout=2.0)
        except asyncio.TimeoutError:
            response_line = None

        if not response_line:
            RichPrinter.error(f"Server '{server_name}' neodpověděl na inicializační požadavek v časovém limitu.")
            # Přečteme a zalogujeme případné chybové hlášky
            stderr_output = await process.stderr.read()
            if stderr_output:
                RichPrinter.error(f"Chybový výstup ze serveru '{server_name}':\n{stderr_output.decode(errors='ignore')}")
            return

        response = json.loads(response_line)
        tools = response.get('result', {}).get('capabilities', {}).get('tools', [])
        for tool in tools:
            self.tool_to_server[tool['name']] = server_name
            self.tool_definitions.append(tool)

    async def restart_server(self, server_name: str):
        """Zastaví, znovu spustí a reinicializuje specifický MCP server."""
        from .rich_printer import RichPrinter
        RichPrinter.info(f"Restartuji server '{server_name}', abych znovu načetl jeho nástroje...")

        if server_name in self.servers:
            process = self.servers[server_name]
            if process.returncode is None:
                process.terminate()
                await process.wait()
            del self.servers[server_name]

        tools_to_remove = [name for name, srv in self.tool_to_server.items() if srv == server_name]
        for tool_name in tools_to_remove:
            del self.tool_to_server[tool_name]

        self.tool_definitions = [tool for tool in self.tool_definitions if self.tool_to_server.get(tool['name']) != server_name]

        script_path = self.server_scripts.get(server_name)
        if script_path:
            await self._start_and_init_server(server_name, script_path)
            RichPrinter.info(f"Server '{server_name}' byl úspěšně restartován.")
        else:
            RichPrinter.error(f"Nelze restartovat server '{server_name}', nebyla nalezena cesta ke skriptu.")

    async def get_tool_descriptions(self) -> str:
        """Získá a zformátuje popisy všech registrovaných nástrojů."""
        if not self.tool_definitions:
            return "Žádné nástroje nejsou k dispozici."

        descriptions = []
        for tool in self.tool_definitions:
            description = tool.get('description', 'No description available.').strip()
            descriptions.append(f"- `{tool['name']}`: {description}")
        return "\n".join(descriptions)

    async def execute_tool(self, tool_name: str, args: list, kwargs: dict, verbose: bool = False) -> str:
        """Vykoná nástroj na příslušném MCP serveru."""
        from .rich_printer import RichPrinter
        server_name = self.tool_to_server.get(tool_name)
        if not server_name:
            return f"Error: Tool '{tool_name}' not registered to any server."

        server_process = self.servers[server_name]

        request_id = int(time.time() * 1000)
        mcp_request = json.dumps({
            "jsonrpc": "2.0", "method": "mcp/tool/execute",
            "params": {"name": tool_name, "args": args, "kwargs": kwargs},
            "id": request_id
        })

        if verbose:
            RichPrinter.info(f"Odesílám MCP požadavek na server '{server_name}':")
            RichPrinter.agent_tool_code(mcp_request)

        if server_process.stdin:
            server_process.stdin.write((mcp_request + '\n').encode())
            await server_process.stdin.drain()

        response_line = await server_process.stdout.readline()
        response = json.loads(response_line)

        if "error" in response:
            return f"Error from {server_name}: {response['error']['message']}"
        return str(response.get("result", {}).get("result", "No result returned."))

    async def shutdown_servers(self):
        """Bezpečně ukončí všechny spuštěné MCP servery."""
        from .rich_printer import RichPrinter
        RichPrinter.info("Ukončuji MCP servery...")
        for server_name, process in self.servers.items():
            if process.returncode is None:
                process.terminate()
                await process.wait()
                print(f"INFO: MCPClient ukončil server '{server_name}'.")