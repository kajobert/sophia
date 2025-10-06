import pytest
import sys
import os
import json

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Importujeme pouze testované nástroje
from mcp_servers import tui_tools_server as tui_tools

# Mockování RichPrinteru již není potřeba, protože nástroje ho přímo nevolají.

def test_inform_user_returns_correct_json():
    message = "This is an info message."
    result = tui_tools.inform_user(message)
    data = json.loads(result)
    assert data == {"display": "inform", "content": message}

def test_warn_user_returns_correct_json():
    message = "This is a warning."
    result = tui_tools.warn_user(message)
    data = json.loads(result)
    assert data == {"display": "warn", "content": message}

def test_error_user_returns_correct_json():
    message = "This is an error."
    result = tui_tools.error_user(message)
    data = json.loads(result)
    assert data == {"display": "error", "content": message}

def test_ask_user_returns_correct_json():
    question = "What is your name?"
    result = tui_tools.ask_user(question)
    data = json.loads(result)
    assert data == {"display": "ask", "content": question}

def test_display_code_returns_correct_json():
    code = "print('Hello, World!')"
    language = "python"
    result = tui_tools.display_code(code, language)
    data = json.loads(result)
    expected_content = {"code": code, "language": language}
    assert data == {"display": "code", "content": expected_content}

def test_display_table_returns_correct_json():
    title = "My Table"
    headers = ["ID", "Name"]
    rows = [["1", "Alice"], ["2", "Bob"]]
    result = tui_tools.display_table(title, headers, rows)
    data = json.loads(result)
    expected_content = {"title": title, "headers": headers, "rows": rows}
    assert data == {"display": "table", "content": expected_content}