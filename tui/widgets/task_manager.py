from textual.widgets import DataTable, Input, Static
from textual.containers import Vertical
from textual.app import ComposeResult

class TaskManager(Static):
    """A widget for submitting tasks and viewing their status."""

    def compose(self) -> ComposeResult:
        """Compose the widget's layout."""
        self.border_title = "Task Management"

        yield Input(placeholder="Zadejte nový úkol pro Sophii a stiskněte Enter...")

        with Vertical(id="task-table-container"):
            yield DataTable(id="task-table")

    def on_mount(self) -> None:
        """Initialize the DataTable when the widget is mounted."""
        table = self.query_one(DataTable)
        table.add_columns("ID Úkolu", "Stav", "Prompt")
        table.add_row("sample-id-123", "PENDING", "Toto je ukázkový úkol...")

    def update_tasks(self, tasks: list[dict]) -> None:
        """Clears and repopulates the task table with new data."""
        table = self.query_one(DataTable)
        table.clear()
        for task in tasks:
            # Přidáváme řádek s barevným stavem pro lepší přehlednost
            status = task.get('status', 'N/A')
            style = ""
            if status == 'TASK_COMPLETED':
                style = "green"
            elif status == 'TASK_FAILED':
                style = "red"
            elif status == 'IN_PROGRESS':
                style = "yellow"

            table.add_row(
                task.get('chat_id', 'N/A'),
                f"[{style}]{status}[/{style}]",
                task.get('user_input', 'N/A')
            )
