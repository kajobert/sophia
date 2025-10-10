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

from tools import file_system
from tools import git_tools
from tools import project_tools

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
    """Hlavní asynchronní smyčka MCP serveru."""
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    # Konsolidace všech core nástrojů do jednoho serveru pro robustnost
    tools = {
        # File System Tools
        "list_files": file_system.list_files,
        "read_file": file_system.read_file,
        "create_file": file_system.create_file,
        "delete_file": file_system.delete_file,
        "rename_file": file_system.rename_file,
        "overwrite_file_with_block": file_system.overwrite_file_with_block,
        "create_file_with_block": file_system.create_file_with_block,
        "replace_with_git_merge_diff": file_system.replace_with_git_merge_diff,

        # Git Tools
        "get_git_status": git_tools.get_git_status,
        "get_git_branch_name": git_tools.get_git_branch_name,
        "add_to_git": git_tools.add_to_git,
        "create_git_commit": git_tools.create_git_commit,
        "revert_git_changes": git_tools.revert_git_changes,
        "get_last_commit_hash": git_tools.get_last_commit_hash,
        "promote_commit_to_last_known_good": git_tools.promote_commit_to_last_known_good,

        # Project Tools
        "get_project_summary": project_tools.get_project_summary,
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

                        tool_call = functools.partial(tool_func, *bound_args.args, **bound_args.kwargs)
                        result = await loop.run_in_executor(None, tool_call)
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