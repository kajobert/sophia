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

from core.rich_printer import RichPrinter

def inform_user(message: str) -> str:
    """
    Zobrazí uživateli informativní zprávu se zeleným označením.
    Použij pro běžná sdělení, potvrzení akcí nebo pozitivní výsledky.
    """
    RichPrinter.inform(message)
    return "Informativní zpráva byla úspěšně zobrazena uživateli."

def warn_user(message: str) -> str:
    """
    Zobrazí uživateli varování s oranžovým označením.
    Použij pro upozornění na méně závažné problémy, které nevyžadují okamžitý zásah.
    """
    RichPrinter.warning(message)
    return "Varovná zpráva byla úspěšně zobrazena uživateli."

def error_user(message: str) -> str:
    """
    Zobrazí uživateli chybovou hlášku s červeným označením.
    Použij pro informování o závažných chybách, selhání operací nebo problémech.
    """
    RichPrinter.error(message)
    return "Chybová hláška byla úspěšně zobrazena uživateli."

def ask_user(question: str) -> str:
    """
    Položí uživateli otázku a počká na jeho odpověď.
    Tento nástroj by se měl používat střídmě, pouze když je interakce nezbytná.
    Systém automaticky zpracuje odpověď, nemusíš na ni čekat.
    """
    RichPrinter.ask(question)
    return "Otázka byla položena uživateli. Jeho odpověď bude poskytnuta v dalším kroku."

def display_code(code: str, language: str = "python") -> str:
    """
    Zobrazí uživateli formátovaný blok kódu se zvýrazněním syntaxe.
    """
    RichPrinter.code(code, language)
    return "Blok kódu byl úspěšně zobrazen."

def display_table(title: str, headers: list[str], rows: list[list[str]]) -> str:
    """
    Zobrazí uživateli přehlednou tabulku s daty.
    """
    RichPrinter.table(title, headers, rows)
    return "Tabulka byla úspěšně zobrazena."

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