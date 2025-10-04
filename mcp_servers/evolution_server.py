"""
MCP Server pro nástroje, které agentovi umožní bezpečně experimentovat,
vyvíjet se a učit se z minulých zkušeností.
"""
import sys
import os
import tempfile
import shutil
import subprocess
import json
import uuid
import inspect
import asyncio
import functools

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importy pro pokročilé nástroje
from core.llm_manager import LLMManager
from core.rich_printer import RichPrinter
from tools.file_system import read_file_section

# --- Stavové proměnné serveru ---
ACTIVE_SANDBOX_PATH = None
ARCHIVE_DIR = os.path.join(project_root, "memory", "task_archive")
os.makedirs(ARCHIVE_DIR, exist_ok=True)
KNOWLEDGE_FILE = os.path.join(project_root, "memory", "self_knowledge.md")

# --- Nástroje ---

def create_code_sandbox(files_to_copy: list[str]) -> str:
    """
    Vytvoří dočasný, izolovaný adresář (sandbox) a zkopíruje do něj zadané soubory
    z kořenového adresáře projektu. To umožňuje bezpečně experimentovat se změnami.
    Vrátí cestu k vytvořenému sandboxu.
    """
    global ACTIVE_SANDBOX_PATH
    if ACTIVE_SANDBOX_PATH:
        return f"Chyba: Již existuje aktivní sandbox v '{ACTIVE_SANDBOX_PATH}'. Nejdříve ho zničte pomocí 'destroy_sandbox'."
    try:
        sandbox_path = tempfile.mkdtemp(prefix="agent_sandbox_")
        ACTIVE_SANDBOX_PATH = sandbox_path
        copied_files = [f for f in files_to_copy if os.path.exists(os.path.join(project_root, f))]
        for file_path in copied_files:
            shutil.copy(os.path.join(project_root, file_path), sandbox_path)
        return f"Sandbox byl úspěšně vytvořen v '{sandbox_path}' s {len(copied_files)} zkopírovanými soubory."
    except Exception as e:
        return f"Chyba při vytváření sandboxu: {e}"

def run_in_sandbox(command: str) -> str:
    """
    Spustí zadaný příkaz uvnitř aktivního sandboxu.
    Užitečné pro spouštění testů nebo skriptů na upravené verzi kódu.
    """
    global ACTIVE_SANDBOX_PATH
    if not ACTIVE_SANDBOX_PATH: return "Chyba: Žádný aktivní sandbox nebyl nalezen."
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = ACTIVE_SANDBOX_PATH + os.pathsep + env.get('PYTHONPATH', '')
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=ACTIVE_SANDBOX_PATH, check=False, env=env)
        return f"Příkaz '{command}' spuštěn v sandboxu.\nVýstup:\n{result.stdout}{result.stderr}"
    except Exception as e:
        return f"Chyba při spouštění příkazu v sandboxu: {e}"

def compare_sandbox_changes(original_filepath: str) -> str:
    """
    Porovná soubor v sandboxu s jeho originální verzí v projektu a vrátí 'diff' výstup.
    """
    global ACTIVE_SANDBOX_PATH
    if not ACTIVE_SANDBOX_PATH: return "Chyba: Žádný aktivní sandbox nebyl nalezen."
    try:
        original_path = os.path.join(project_root, original_filepath)
        sandbox_path = os.path.join(ACTIVE_SANDBOX_PATH, os.path.basename(original_filepath))
        if not os.path.exists(sandbox_path): return f"Chyba: Soubor '{os.path.basename(original_filepath)}' neexistuje v sandboxu."
        result = subprocess.run(['diff', '-u', original_path, sandbox_path], capture_output=True, text=True, check=False)
        return f"Rozdíly pro soubor '{original_filepath}':\n{result.stdout or '(žádné změny)'}"
    except Exception as e:
        return f"Chyba při porovnávání souborů: {e}"

def destroy_sandbox() -> str:
    """Smaže aktivní sandbox a všechny jeho soubory."""
    global ACTIVE_SANDBOX_PATH
    if not ACTIVE_SANDBOX_PATH: return "Chyba: Žádný aktivní sandbox k smazání."
    try:
        path_to_return, ACTIVE_SANDBOX_PATH = ACTIVE_SANDBOX_PATH, None
        shutil.rmtree(path_to_return)
        return f"Sandbox v '{path_to_return}' byl úspěšně zničen."
    except Exception as e:
        return f"Chyba při ničení sandboxu: {e}"

