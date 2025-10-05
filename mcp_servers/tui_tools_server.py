import sys
import os
import json
import inspect
import asyncio
import functools

# Přidání cesty k projektu pro importy, aby bylo možné najít core moduly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# RichPrinter se zde již nepoužívá, volání se přesouvá do orchestratoru

def inform_user(message: str) -> str:
    """
    Pošle informativní zprávu do TUI.
    Vrací JSON pro zpracování v orchestratoru.
    """
    return json.dumps({"display": "inform", "content": message})

def warn_user(message: str) -> str:
    """
    Pošle varovnou zprávu do TUI.
    Vrací JSON pro zpracování v orchestratoru.
    """
    return json.dumps({"display": "warning", "content": message})

def error_user(message: str) -> str:
    """
    Pošle chybovou zprávu do TUI.
    Vrací JSON pro zpracování v orchestratoru.
    """
    return json.dumps({"display": "error", "content": message})

def ask_user(question: str) -> str:
    """
    Položí otázku v TUI.
    Vrací JSON pro zpracování v orchestratoru.
    """
    return json.dumps({"display": "ask", "content": question})

def display_code(code: str, language: str = "python") -> str:
    """
    Pošle blok kódu pro zobrazení v TUI.
    Vrací JSON pro zpracování v orchestratoru.
    """
    content = {"code": code, "language": language}
    return json.dumps({"display": "code", "content": content})

def display_table(title: str, headers: list[str], rows: list[list[str]]) -> str:
    """
    Pošle data pro zobrazení tabulky v TUI.
    Vrací JSON pro zpracování v orchestratoru.
    """
    content = {"title": title, "headers": headers, "rows": rows}
    return json.dumps({"display": "table", "content": content})

# --- MCP Server Boilerplate ---

def create_response(request_id, result):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result})

def create_error_response(request_id, code, message):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})

async def main():
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    tools = {
        "inform_user": inform_user,
        "warn_user": warn_user,
        "error_user": error_user,
        "ask_user": ask_user,
        "display_code": display_code,
        "display_table": display_table,
    }

    while True:
        line = await reader.readline()
        if not line: break
        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            response = None

            if method == "initialize":
                tool_definitions = [{"name": name, "description": inspect.getdoc(func) or ""} for name, func in tools.items()]
                response = create_response(request_id, {"capabilities": {"tools": tool_definitions}})

            elif method == "mcp/tool/execute":
                params = request.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("args", [])
                tool_kwargs = params.get("kwargs", {})

                if tool_name in tools:
                    try:
                        tool_call = functools.partial(tools[tool_name], *tool_args, **tool_kwargs)
                        result = await loop.run_in_executor(None, tool_call)
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