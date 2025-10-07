import logging
import os
from typing import Callable, Any
import json

# Přidání rich importů pro panely a syntaxi
try:
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.markdown import Markdown
except ImportError:
    # Falešné třídy, pokud rich není nainstalován (např. v CI/CD bez TUI)
    Panel = Syntax = Markdown = lambda x, *args, **kwargs: str(x)


# Tento blok try/except umožňuje, aby kód fungoval, i když není nainstalován
# Textual nebo když se spouští v jiném kontextu než TUI.
try:
    from tui.messages import LogMessage, ChatMessage
except (ImportError, ModuleNotFoundError):
    # Vytvoříme falešné třídy, pokud import selže.
    # To zajišťuje, že zbytek kódu nespadne na `NameError`.
    class LogMessage:
        def __init__(self, text: str, level: str = "INFO"): pass
    class ChatMessage:
        def __init__(self, content: Any, owner: str, msg_type: str): pass


class RichPrinter:
    """
    Centralizovaná třída pro formátovaný výstup a logování.
    V TUI režimu posílá zprávy do aplikace. V opačném případě je ticho.
    Logování do souboru funguje vždy.
    """
    _logger: logging.Logger | None = None
    _communication_logger: logging.Logger | None = None
    _error_logger: logging.Logger | None = None
    _message_poster: Callable[[Any], None] | None = None

    @staticmethod
    def _setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
        """Pomocná funkce pro nastavení jednoho loggeru."""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        if logger.hasHandlers():
            logger.handlers.clear()

        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    @staticmethod
    def configure_logging(log_dir="logs"):
        """Konfiguruje všechny souborové loggery. Je bezpečné volat vícekrát."""
        if RichPrinter._logger:
            return

        # Hlavní systémový log
        system_log_path = os.path.join(log_dir, "agent_run.log")
        RichPrinter._logger = RichPrinter._setup_logger("JulesAgent", system_log_path)

        # Log pro komunikaci
        comm_log_path = os.path.join(log_dir, "communication.log")
        RichPrinter._communication_logger = RichPrinter._setup_logger("CommunicationLog", comm_log_path)

        # Log pro chyby
        error_log_path = os.path.join(log_dir, "errors.log")
        RichPrinter._error_logger = RichPrinter._setup_logger("ErrorLog", error_log_path)

        RichPrinter.info(f"Logging configured. System log: {system_log_path}, Communication log: {comm_log_path}, Error log: {error_log_path}")

    @staticmethod
    def set_message_poster(poster: Callable[[Any], None]):
        """
        Nastaví funkci, která se má použít pro posílání zpráv.
        V kontextu Textual to bude `app.post_message`.
        """
        RichPrinter._message_poster = poster

    @staticmethod
    def _log(level: int, message: str, *args, **kwargs):
        if RichPrinter._logger:
            log_message = str(message)
            RichPrinter._logger.log(level, log_message, *args, **kwargs)

    @staticmethod
    def _post(message: Any):
        """Interní metoda pro poslání zprávy, pokud je poster nastaven."""
        if RichPrinter._message_poster:
            RichPrinter._message_poster(message)

    # --- Metody pro systémové logy (pro StatusWidget) ---

    @staticmethod
    def info(message: str):
        RichPrinter._log(logging.INFO, message)
        RichPrinter._post(LogMessage(message, "INFO"))

    @staticmethod
    def warning(message: str):
        RichPrinter._log(logging.WARNING, message)
        RichPrinter._post(LogMessage(message, "WARNING"))

    @staticmethod
    def error(message: str):
        RichPrinter._log(logging.ERROR, message)
        RichPrinter._post(LogMessage(message, "ERROR"))

    # --- Nové metody pro specializované logování ---

    @staticmethod
    def log_communication(title: str, content: str | dict, style: str = "blue"):
        """Zaznamená událost do komunikačního logu a pošle panel do TUI."""
        text_content = ""
        panel_content = ""

        if isinstance(content, dict):
            text_content = json.dumps(content, indent=2, ensure_ascii=False)
            panel_content = Syntax(text_content, "json", theme="monokai", line_numbers=True)
        else:
            text_content = str(content)
            # Použijeme Markdown pro lepší formátování, pokud je přítomen
            panel_content = Markdown(text_content) if "```" in text_content or "**" in text_content else text_content

        if RichPrinter._communication_logger:
            RichPrinter._communication_logger.info(f"--- {title} ---\n{text_content}\n")

        panel = Panel(panel_content, title=title, border_style=style, expand=False)
        RichPrinter._post(ChatMessage(panel, owner='system', msg_type='communication_log'))

    @staticmethod
    def log_error_panel(title: str, content: str, exception: Exception | None = None):
        """Zaznamená chybu do error logu a pošle červený panel do TUI."""
        full_content_md = content
        full_content_log = content
        if exception:
            # Formát pro Markdown v TUI
            full_content_md += f"\n\n**Výjimka:**\n`{type(exception).__name__}: {exception}`"
            # Formát pro čistý text v log souboru
            full_content_log += f"\n\nVýjimka:\n{type(exception).__name__}: {exception}"

        if RichPrinter._error_logger:
            RichPrinter._error_logger.error(f"--- {title} ---\n{full_content_log}\n")

        panel = Panel(Markdown(full_content_md), title=f"Chyba: {title}", border_style="bold red")
        RichPrinter._post(ChatMessage(panel, owner='system', msg_type='error_log'))

    @staticmethod
    def memory_log(operation: str, source: str, content: dict):
        """
        Vytvoří a odešle zprávu o paměťové operaci do TUI.
        """
        log_data = {
            "operation": operation,
            "source": source,
            "content": content,
        }
        RichPrinter._post(ChatMessage(log_data, owner='system', msg_type='memory_log'))


    # --- Metody pro zobrazení v TUI ---
    # Od verze s refaktoringem je za posílání ChatMessage zodpovědný Orchestrator,
    # aby se oddělila logika systémového logování od zobrazování zpráv pro uživatele.
    # RichPrinter nyní poskytuje pouze nízkoúrovňové metody _post a _log.