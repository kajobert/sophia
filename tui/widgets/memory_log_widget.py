from textual.widgets import RichLog
from rich.panel import Panel
from rich.text import Text
import json

class MemoryLogWidget(RichLog):
    """Widget pro zobrazování logů z paměti."""

    def __init__(self, **kwargs):
        super().__init__(highlight=True, markup=True, **kwargs)
        self.border_title = "Záznamy Paměti"

    def add_log(self, operation: str, source: str, content: dict):
        """
        Přidá formátovaný záznam do logu.
        
        Args:
            operation (str): Typ operace (e.g., 'WRITE', 'READ', 'CLEAR').
            source (str): Zdroj paměti (e.g., 'LTM (ChromaDB)', 'STM (SQLite)').
            content (dict): Obsah logu.
        """
        if operation == "WRITE":
            color = "green"
            title = f"[bold {color}]ZÁPIS[/bold {color}] do {source}"
        elif operation == "READ":
            color = "blue"
            title = f"[bold {color}]ČTENÍ[/bold {color}] z {source}"
        elif operation == "CLEAR":
            color = "red"
            title = f"[bold {color}]MAZÁNÍ[/bold {color}] v {source}"
        else:
            color = "white"
            title = f"[bold]OPERACE[/bold] v {source}"

        text_content = Text()
        for key, value in content.items():
            text_content.append(f"[bold]{key.capitalize()}:[/bold] ", style="yellow")
            if isinstance(value, (dict, list)):
                # Pretty print JSON for better readability
                pretty_value = json.dumps(value, indent=2, ensure_ascii=False)
                text_content.append(pretty_value + "\n", style="white")
            else:
                text_content.append(str(value) + "\n", style="white")

        panel = Panel(
            text_content,
            title=title,
            border_style=color,
            expand=False
        )
        self.write(panel)
        self.scroll_end(animate=True)