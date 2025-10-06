import sys
import os

# Přidání cesty k projektu pro importy, aby bylo možné najít core moduly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.rich_printer import RichPrinter

def inform_user(message: str) -> str:
    """
    Zobrazí uživateli informativní zprávu se zeleným označením.
    Použij pro běžná sdělení, potvrzení akcí nebo pozitivní výsledky.
    """
    RichPrinter.inform(message)
    return "Informativní zpráva byla úspěšně zobrazena uživateli."

def warn_user(message: str) -> str:
    """
    Zobrazí uživateli varování s oranžovým označením.
    Použij pro upozornění na méně závažné problémy, které nevyžadují okamžitý zásah.
    """
    RichPrinter.warn(message)
    return "Varovná zpráva byla úspěšně zobrazena uživateli."

def error_user(message: str) -> str:
    """
    Zobrazí uživateli chybovou hlášku s červeným označením.
    Použij pro informování o závažných chybách, selhání operací nebo problémech.
    """
    RichPrinter.error(message)
    return "Chybová hláška byla úspěšně zobrazena uživateli."

def ask_user(question: str) -> str:
    """
    Položí uživateli otázku a počká na jeho odpověď.
    Tento nástroj by se měl používat střídmě, pouze když je interakce nezbytná.
    Systém automaticky zpracuje odpověď, nemusíš na ni čekat.
    """
    # V reálné implementaci by toto volání vyvolalo událost v TUI,
    # která by zobrazila dialog a čekala na vstup.
    # Pro účely MCP serveru stačí jen zavolat printer.
    RichPrinter.ask(question)
    return "Otázka byla položena uživateli. Jeho odpověď bude poskytnuta v dalším kroku."

def display_code(code: str, language: str = "python") -> str:
    """
    Zobrazí uživateli formátovaný blok kódu se zvýrazněním syntaxe.
    """
    RichPrinter.code(code, language)
    return "Blok kódu byl úspěšně zobrazen."

def display_table(title: str, headers: list[str], rows: list[list[str]]) -> str:
    """
    Zobrazí uživateli přehlednou tabulku s daty.
    """
    RichPrinter.table(title, headers, rows)
    return "Tabulka byla úspěšně zobrazena."