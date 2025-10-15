from textual.widgets import RichLog
from datetime import datetime

class StatusWidget(RichLog):
    """Widget pro zobrazení stavových a logovacích zpráv."""

    def __init__(self, **kwargs) -> None:
        super().__init__(highlight=True, markup=True, **kwargs)
        self.border_title = "Systémový Log"

    def add_log(self, message: str, level: str = "INFO"):
        """Přidá logovací zprávu s časovým razítkem a úrovní."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        color = "white"
        if level == "INFO":
            color = "cyan"
        elif level == "WARNING":
            color = "yellow"
        elif level == "ERROR":
            color = "bold red"

        self.write(f"[[{color}]{timestamp} | {level}[/{color}]] {message}")