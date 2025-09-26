from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

class Colors:
    """Třída pro uchování ANSI kódů pro barvy v terminálu."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class RichPrinter:
    """
    Centralizovaná třída pro formátovaný výstup do terminálu pomocí knihovny Rich.
    """
    console = Console()

    @staticmethod
    def print_header(text: str, style: str = "bold magenta"):
        """Vytiskne hlavní nadpis."""
        RichPrinter.console.print(f"\n--- {text} ---", style=style)

    @staticmethod
    def print_subheader(text: str, style: str = "bold cyan"):
        """Vytiskne podnadpis (např. pro Akci nebo Výsledek)."""
        RichPrinter.console.print(f"{text}", style=style)

    @staticmethod
    def print_info(text: str):
        """Vytiskne informační zprávu."""
        RichPrinter.console.print(f"[dim]INFO:[/] {text}")

    @staticmethod
    def print_warning(text: str):
        """Vytiskne varovnou zprávu."""
        RichPrinter.console.print(f"[yellow]VAROVÁNÍ:[/] {text}")

    @staticmethod
    def print_error(text: str):
        """Vytiskne chybovou zprávu."""
        RichPrinter.console.print(f"[bold red]CHYBA:[/] {text}")

    @staticmethod
    def print_code(code: str, language: str = "json"):
        """Vytiskne blok kódu se zvýrazněním syntaxe."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=False, background_color="default")
        RichPrinter.console.print(syntax)

    @staticmethod
    def print_markdown(text: str):
        """Vytiskne text formátovaný jako Markdown."""
        md = Markdown(text)
        RichPrinter.console.print(md)

    @staticmethod
    def print_panel(text: str, title: str = "Výsledek", border_style: str = "green"):
        """Vytiskne text v ohraničeném panelu."""
        panel = Panel.fit(Text(text), title=title, border_style=border_style)
        RichPrinter.console.print(panel)