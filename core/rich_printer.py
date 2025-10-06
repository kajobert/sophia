import logging
import os
from typing import Callable, Any

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
    _message_poster: Callable[[Any], None] | None = None

    @staticmethod
    def configure_logging(log_dir="logs", log_file="agent_run.log"):
        """Konfiguruje souborové logování. Je bezpečné volat vícekrát."""
        if RichPrinter._logger:
            return
        logger = logging.getLogger("JulesAgent")
        logger.setLevel(logging.INFO)
        if logger.hasHandlers():
            logger.handlers.clear()
        log_path = os.path.join(log_dir, log_file)
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        RichPrinter._logger = logger
        RichPrinter._log(logging.INFO, f"Logging configured. Log file at: {log_path}")

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

    # --- Metody pro zobrazení v TUI ---
    # Od verze s refaktoringem je za posílání ChatMessage zodpovědný Orchestrator,
    # aby se oddělila logika systémového logování od zobrazování zpráv pro uživatele.
    # RichPrinter nyní poskytuje pouze nízkoúrovňové metody _post a _log.