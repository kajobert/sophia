"""
MCP Server pro nástroje zaměřené na hloubkovou analýzu a debugování kódu.
"""
import sys
import os
import subprocess
import shlex
import shutil
import json
import inspect
import asyncio
import functools

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Nástroje ---

def _run_command(command: list[str]) -> str:
    """Pomocná funkce pro spouštění příkazů a vracení jejich výstupu."""
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        env = os.environ.copy()
        env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')

        result = subprocess.run(
            command, capture_output=True, text=True, cwd=project_root, check=False, env=env
        )
        # Pylint vrací různé nenulové kódy pro různé typy nalezených problémů,
        # ale my chceme výstup vždy, pokud se příkaz úspěšně spustil.
        if result.returncode != 0 and "Your code has been rated at" not in result.stdout:
             return f"Error running command: {' '.join(command)}\nExit Code: {result.returncode}\nStderr:\n{result.stderr}\nStdout:\n{result.stdout}"
        return result.stdout or result.stderr
    except FileNotFoundError:
        return f"Error: Command not found: '{command[0]}'. Make sure the required tool is installed."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def profile_code_execution(command: str) -> str:
    """
    Spustí zadaný příkaz (např. 'pytest tests/test_specific_feature.py') pomocí profilovacího nástroje (cProfile)
    a vrátí přehlednou tabulku nejpomalejších funkcí a operací.
    """
    command_parts = shlex.split(command)
    profile_cmd = [command_parts[0], '-m', 'cProfile', '-s', 'tottime'] + command_parts[1:]
    return _run_command(profile_cmd)

def run_static_code_analyzer(path: str) -> str:
    """
    Spustí na zadaný soubor nebo adresář pokročilou statickou analýzu pomocí Pylint
    a vrátí seznam potenciálních problémů, chyb a doporučení pro vylepšení kódu.
    """
    pylint_executable = os.path.join(os.path.dirname(sys.executable), 'pylint')
    if not os.path.exists(pylint_executable): return "Error: pylint not found."
    return _run_command([pylint_executable, path])

def get_code_complexity(path: str) -> str:
    """
    Analyzuje zadaný soubor nebo adresář pomocí nástroje Radon a vrátí report
    o cyklomatické složitosti a indexu udržovatelnosti.
    """
    radon_executable = os.path.join(os.path.dirname(sys.executable), 'radon')
    if not os.path.exists(radon_executable): return "Error: radon not found."

    cc_report = _run_command([radon_executable, 'cc', '-a', path])
    mi_report = _run_command([radon_executable, 'mi', path])
    return f"--- Cyclomatic Complexity Report ---\n{cc_report}\n\n--- Maintainability Index Report ---\n{mi_report}"

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
        "profile_code_execution": profile_code_execution,
        "run_static_code_analyzer": run_static_code_analyzer,
        "get_code_complexity": get_code_complexity,
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