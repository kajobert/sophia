import pytest
import os
import sys
import json
from unittest.mock import MagicMock

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Mockování modulů PŘED jejich importem v orchestrátoru
# Tím zajistíme, že se nepokusí stáhnout modely nebo inicializovat složité třídy.
sys.modules['core.long_term_memory'] = MagicMock()
sys.modules['core.prompt_builder'] = MagicMock()
sys.modules['core.rich_printer'] = MagicMock()

from core.orchestrator import JulesOrchestrator
from core.llm_manager import LLMManager
from core.mcp_client import MCPClient

@pytest.fixture
def orchestrator_instance(monkeypatch):
    """
    Vytvoří bezpečnou a izolovanou instanci orchestrátoru pro testování
    pomocí monkeypatching, aniž by se dotkla souborového systému.
    """
    # 1. Mockování proměnných prostředí
    monkeypatch.setenv('OPENROUTER_API_KEY', 'mock_key')

    # 2. Mockování načítání konfigurace v LLMManageru, aby se nečetl config.yaml
    def mock_load_config(self):
        self.config = {
            "llm_models": {"default": "mock", "aliases": {}, "models": {"mock": {}}},
            "orchestrator": {"max_iterations": 10},
            "memory": {"short_term_limit": 3, "long_term_retrieval_limit": 3},
        }
    monkeypatch.setattr(LLMManager, "_load_config", mock_load_config)

    # 3. Mockování spouštění MCP serverů
    async def mock_start_servers(self):
        pass  # Nedělej nic
    monkeypatch.setattr(MCPClient, "start_servers", mock_start_servers)

    # 4. Vytvoření instance orchestrátoru
    # Díky mockům výše se jeho __init__ provede bezpečně.
    orc = JulesOrchestrator(project_root='.')
    return orc

def test_parse_llm_response_valid(orchestrator_instance):
    """Testuje parsování validní JSON odpovědi."""
    response_text = json.dumps({
        "explanation": "This is a test explanation.",
        "tool_call": {
            "tool_name": "test_tool",
            "args": [1, "two"],
            "kwargs": {"three": 4}
        }
    })
    explanation, tool_call = orchestrator_instance._parse_llm_response(response_text)

    assert explanation == "This is a test explanation."
    assert tool_call is not None
    assert tool_call['tool_name'] == "test_tool"
    assert tool_call['args'] == [1, "two"]
    assert tool_call['kwargs'] == {"three": 4}

def test_parse_llm_response_missing_keys(orchestrator_instance):
    """Testuje parsování validní JSON odpovědi s chybějícími klíči."""
    response_text = json.dumps({
        "explanation": "Explanation only.",
        "tool_call": {
            "tool_name": "tool_without_args"
        }
    })
    explanation, tool_call = orchestrator_instance._parse_llm_response(response_text)

    assert explanation == "Explanation only."
    assert tool_call is not None
    assert tool_call['tool_name'] == "tool_without_args"
    assert "args" not in tool_call
    assert "kwargs" not in tool_call

def test_parse_llm_response_invalid_json(orchestrator_instance):
    """Testuje, jak si parsování poradí s nevalidním JSON."""
    response_text = "this is not json"
    explanation, tool_call = orchestrator_instance._parse_llm_response(response_text)

    assert "CHYBA PARSOVÁNÍ JSON" in explanation
    assert tool_call is None