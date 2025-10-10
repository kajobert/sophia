import sys
import os
import json
import inspect
import asyncio
import functools

from tools import control

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
    """Hlavní asynchronní smyčka MCP serveru pro kontrolní nástroje."""
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    tools = {
        "task_complete": control.task_complete,
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
                    tool_func = tools[tool_name]
                    try:
                        # Inteligentní spojení args a kwargs do jednoho volání
                        sig = inspect.signature(tool_func)
                        bound_args = sig.bind(*tool_args, **tool_kwargs)
                        bound_args.apply_defaults()

                        # Ponecháme speciální logiku pro task_complete, pokud je stále relevantní
                        if tool_name == "task_complete":
                             summary = bound_args.arguments.get('reason', "Nebylo poskytnuto žádné shrnutí.")
                             result = await loop.run_in_executor(None, functools.partial(tool_func, reason=summary))
                        else:
                             result = await loop.run_in_executor(None, functools.partial(tool_func, *bound_args.args, **bound_args.kwargs))

                        response = create_response(request_id, {"result": str(result)})
                    except (TypeError, Exception) as e:
                        response = create_error_response(request_id, -32000, f"Tool error for {tool_name}: {e}")
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