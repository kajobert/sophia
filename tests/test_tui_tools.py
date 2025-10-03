import pytest
import sys
import os
from unittest.mock import MagicMock

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Importujeme nástroje a třídu, kterou budeme mockovat
from mcp_servers import tui_tools
from core.rich_printer import RichPrinter

@pytest.fixture
def mock_rich_printer(monkeypatch):
    """
    Fixtura, která pomocí monkeypatch nahradí všechny relevantní metody
    v RichPrinteru sledovatelnými MagicMock objekty.
    """
    mock_inform = MagicMock()
    mock_warning = MagicMock()
    mock_error = MagicMock()
    mock_ask = MagicMock()
    mock_code = MagicMock()
    mock_table = MagicMock()

    monkeypatch.setattr(RichPrinter, 'inform', mock_inform)
    monkeypatch.setattr(RichPrinter, 'warning', mock_warning)
    monkeypatch.setattr(RichPrinter, 'error', mock_error)
    monkeypatch.setattr(RichPrinter, 'ask', mock_ask)
    monkeypatch.setattr(RichPrinter, 'code', mock_code)
    monkeypatch.setattr(RichPrinter, 'table', mock_table)

    # Vrátíme slovník s mocky, abychom k nim měli v testech přístup
    return {
        "inform": mock_inform,
        "warning": mock_warning,
        "error": mock_error,
        "ask": mock_ask,
        "code": mock_code,
        "table": mock_table,
    }

def test_inform_user_calls_rich_printer(mock_rich_printer):
    message = "This is an info message."
    result = tui_tools.inform_user(message)
    assert "úspěšně zobrazena" in result
    mock_rich_printer["inform"].assert_called_once_with(message)

def test_warn_user_calls_rich_printer(mock_rich_printer):
    message = "This is a warning."
    result = tui_tools.warn_user(message)
    assert "úspěšně zobrazena" in result
    mock_rich_printer["warning"].assert_called_once_with(message)

def test_error_user_calls_rich_printer(mock_rich_printer):
    message = "This is an error."
    result = tui_tools.error_user(message)
    assert "úspěšně zobrazena" in result
    mock_rich_printer["error"].assert_called_once_with(message)

def test_ask_user_calls_rich_printer(mock_rich_printer):
    question = "What is your name?"
    result = tui_tools.ask_user(question)
    assert "otázka byla položena" in result.lower()
    mock_rich_printer["ask"].assert_called_once_with(question)

def test_display_code_calls_rich_printer(mock_rich_printer):
    code = "print('Hello, World!')"
    language = "python"
    result = tui_tools.display_code(code, language)
    assert "úspěšně zobrazen" in result
    mock_rich_printer["code"].assert_called_once_with(code, language)

def test_display_table_calls_rich_printer(mock_rich_printer):
    title = "My Table"
    headers = ["ID", "Name"]
    rows = [["1", "Alice"], ["2", "Bob"]]
    result = tui_tools.display_table(title, headers, rows)
    assert "úspěšně zobrazena" in result
    mock_rich_printer["table"].assert_called_once_with(title, headers, rows)