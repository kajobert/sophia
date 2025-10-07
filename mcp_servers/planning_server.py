"""
MCP Server pro nástroje určené k hierarchickému plánování, správě úkolů a zpracování textu.
"""
import sys
import os
import uuid
import time
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
    zvládnutelné kroky. Každý úkol dostane unikátní ID a časovou značku.
    """
    task_id = str(uuid.uuid4())
    TASK_DATABASE[task_id] = {
        "id": task_id,
        "description": description,
        "parent_id": parent_id,
        "subtasks": [],
        "status": "new",
        "created_at": time.time()  # Přidána časová značka pro správné řazení
    }
    if parent_id and parent_id in TASK_DATABASE:
        TASK_DATABASE[parent_id]["subtasks"].append(task_id)
    return f"Úkol '{description[:30]}...' byl úspěšně vytvořen s ID: {task_id}"

def get_task_tree() -> str:
    """
    Vrátí stromovou strukturu všech aktuálních úkolů a podúkolů, včetně jejich stavu,
    seřazenou podle času vytvoření. Poskytuje přehled o postupu práce.
    """
    if not TASK_DATABASE:
        return "Žádné úkoly nebyly vytvořeny."

    # Vytvoříme slovník dětí pro každého rodiče a seznam kořenových úkolů
    children_by_parent = {}
    root_tasks = []

    # Seřadíme všechny úkoly hned na začátku
    sorted_tasks = sorted(TASK_DATABASE.values(), key=lambda t: t.get('created_at', 0))

    for task in sorted_tasks:
        parent_id = task.get("parent_id")
        if parent_id:
            if parent_id not in children_by_parent:
                children_by_parent[parent_id] = []
            children_by_parent[parent_id].append(task)
        else:
            root_tasks.append(task)

    def build_tree_recursive(tasks, level=0):
        tree_str = ""
        for task in tasks:
            indent = "    " * level
            tree_str += f"- [{task['status']}] {task['description']} (ID: {task['id']})\n"
            if task['id'] in children_by_parent:
                tree_str += build_tree_recursive(children_by_parent[task['id']], level + 1)
        return tree_str

    full_tree = "Strom aktuálních úkolů:\n"
    full_tree += build_tree_recursive(root_tasks)
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
    return json.dumps(TASK_DATABASE[task_id], indent=2)

def get_next_executable_task() -> str:
    """
    Najde a vrátí první proveditelný úkol na základě času vytvoření (FIFO).
    Prohledá databázi úkolů, najde všechny úkoly ve stavu 'new', jejichž podúkoly jsou 'completed',
    seřadí je podle času vytvoření a vrátí ten nejstarší.
    Jakmile je úkol vrácen, jeho stav je aktualizován na 'in_progress'.
    """
    executable_tasks = []
    for task in TASK_DATABASE.values():
        if task['status'] == 'new':
            subtasks = task.get("subtasks", [])
            all_subtasks_completed = all(
                TASK_DATABASE.get(sub_id, {}).get('status') == 'completed'
                for sub_id in subtasks
            )
            if all_subtasks_completed:
                executable_tasks.append(task)

    if not executable_tasks:
        return "Žádné další proveditelné úkoly nebyly nalezeny."

    # Seřadit proveditelné úkoly podle 'created_at' (nejstarší první)
    executable_tasks.sort(key=lambda t: t.get('created_at', float('inf')))

    next_task = executable_tasks[0]
    task_id = next_task['id']

    TASK_DATABASE[task_id]['status'] = 'in_progress'

    task_info = {
        "id": next_task["id"],
        "description": next_task["description"],
        "parent_id": next_task.get("parent_id")
    }
    return json.dumps(task_info, indent=2)

async def summarize_text(text_to_summarize: str) -> str:
    """
    Využije ekonomický LLM model k sumarizaci dlouhého textu.
    """
    try:
        RichPrinter.info("Inicializuji LLM pro sumarizaci...")
        llm_manager = LLMManager(project_root=project_root)
        summarizer_model = llm_manager.get_llm("economical")
        prompt = f"Prosím, shrň následující text do několika klíčových bodů. Zaměř se na nejdůležitější informace a buď stručný. Text ke shrnutí:\n\n---\n{text_to_summarize}\n---"
        RichPrinter.info("Sumarizuji text...")
        summary, _ = await summarizer_model.generate_content_async(prompt)
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
        "get_next_executable_task": get_next_executable_task,
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
                        tool_func = tools[tool_name]
                        if asyncio.iscoroutinefunction(tool_func):
                            result = await tool_func(*tool_args, **tool_kwargs)
                        else:
                            tool_call = functools.partial(tool_func, *tool_args, **tool_kwargs)
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