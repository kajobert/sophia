import logging
import os
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.theme import Theme

# Custom theme for better visual distinction
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "header": "bold magenta",
    "subheader": "bold blue",
    "mcp_request": "yellow",
    "mcp_response": "green",
    "prompt": "dim",
    "system": "bold green on black"
})

class RichPrinter:
    """
    Centralizovaná třída pro formátovaný výstup a logování.
    Používá rich pro výstup do konzole a standardní logging pro zápis do souboru.
    """
    console = Console(theme=custom_theme)
    _logger = None

    @staticmethod
    def configure_logging(log_dir="logs", log_file="agent_run.log"):
        """Konfiguruje souborové logování."""
        if RichPrinter._logger:
            return  # Již konfigurováno

        logger = logging.getLogger("JulesAgent")
        logger.setLevel(logging.INFO)

        # Zamezení duplicitním handlerům
        if logger.hasHandlers():
            logger.handlers.clear()

        log_path = os.path.join(log_dir, log_file)
        os.makedirs(log_dir, exist_ok=True)

        # Handler pro soubor
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        RichPrinter._logger = logger
        # Do not print here, as it might not be desired in all contexts
        # Let the caller announce that logging is configured.
        RichPrinter._log(logging.INFO, f"Logging configured. Log file at: {log_path}")


    @staticmethod
    def _log(level, message, *args, **kwargs):
        if RichPrinter._logger:
            # Ensure message is a simple string for the logger
            log_message = str(message)
            RichPrinter._logger.log(level, log_message, *args, **kwargs)

    @staticmethod
    def print_info(message: str):
        RichPrinter.console.print(f"[INFO] {message}", style="info")
        RichPrinter._log(logging.INFO, message)

    @staticmethod
    def print_warning(message: str):
        RichPrinter.console.print(f"[VAROVÁNÍ] {message}", style="warning")
        RichPrinter._log(logging.WARNING, message)

    @staticmethod
    def print_error(message: str):
        RichPrinter.console.print(f"[CHYBA] {message}", style="error")
        RichPrinter._log(logging.ERROR, message)

    @staticmethod
    def print_header(message: str, style="header"):
        RichPrinter.console.print(Panel(Text(message, justify="center"), style=style, padding=(0, 5)))
        RichPrinter._log(logging.INFO, f"--- {message} ---")

    @staticmethod
    def print_subheader(message: str, style="subheader"):
        RichPrinter.console.print(message, style=style)
        RichPrinter._log(logging.INFO, message)

    @staticmethod
    def print_code(code: str, language: str = "python", title="Kód"):
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        RichPrinter.console.print(Panel(syntax, title=title, border_style="green"))
        RichPrinter._log(logging.INFO, f"CODE BLOCK ({title}):\n{code}")

    @staticmethod
    def print_panel(content: str, title: str, border_style="default"):
        # Convert content to string if it's not, just in case
        content_str = str(content)
        RichPrinter.console.print(Panel(content_str, title=title, border_style=border_style, expand=False))
        RichPrinter._log(logging.INFO, f"PANEL ({title}):\n{content_str}")

    @staticmethod
    def print_markdown(content: str, title="Vysvětlení"):
        """Zobrazí obsah formátovaný jako Markdown v panelu."""
        md = Markdown(content)
        RichPrinter.console.print(Panel(md, title=title, border_style="dim"))
        RichPrinter._log(logging.INFO, f"MARKDOWN ({title}):\n{content}")