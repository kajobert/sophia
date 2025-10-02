import sys
import os
import json
import inspect
import asyncio
import importlib.util

# Dynamically add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def create_response(request_id, result):
    """Creates a standard JSON-RPC response."""
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result})

def create_error_response(request_id, code, message):
    """Creates a standard JSON-RPC error response."""
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})

def load_git_tools():
    """Loads all functions from the tools/git_tools.py module."""
    tools = {}
    tools_module_path = os.path.join(project_root, "tools", "git_tools.py")
    module_name = "tools.git_tools"

    if not os.path.exists(tools_module_path):
        print(f"Error: Git tools module not found at {tools_module_path}", file=sys.stderr)
        return tools

    try:
        spec = importlib.util.spec_from_file_location(module_name, tools_module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        for name, func in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("_"):
                tools[name] = func
    except Exception as e:
        print(f"Error loading git tools from {tools_module_path}: {e}", file=sys.stderr)

    return tools

async def main():
    """Main asynchronous loop for the Git tools MCP server."""
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    tools = load_git_tools()

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
                    doc = inspect.getdoc(func) or "No description available."
                    # Clean up the docstring for better display
                    cleaned_doc = ' '.join(doc.strip().split())
                    tool_definitions.append({
                        "name": name,
                        "description": cleaned_doc,
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
                        # Git commands are I/O bound, run in executor
                        result = await loop.run_in_executor(
                            None, tools[tool_name], *tool_args, **tool_kwargs
                        )
                        response = create_response(request_id, {"result": str(result)})
                    except Exception as e:
                        response = create_error_response(request_id, -32000, f"Tool error: {e}")
                else:
                    response = create_error_response(request_id, -32601, f"Method not found: {tool_name}")

            else:
                response = create_error_response(request_id, -32601, f"Method not found: {method}")

        except Exception as e:
            response = create_error_response(None, -32603, f"Internal error: {e}")

        if response:
            print(response)
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())