from textual.widgets import Static
from rich.panel import Panel
from rich.text import Text

class StatisticsWidget(Static):
    """Widget for displaying statistics."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.total_cost = 0.0
        self.completed_tasks = 0

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        self.update_display()

    def update_display(self):
        """Update the displayed statistics."""
        text = Text(f"Celkové náklady: ${self.total_cost:.6f}\n", justify="left")
        text.append(f"Dokončené úkoly: {self.completed_tasks}")
        self.update(Panel(text, title="Statistiky", border_style="green"))

    def set_statistics(self, total_cost: float, completed_tasks: int):
        """Set the statistics and update the display."""
        self.total_cost = total_cost
        self.completed_tasks = completed_tasks
        self.update_display()