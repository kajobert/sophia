"""
MCP Server pro nástroje určené k hierarchickému plánování, správě úkolů a zpracování textu.
"""
import sys
import os
import uuid
from typing import Dict, Any
import json
import inspect
import asyncio
import functools

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.llm_manager import LLMManager
from core.rich_printer import RichPrinter

# --- Databáze úkolů v paměti ---
TASK_DATABASE: Dict[str, Dict[str, Any]] = {}
# --------------------------------

def create_task(description: str, parent_id: str = None) -> str:
    """
    Vytvoří nový úkol nebo podúkol. Umožňuje rozdělit komplexní problémy na menší,
    zvládnutelné kroky. Každý úkol dostane unikátní ID.
    """
    task_id = str(uuid.uuid4())
    TASK_DATABASE[task_id] = {
        "description": description,
        "parent_id": parent_id,
        "subtasks": [],
        "status": "new"
    }
    if parent_id and parent_id in TASK_DATABASE:
        TASK_DATABASE[parent_id]["subtasks"].append(task_id)
    return f"Úkol '{description[:30]}...' byl úspěšně vytvořen s ID: {task_id}"

def get_task_tree() -> str:
    """
    Vrátí stromovou strukturu všech aktuálních úkolů a podúkolů, včetně jejich stavu.
    Poskytuje přehled o postupu práce.
    """
    if not TASK_DATABASE: return "Žádné úkoly nebyly vytvořeny."
    def build_tree(task_id: str, level: int = 0) -> str:
        task = TASK_DATABASE[task_id]
        indent = "    " * level
        tree_str = f"{indent}- [{task['status']}] {task['description']} (ID: {task_id})\n"
        for subtask_id in task["subtasks"]:
            tree_str += build_tree(subtask_id, level + 1)
        return tree_str
    root_tasks = [task_id for task_id, task in TASK_DATABASE.items() if not task.get("parent_id")]
    full_tree = "Strom aktuálních úkolů:\n"
    for task_id in root_tasks:
        full_tree += build_tree(task_id)
    return full_tree.strip()

def update_task_status(task_id: str, status: str) -> str:
    """
    Aktualizuje stav zadaného úkolu.
    Povolené stavy jsou: 'new', 'in_progress', 'completed', 'failed'.
    """
    if task_id not in TASK_DATABASE: return f"Chyba: Úkol s ID '{task_id}' nebyl nalezen."
    allowed_statuses = ['new', 'in_progress', 'completed', 'failed']
    if status not in allowed_statuses: return f"Chyba: Neplatný stav '{status}'. Povolené stavy jsou: {', '.join(allowed_statuses)}"
    TASK_DATABASE[task_id]['status'] = status
    return f"Stav úkolu {task_id} byl aktualizován na '{status}'."

def get_task_details(task_id: str) -> str:
    """Vrátí detailní informace o konkrétním úkolu."""
    if task_id not in TASK_DATABASE: return f"Chyba: Úkol s ID '{task_id}' nebyl nalezen."
    return str(TASK_DATABASE[task_id])

def summarize_text(text_to_summarize: str) -> str:
    """
    Využije ekonomický LLM model k sumarizaci dlouhého textu.
    Užitečné pro zpracování obsahu souborů, dlouhých logů nebo historie konverzace.
    """
    try:
        RichPrinter.info("Inicializuji LLM pro sumarizaci...")
        llm_manager = LLMManager(project_root=project_root)
        summarizer_model = llm_manager.get_llm("economical")
        prompt = f"Prosím, shrň následující text do několika klíčových bodů. Zaměř se na nejdůležitější informace a buď stručný. Text ke shrnutí:\n\n---\n{text_to_summarize}\n---"
        RichPrinter.info("Sumarizuji text...")
        summary, _ = summarizer_model.generate_content(prompt)
        return f"Shrnutí textu:\n{summary}"
    except Exception as e:
        RichPrinter.error(f"Došlo k chybě při sumarizaci textu: {e}")
        return f"Chyba: Nepodařilo se sumarizovat text. Důvod: {e}"

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
        "create_task": create_task,
        "get_task_tree": get_task_tree,
        "update_task_status": update_task_status,
        "get_task_details": get_task_details,
        "summarize_text": summarize_text,
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