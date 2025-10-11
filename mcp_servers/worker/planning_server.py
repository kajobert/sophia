import sys
import os
import json
import asyncio
import inspect
import functools
from typing import List, Dict, Any

# Dynamické přidání kořenového adresáře projektu do sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class PlanningServer:
    """
    Tento server poskytuje nástroje pro agilní plánování a sledování úkolů.
    Umožňuje agentovi dynamicky vytvářet, upravovat a spravovat dílčí úkoly v rámci hlavního cíle.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.tasks_file = os.path.join(self.project_root, ".sandbox", "tasks.json")
        self._initialize_tasks_file()

    def _initialize_tasks_file(self):
        """Zajistí, že soubor s úkoly existuje a má správnou strukturu."""
        os.makedirs(os.path.dirname(self.tasks_file), exist_ok=True)
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump({"main_goal": "", "tasks": []}, f, indent=2)

    def reset_plan(self) -> str:
        """
        Resets the entire plan by clearing the main goal and all sub-tasks.
        """
        self._initialize_tasks_file()
        return "The project plan has been reset."

    def _read_tasks(self) -> Dict[str, Any]:
        """Načte úkoly ze souboru."""
        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._initialize_tasks_file()
            return {"main_goal": "", "tasks": []}

    def _write_tasks(self, tasks_data: Dict[str, Any]):
        """Zapíše úkoly do souboru."""
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, indent=2, ensure_ascii=False)

    def get_main_goal(self) -> str:
        """
        Vrátí hlavní cíl mise.
        """
        tasks_data = self._read_tasks()
        goal = tasks_data.get("main_goal")
        return goal if goal else "Není definován žádný hlavní cíl."

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Vrátí seznam všech dílčích úkolů.
        """
        tasks_data = self._read_tasks()
        return tasks_data.get("tasks", [])

    def update_task_description(self, new_description: str) -> str:
        """
        Aktualizuje popis hlavního cíle mise.
        """
        tasks_data = self._read_tasks()
        tasks_data["main_goal"] = new_description
        self._write_tasks(tasks_data)
        return f"Hlavní cíl byl aktualizován na: '{new_description}'"

    def add_subtask(self, description: str, priority: int = 10) -> str:
        """
        Přidá nový dílčí úkol do plánu.

        Args:
            description: Popis úkolu.
            priority: Priorita úkolu (nižší číslo = vyšší priorita).
        """
        tasks_data = self._read_tasks()
        new_task = {
            "id": len(tasks_data.get("tasks", [])),
            "description": description,
            "priority": priority,
            "completed": False,
        }
        tasks_data.get("tasks", []).append(new_task)
        self._write_tasks(tasks_data)
        return f"Nový dílčí úkol přidán: '{description}' (ID: {new_task['id']})"

    def mark_task_as_completed(self, task_id: int) -> str:
        """
        Označí dílčí úkol jako dokončený.

        Args:
            task_id: ID úkolu, který má být označen.
        """
        tasks_data = self._read_tasks()
        tasks = tasks_data.get("tasks", [])
        task_found = False
        for task in tasks:
            if task["id"] == task_id:
                task["completed"] = True
                task_found = True
                break

        if not task_found:
            return f"Chyba: Úkol s ID {task_id} nebyl nalezen."

        self._write_tasks(tasks_data)
        return f"Úkol {task_id} byl označen jako dokončený."

    def get_next_executable_task(self) -> Dict[str, Any] | None:
        """
        Vrátí další nedokončený úkol s nejvyšší prioritou.
        """
        tasks_data = self._read_tasks()
        tasks = tasks_data.get("tasks", [])
        incomplete_tasks = [task for task in tasks if not task["completed"]]

        if not incomplete_tasks:
            return None

        incomplete_tasks.sort(key=lambda x: x["priority"])
        return incomplete_tasks[0]

    def reprioritize_task(self, task_id: int, new_priority: int) -> str:
        """
        Změní prioritu existujícího dílčího úkolu.

        Args:
            task_id: ID úkolu.
            new_priority: Nová priorita (nižší číslo = vyšší priorita).
        """
        tasks_data = self._read_tasks()
        tasks = tasks_data.get("tasks", [])
        task_found = False
        for task in tasks:
            if task["id"] == task_id:
                task["priority"] = new_priority
                task_found = True
                break

        if not task_found:
            return f"Chyba: Úkol s ID {task_id} nebyl nalezen."

        self._write_tasks(tasks_data)
        return f"Priorita úkolu {task_id} byla změněna na {new_priority}."

def create_response(request_id, result):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result})

def create_error_response(request_id, code, message):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})

async def main():
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    server_instance = PlanningServer(project_root=".")
    tools = {name: func for name, func in inspect.getmembers(server_instance, predicate=inspect.ismethod) if not name.startswith('_')}

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
                tool_definitions = [{"name": name, "description": inspect.getdoc(func) or "No description."} for name, func in tools.items()]
                response = create_response(request_id, {"capabilities": {"tools": tool_definitions}})

            elif method == "mcp/tool/execute":
                params = request.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("args", [])
                tool_kwargs = params.get("kwargs", {})

                if tool_name in tools:
                    tool_func = tools[tool_name]
                    try:
                        sig = inspect.signature(tool_func)
                        bound_args = sig.bind(*tool_args, **tool_kwargs)
                        bound_args.apply_defaults()

                        result = await loop.run_in_executor(None, functools.partial(tool_func, *bound_args.args, **bound_args.kwargs))
                        response = create_response(request_id, {"result": result})
                    except Exception as e:
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
    if os.getenv("RUN_MANUAL_TESTS"):
        # Příklad použití pro manuální testování
        server = PlanningServer(project_root=".")
        print(server.update_task_description("Implementovat kompletní autentizační systém."))
        print(server.add_subtask("Vytvořit model uživatele v databázi.", priority=1))
        print(server.add_subtask("Implementovat registraci a přihlašování.", priority=2))
        print(server.add_subtask("Přidat middleware pro ověření tokenu.", priority=3))
        print("Všechny úkoly:", server.get_all_tasks())
        next_task = server.get_next_executable_task()
        print("Další úkol k provedení:", next_task)
        if next_task:
            print(server.mark_task_as_completed(next_task['id']))
        print("Další úkol k provedení:", server.get_next_executable_task())
        print(server.reprioritize_task(2, 0))
        print("Další úkol k provedení:", server.get_next_executable_task())
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            pass