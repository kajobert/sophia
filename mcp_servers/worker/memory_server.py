import sys
import os
import json
import inspect
import asyncio
import functools

# Dynamické přidání kořenového adresáře projektu do sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools import memory_tools

def create_response(request_id, result):
    """Vytvoří standardní JSON-RPC odpověď."""
    return json.dumps({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    })

def create_error_response(request_id, code, message):
    """Vytvoří standardní JSON-RPC chybovou odpověď."""
    return json.dumps({
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message}
    })

async def main():
    """Hlavní asynchronní smyčka MCP serveru pro paměťové nástroje."""
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    tools = {
        "recall_past_tasks": memory_tools.recall_past_tasks,
    }

    while True:
        line = await reader.readline()
        if not line:
            break

        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            response = None

            if method == "initialize":
                tool_definitions = []
                for name, func in tools.items():
                    tool_definitions.append({
                        "name": name,
                        "description": inspect.getdoc(func) or "No description.",
                    })
                response_data = {"capabilities": {"tools": tool_definitions}}
                response = create_response(request_id, response_data)

            elif method == "mcp/tool/execute":
                params = request.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("args", [])
                tool_kwargs = params.get("kwargs", {})

                if tool_name in tools:
                    try:
                        # Vytvoříme parciální funkci, která zapouzdří funkci i její argumenty
                        func_to_run = functools.partial(tools[tool_name], *tool_args, **tool_kwargs)
                        result = await loop.run_in_executor(
                            None, func_to_run
                        )
                        response = create_response(request_id, {"result": str(result)})
                    except Exception as e:
                        response = create_error_response(request_id, -32000, f"Tool error: {e}")
                else:
                    response = create_error_response(request_id, -32601, f"Method not found: {tool_name}")

            else:
                response = create_error_response(request_id, -32601, "Method not found")

        except Exception as e:
            response = create_error_response(None, -32603, f"Internal error: {e}")

        if response:
            print(response)
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())