def run_playwright_test(script_content: str) -> str:
    """
    Přijme obsah Playwright skriptu, uloží ho do dočasného souboru a spustí ho.
    Vrátí výsledek testu a případně cestu k pořízeným screenshotům.
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py', dir='.') as tmp_file:
            tmp_file.write(script_content)
            script_path = tmp_file.name
        playwright_executable = os.path.join(os.path.dirname(sys.executable), 'playwright')
        command = [playwright_executable, 'test', script_path]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        os.remove(script_path)
        return f"Playwright test dokončen.\nVýstup:\n{result.stdout}{result.stderr}"
    except Exception as e:
        return f"Chyba při spouštění Playwright testu: {e}"

def propose_refactoring(filepath: str, class_or_function: str) -> str:
    """
    Vezme konkrétní kus kódu, pošle ho LLM se speciálním promptem zaměřeným na refaktoring
    a vrátí 'čistší' nebo efektivnější verzi tohoto kódu.
    """
    try:
        code_section = read_file_section(f"PROJECT_ROOT/{filepath}", class_or_function)
        if code_section.startswith("Error:"): return code_section
        llm_manager = LLMManager(project_root=project_root)
        model = llm_manager.get_llm("powerful")
        prompt = f"Jsi expert na refaktoring a čistý kód. Navrhni vylepšenou verzi následujícího kódu. Zaměř se na čitelnost, efektivitu a dodržování osvědčených postupů. Vrať POUZE kód, bez jakéhokoliv dalšího textu nebo vysvětlení.\n\nKód k refaktoringu:\n---\n{code_section}\n---"
        refactored_code, _ = model.generate_content(prompt)
        return f"Návrh na refaktoring pro '{class_or_function}':\n```python\n{refactored_code}\n```"
    except Exception as e:
        return f"Chyba při navrhování refaktoringu: {e}"

def archive_completed_task(task_id: str, summary: str, history: list) -> str:
    """
    Po úspěšném dokončení úkolu vezme celou jeho historii, kontext a finální řešení
    a uloží je do samostatné, komprimované 'vzpomínky' v archivu.
    """
    try:
        archive_file = os.path.join(ARCHIVE_DIR, f"{task_id}.json")
        data = {"task_id": task_id, "summary": summary, "history": history, "archived_at": str(uuid.uuid4())}
        with open(archive_file, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2)
        return f"Úkol {task_id} byl úspěšně archivován."
    except Exception as e:
        return f"Chyba při archivaci úkolu: {e}"

def search_task_archive(query: str) -> str:
    """Prohledá archiv dokončených úkolů a vrátí shrnutí nejrelevantnějších úkolů."""
    try:
        relevant_tasks = [f"- {data['summary']} (ID: {data['task_id']})" for f in os.listdir(ARCHIVE_DIR) if f.endswith(".json") and query.lower() in (data := json.load(open(os.path.join(ARCHIVE_DIR, f), 'r', encoding='utf-8'))).get('summary', '').lower()]
        if not relevant_tasks: return "V archivu nebyly nalezeny žádné relevantní úkoly."
        return "Nalezené relevantní úkoly v archivu:\n" + "\n".join(relevant_tasks)
    except Exception as e:
        return f"Chyba při prohledávání archivu: {e}"

def update_self_knowledge(new_knowledge: str) -> str:
    """
    Přidá novou znalost, strategii nebo poznatek do agentovy báze znalostí.
    Tento soubor se používá pro dlouhodobé učení a vylepšování strategií.
    """
    try:
        with open(KNOWLEDGE_FILE, 'a', encoding='utf-8') as f: f.write(f"\n\n---\n*Záznam přidaný {str(uuid.uuid4())}*\n{new_knowledge}")
        return "Báze znalostí byla úspěšně aktualizována."
    except Exception as e:
        return f"Chyba při aktualizaci báze znalostí: {e}"

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
        "create_code_sandbox": create_code_sandbox,
        "run_in_sandbox": run_in_sandbox,
        "compare_sandbox_changes": compare_sandbox_changes,
        "destroy_sandbox": destroy_sandbox,
        "run_playwright_test": run_playwright_test,
        "propose_refactoring": propose_refactoring,
        "archive_completed_task": archive_completed_task,
        "search_task_archive": search_task_archive,
        "update_self_knowledge": update_self_knowledge,
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