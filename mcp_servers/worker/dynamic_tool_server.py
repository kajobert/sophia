import sys
import os
import json
import inspect
import asyncio
import importlib.util

# Dynamické přidání kořenového adresáře projektu do sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def create_response(request_id, result):
    """Vytvoří standardní JSON-RPC odpověď."""
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result})

def create_error_response(request_id, code, message):
    """Vytvoří standardní JSON-RPC chybovou odpověď."""
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})

def load_dynamic_tools():
    """Dynamicky načte všechny nástroje z adresáře sandbox/custom_tools."""
    tools = {}
    custom_tools_dir = os.path.join(project_root, "sandbox", "custom_tools")
    if not os.path.isdir(custom_tools_dir):
        return tools

    for filename in os.listdir(custom_tools_dir):
        if filename.endswith(".py"):
            module_name = f"custom_tools.{filename[:-3]}"
            filepath = os.path.join(custom_tools_dir, filename)

            try:
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                module = importlib.util.module_from_spec(spec)
                # Přidání do sys.modules, aby fungovaly případné další importy v nástroji
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                for name, func in inspect.getmembers(module, inspect.isfunction):
                    if not name.startswith("_"):
                        tools[name] = func
            except Exception as e:
                # V případě chyby logujeme, ale nepadáme
                print(f"Error loading dynamic tool from {filename}: {e}", file=sys.stderr)
    return tools

async def main():
    """Hlavní asynchronní smyčka pro dynamický MCP server."""
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    tools = load_dynamic_tools()

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

                        result = await loop.run_in_executor(None, tool_func, *bound_args.args, **bound_args.kwargs)
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