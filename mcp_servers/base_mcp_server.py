import sys
import json
import asyncio
import inspect

class BaseMCPServer:
    """
    Base class for all MCP (Multi-Capability Protocol) servers.
    Handles the JSON-RPC 2.0 communication loop.
    """
    def __init__(self):
        self.tools = []

    def add_tool(self, name, function, description):
        """Registers a tool to be exposed by this server."""
        self.tools.append({
            "name": name,
            "function": function,
            "description": description,
            "parameters": self._get_tool_parameters(function)
        })

    def _get_tool_parameters(self, function):
        """Extracts parameter information from a function signature."""
        try:
            return [
                {"name": name, "type": str(param.annotation), "required": param.default == inspect.Parameter.empty}
                for name, param in inspect.signature(function).parameters.items()
                if name != 'self'
            ]
        except (ValueError, TypeError):
            return [] # Cannot inspect signature

    def get_capabilities(self):
        """Returns the list of tools this server provides."""
        return {
            "tools": [{k: v for k, v in tool.items() if k != 'function'} for tool in self.tools]
        }

    async def handle_request(self, request_data):
        """Handles a single JSON-RPC request."""
        try:
            request = json.loads(request_data)
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if method == "initialize":
                response = {"jsonrpc": "2.0", "result": {"capabilities": self.get_capabilities()}, "id": request_id}
            elif method == "mcp/tool/execute":
                tool_name = params.get("name")
                tool = next((t for t in self.tools if t["name"] == tool_name), None)
                if tool:
                    args = params.get("args", [])
                    kwargs = params.get("kwargs", {})
                    result = await self._execute_tool_function(tool["function"], args, kwargs)
                    response = {"jsonrpc": "2.0", "result": {"result": result}, "id": request_id}
                else:
                    response = {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": request_id}
            else:
                response = {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": request_id}

        except json.JSONDecodeError:
            response = {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}
        except Exception as e:
            response = {"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Internal error: {e}"}, "id": request_id}

        return json.dumps(response)

    async def _execute_tool_function(self, func, args, kwargs):
        """Executes the tool function, handling both sync and async methods."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # To avoid blocking the event loop, run sync functions in a thread pool executor
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def _run_loop(self):
        """The main communication loop, reading from stdin and writing to stdout."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_running_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        writer = asyncio.StreamWriter(
            transport=await asyncio.get_running_loop().connect_write_pipe(asyncio.Protocol, sys.stdout),
            protocol=asyncio.Protocol(),
            reader=None,
            loop=asyncio.get_running_loop()
        )

        while not reader.at_eof():
            request_data = await reader.readline()
            if not request_data:
                break
            response_json = await self.handle_request(request_data.decode())
            writer.write((response_json + '\n').encode())
            await writer.drain()

    def run(self):
        """Starts the server's event loop."""
        try:
            asyncio.run(self._run_loop())
        except KeyboardInterrupt:
            pass # Exit gracefully on Ctrl+C