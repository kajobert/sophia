from textual.widgets import RichLog
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax

class ChatWidget(RichLog):
    """Widget pro zobrazení historie chatu."""

    def __init__(self, **kwargs) -> None:
        super().__init__(highlight=True, markup=True, **kwargs)
        self.border_title = "Konverzace"

    def add_user_message(self, message: str):
        """Přidá zprávu od uživatele do chatu."""
        self.write(Panel(f"[bold green]Uživatel:[/bold green]\n{message}", border_style="green"))

    def add_agent_message(self, content: str, msg_type: str = "text"):
        """
        Přidá zprávu od agenta (Jules) do chatu.
        Formátuje zprávu podle jejího typu.
        """
        panel_content = ""
        if msg_type == "markdown":
            panel_content = Markdown(content)
            title = "[bold blue]Jules (Myšlenkový pochod):[/bold blue]"
        elif msg_type == "tool_code":
            panel_content = Syntax(content, "json", theme="monokai", line_numbers=True)
            title = "[bold yellow]Jules (Volání nástroje):[/bold yellow]"
        elif msg_type == "tool_output":
            panel_content = content
            title = "[bold cyan]Jules (Výstup nástroje):[/bold cyan]"
        else: # Obyčejný text
            panel_content = content
            title = "[bold blue]Jules:[/bold blue]"

        self.write(Panel(panel_content, title=title, border_style="blue", expand=False))