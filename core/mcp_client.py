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

    async def start_servers(self):
        """Spustí a inicializuje všechny MCP servery nalezené v adresáři mcp_servers."""
        servers_dir = os.path.join(self.project_root, "mcp_servers")
        if not os.path.isdir(servers_dir):
            print(f"VAROVÁNÍ: Adresář MCP serverů '{servers_dir}' nebyl nalezen.")
            return

        for filename in os.listdir(servers_dir):
            if filename.endswith("_server.py"):
                script_path = os.path.join(servers_dir, filename)
                server_name = os.path.basename(script_path)

                process = await asyncio.create_subprocess_exec(
                    sys.executable, script_path,
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    cwd=self.project_root
                )
                self.servers[server_name] = process
                print(f"INFO: MCPClient spustil server '{server_name}' (PID: {process.pid}).")

                init_request = json.dumps({"jsonrpc": "2.0", "method": "initialize", "id": 1})
                process.stdin.write((init_request + '\n').encode())
                await process.stdin.drain()

                # Krátké zpoždění, aby měl server čas nastartovat a odpovědět
                await asyncio.sleep(0.2)

                response_line = await process.stdout.readline()

                if not response_line:
                    print(f"CHYBA: Server '{server_name}' neodpověděl na inicializační požadavek.")
                    continue

                response = json.loads(response_line)

                tools = response.get('result', {}).get('capabilities', {}).get('tools', [])
                for tool in tools:
                    self.tool_to_server[tool['name']] = server_name
                    self.tool_definitions.append(tool)

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
        # Tento import je zde, aby se zabránilo cyklické závislosti na startu
        from .rich_printer import RichPrinter

        server_name = self.tool_to_server.get(tool_name)
        if not server_name:
            return f"Error: Tool '{tool_name}' not registered to any server."

        server_process = self.servers[server_name]

        request_id = int(time.time() * 1000)
        mcp_request = json.dumps({
            "jsonrpc": "2.0", "method": "mcp/tool/execute",
            "params": {
                "name": tool_name,
                "args": args,
                "kwargs": kwargs
            },
            "id": request_id
        })

        if verbose:
            RichPrinter.print_info(f"Odesílám MCP požadavek na server '{server_name}':")
            RichPrinter.print_code(mcp_request, "json")

        server_process.stdin.write((mcp_request + '\n').encode())
        await server_process.stdin.drain()

        response_line = await server_process.stdout.readline()
        response = json.loads(response_line)

        if "error" in response:
            return f"Error from {server_name}: {response['error']['message']}"
        return str(response.get("result", {}).get("result", "No result returned."))

    async def shutdown_servers(self):
        """Bezpečně ukončí všechny spuštěné MCP servery."""
        for server_name, process in self.servers.items():
            if process.returncode is None:
                process.terminate()
                await process.wait()
                print(f"INFO: MCPClient ukončil server '{server_name}'.")