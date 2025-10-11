import os
import json
from typing import List, Dict, Any

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
        if not os.path.exists(self.tasks_file):
            os.makedirs(os.path.dirname(self.tasks_file), exist_ok=True)
            with open(self.tasks_file, "w") as f:
                json.dump({"main_goal": "", "tasks": []}, f, indent=2)

    def _read_tasks(self) -> Dict[str, Any]:
        """Načte úkoly ze souboru."""
        try:
            with open(self.tasks_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._initialize_tasks_file()
            return {"main_goal": "", "tasks": []}

    def _write_tasks(self, tasks_data: Dict[str, Any]):
        """Zapíše úkoly do souboru."""
        with open(self.tasks_file, "w") as f:
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

        # Seřadí úkoly podle priority (vzestupně)
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

if __name__ == '__main__':
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